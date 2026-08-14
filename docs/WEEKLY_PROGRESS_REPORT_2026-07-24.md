# Credit Card Statement Analyzer 本周项目进展

**汇报日期：2026-07-24**
**项目设计：Eric Liu**

## 1. 本周目标

本周的重点是把项目从“上传 PDF 后临时生成图表的演示程序”，推进为一个可以在本机长期使用、能够解释识别过程、保存历史记录，并具备基本访问控制的个人财务分析工具。

我们主要解决了六类问题：账单解析、商户分类、信用卡识别、历史数据库、本地登录，以及 Windows/macOS 的本地运行和封装。

## 2. 当前完整处理流程

用户上传一个或多个信用卡 PDF 后，程序按以下顺序工作：

1. 使用 `pdfplumber` 在本机提取 PDF 文本，原始 PDF 不上传到云端。
2. 根据文本中的银行特征选择 Bank of America、Chase 或通用解析器。
3. 解析交易日期、商户描述、金额，并识别信用卡产品名称及尾号。
4. 先使用用户自定义规则，再使用内置关键词规则进行商户分类。
5. 对规则无法识别的商户，可调用本机 Ollama 大模型进行补充分类。
6. 用户在界面中审核分类结果和分类原因。
7. 用户确认后，程序把账单和交易保存到本地 SQLite 数据库。
8. History 页面从数据库读取历史数据，并按月份、信用卡和类别生成总结。

## 3. 账单和信用卡识别

银行识别逻辑在 `parsers/selector.py`。程序检查账单前部是否包含 `BANK OF AMERICA`、`BANKAMERICARD` 或 `CHASE` 等特征，再选择对应解析器，无法确认时使用通用解析器。

本周重点修复了 Bank of America 账单被错误解析的问题，并改进了 Chase 与 Bank of America 的卡片识别。信用卡产品通过账单中的产品关键词识别，例如 `FREEDOM UNLIMITED`、`SAPPHIRE PREFERRED`、`CUSTOMIZED CASH REWARDS`。账户号码只提取最后四位，程序不保存完整卡号或 CVV。

相关实现位于：

- `parsers/bank_of_america_parser.py`
- `parsers/generic_parser.py`
- `parsers/card_metadata.py`
- `services/transaction_service.py`

## 4. 商户分类逻辑

分类不是联网查询商户，也不是无依据猜测。目前采用可解释的混合分类流程：

1. **用户规则优先**：读取 `data/custom_merchant_rules.json`。
2. **内置规则其次**：读取 `data/merchant_rules.json`。
3. **本地 LLM 补充**：仅处理仍为 `Uncategorized` 的商户。
4. **人工审核兜底**：证据不足或置信度低时继续保留 `Uncategorized`。

规则分类会先统一商户名称的大小写和空格，再进行关键词包含匹配。每笔交易同时记录分类来源，例如 `Built-in rule: STARBUCKS`、`Custom rule`，或者本地模型名称、提示词版本、置信度和原因。

确定性规则执行逻辑在 `categorization/categorizer.py`，规则读写在 `categorization/rules.py`。因此 mentor 可以直接审查分类顺序和具体关键词，而不需要把识别过程视为黑盒。

## 5. 本地大模型分类

我们采用 Ollama 和 `llama3.2:3b`，Windows 与 macOS 使用同一套 API 和提示词。模型通过 `http://localhost:11434` 在本机运行，商户描述不会因为分类被发送到云端。

模型只能从固定类别中选择，并返回结构化 JSON，包括 `category`、`confidence` 和 `reason`。温度设置为 0，以减少同一商户多次分类的不一致。高置信度结果可以自动应用，低置信度结果只作为建议。

模型提示词、类别定义、JSON Schema 和版本号位于 `services/local_llm_service.py`。结果缓存在 `data/llm_category_cache.json`，缓存键包含模型、提示词版本和规范化商户名称。

我们明确把“减少 Uncategorized”和“提高准确率”区分开。错误分类可能比保留未知更危险，因此未知商户不会被强制猜测。

## 6. SQLite 历史数据库

项目此前没有数据库，交易只存在于当前 Streamlit 会话，关闭程序后历史就会消失。本周加入 SQLite schema v2，数据库存放在用户系统数据目录，而不是项目安装目录：

- Windows：`%LOCALAPPDATA%\CreditCardStatementAnalyzer\analyzer.db`
- macOS：`~/Library/Application Support/CreditCardStatementAnalyzer/analyzer.db`

`statements` 表保存文件指纹、文件名、银行、信用卡标签、账单月份和导入时间。`transactions` 表保存日期、商户、金额、分类、分类原因、信用卡和原始描述。金额以整数“分”保存，避免浮点数造成金额精度问题。

程序对 PDF 完整内容计算 SHA-256 指纹，并把它作为账单唯一键。即使文件被改名，只要内容相同，就会被识别为已导入账单，程序会读取历史记录而不是重复插入。

数据库实现位于 `services/database_service.py`，完整设计记录在 `docs/DATABASE.md`。原始 PDF、完整卡号、CVV 和银行登录凭据都不会写入数据库。

## 7. 登录界面

首次打开程序时，用户需要创建本地账户，之后必须登录才能访问账单和 History 页面。界面加入了新的应用图标、登录状态、退出按钮和 `Designed by Eric Liu`。

密码不以明文保存。数据库保存随机 16-byte salt 和 PBKDF2-HMAC-SHA256 结果，使用 600,000 次迭代。登录状态保存在当前 Streamlit session 中。

目前它是本机单用户访问门锁，不是生产级多人认证。交易还没有按 `user_id` 隔离，也没有密码重置、邮件验证、登录限速、恢复代码或服务端 session 管理。这些限制已经明确写入数据库文档。

## 8. 历史分析和界面改进

应用现在分为 `Analyze` 和 `History` 两个工作区。Analyze 用于上传、分类、审核和保存；History 用于查看长期记录。

历史数据支持按月份和信用卡过滤，并显示总支出、交易数量、平均金额、分类完成率、月度变化、每日消费、分类占比、最高支出和按卡片汇总。饼图直接显示分类名称与比例，下方保留带图标的分类金额单元。

多份账单可以在一次分析中合并，月份筛选可以比较不同账单周期。信用卡图表显示解析出的银行产品和尾号，不再使用 PDF 文件名代替信用卡名称。

## 9. 跨平台与安全

Windows 提供本地批处理启动器；macOS 提供可复制到 Mac 的 ZIP 安装包、安装脚本和启动脚本。macOS 安装器会准备独立 Python 环境，并在需要时引导安装 Ollama 和下载模型。

两个系统的启动入口都限制 Streamlit 只监听 `127.0.0.1`，避免财务页面暴露到同一局域网。这个地址只能从运行程序的电脑访问；它不是可分享给其他设备的公开网址，而且本地服务停止后链接就会失效。

## 10. 测试和验证

目前共有 **33 项自动化测试通过**，覆盖：

- Bank of America 和通用账单解析
- 信用卡产品和尾号识别
- 内置规则、自定义规则和优先级
- 本地 LLM 结构化输出、缓存和异常处理
- SQLite 保存、金额精度、查询、删除和重复检测
- schema v1 到 v2 升级且不丢失历史
- 密码验证以及数据库中不出现明文密码
- 首次账户创建、退出和重新登录

Streamlit 的 Analyze、History 和登录页面也进行了应用级运行测试。

## 11. 当前限制

- 仅针对当前已实现的银行版式可靠，新的银行或改版账单仍需要新增解析器和回归样本。
- 本地 LLM 不能保证所有陌生商户都正确，仍需要置信度和人工审核。
- SQLite 适合本机单用户，不适合多台设备同时写入或互联网多人服务。
- 当前登录不能隔离多个用户的数据，不应直接作为公开网站认证。
- 本地链接依赖 Streamlit 进程持续运行，不能直接分享给 mentor 或其他设备。
- macOS ZIP 尚不是经过 Apple Developer 签名和公证的 DMG。

## 12. 下一阶段建议

下一阶段建议先给 `statements`、`transactions`、`cards` 和 `merchant_rules` 增加 `user_id`，建立真正的数据所有权边界；随后把 SQLite 模型迁移到 PostgreSQL，并接入成熟的认证方案。

发布版本还需要 HTTPS、服务端 session、登录限速、密码恢复、数据库迁移工具、加密备份、隐私政策和数据删除机制。解析方面应继续收集脱敏后的多银行测试样本，建立准确率、规则覆盖率、低置信度比例和人工纠错率等评价指标。

## 13. 可以与 mentor 重点讨论的问题

1. 第一版发布目标是本地桌面工具，还是多人在线服务？
2. 是否需要保存原始 PDF，还是只保存结构化交易？
3. 分类错误和 `Uncategorized` 之间应如何权衡？
4. 哪些银行和信用卡版式必须进入第一版支持范围？
5. 登录采用学校/公司 SSO、第三方 OAuth，还是自建账户？
6. 是否需要跨设备同步、数据导入导出和用户主动删除全部数据？
7. 项目评价应更关注解析准确率、分类准确率，还是完整产品流程？

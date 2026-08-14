# 商户分类机制

## 目标

系统把信用卡账单中的商户描述映射为消费类别。分类完全在本机完成，不会把账单或商户信息发送到外部服务。

## 规则从哪里来

当前版本在运行时不联网，也没有读取银行的 Merchant Category Code (MCC)。分类不是来自银行确认，而是关键词匹配：

- 内置规则由项目开发过程中人工编写。来源可能是常见品牌知识，也可能是根据商户名称和账单上下文做出的推断。
- 用户规则由用户在界面中明确保存，视为用户确认的分类偏好。
- `Uncategorized` 表示没有规则匹配，不代表交易解析失败。

因此，“成功匹配规则”和“商户类别得到外部事实验证”是两回事。程序只承诺忠实执行已有规则，不声称所有内置规则都经过联网核实。人工新增规则的判断依据记录在 [RULE_DECISIONS.md](RULE_DECISIONS.md)。

## 处理流程

每条交易按以下顺序处理：

1. 将商户描述转为大写，并合并多余空格。
2. 检查用户自定义规则 `data/custom_merchant_rules.json`。
3. 检查项目内置规则 `data/merchant_rules.json`。
4. 如果没有任何关键词匹配，返回 `Uncategorized`。

交易表中的 `Rule source` 列会显示实际命中的关键词，例如 `Built-in rule: WINGSTOP` 或 `Custom rule: AMAZON MKTPL`。这使每一条自动分类都可以追溯。

用户规则优先于内置规则。例如，内置规则把 `AMAZON` 归为 `Shopping`，用户可以保存 `AMAZON MKTPL -> Other`，以后包含 `AMAZON MKTPL` 的交易将优先归为 `Other`。

## 为什么会出现 Uncategorized

信用卡账单通常只提供原始商户描述，例如：

```text
TST* PARIS BAGUETTE - ELM ELMHURST NY
```

其中可能包含支付平台前缀、门店号、电话号码和城市。程序不会根据金额或名称盲目猜测类别；当规则库没有可确认的关键词时，会保留 `Uncategorized`，让用户审核。

## 遇到新商户时怎么办

### 在界面中保存规则

1. 打开左侧 `Custom Categories`。
2. 在 `Merchant contains` 输入稳定、具有辨识度的部分，例如 `PARIS BAGUETTE`。
3. 选择类别并点击 `Save rule`。
4. 页面重新分析后，当前和未来账单中的匹配交易都会使用该类别。

不要把日期、金额、门店流水号或完整电话号码放进关键词。关键词太长可能无法匹配另一家门店，太短则可能误伤无关商户。

交易表中的类别也可以直接修改，但该修改只影响当前页面和导出的 CSV。只有侧边栏保存的规则会写入本地文件并在未来继续使用。

### 修改项目内置规则

经过确认且适合大多数用户的商户，可以加入 `data/merchant_rules.json`。文件结构是类别到关键词列表的映射：

```json
{
  "Dining": ["PARIS BAGUETTE", "WINGSTOP"],
  "Transportation": ["OMNY"]
}
```

修改后应在 `tests/test_categorizer.py` 添加测试，防止规则顺序造成误分类。

## 关键代码

- `categorization/categorizer.py`：规范化商户名称并执行优先级匹配。
- `categorization/rules.py`：读取内置规则，保存、列出和删除用户规则。
- `data/merchant_rules.json`：项目维护的通用规则。
- `data/custom_merchant_rules.json`：用户在界面中保存的本地规则。
- `tests/test_categorizer.py`：分类行为和优先级测试。

## 当前方案的局限

关键词规则透明、快速、可离线运行，但它不理解商户语义，也无法自动判断同名商户。更高级的后续版本可以加入商户名称清洗、MCC 数据、用户纠错学习或本地机器学习模型；无论采用哪种方式，低置信度结果仍应交给用户确认。

## 验证

在项目目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

测试应全部通过，然后再用真实账单确认交易数量、消费总额和未分类数量。

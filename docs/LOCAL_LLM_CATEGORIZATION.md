# 本地 LLM 分类设计

## 结论

本地 LLM 适合作为未知商户的后备分类器，不适合替代 PDF 解析、用户规则或已确认规则。推荐采用混合流程：

当前实现使用 Ollama 的本地 HTTP API 和 `llama3.2:3b`。商户描述是英文，因此选择约 2GB 的纯文本模型，不依赖中文或视觉能力。相同 API、模型标签、提示词和 JSON Schema 可在 Windows 与 macOS 使用。

官方依据：

- Ollama Windows 文档：https://docs.ollama.com/windows
- Ollama macOS 文档：https://docs.ollama.com/macos
- Structured Outputs：https://docs.ollama.com/capabilities/structured-outputs
- llama3.2 模型页：https://ollama.com/library/llama3.2

1. 用户自定义规则：最高优先级，代表用户确认的偏好。
2. 内置关键词规则：处理稳定、已维护的常见商户。
3. 本地 LLM：只处理前两层无法识别的商户。
4. 人工确认：LLM 低置信度或类别不明确时保留 `Uncategorized`。

## 为什么不让 LLM 解析整个账单

PDF 交易解析需要金额、日期和列位置准确。LLM 可能遗漏交易、改变金额或产生不存在的记录。银行专用解析器应该先生成确定性的交易数据，然后只把商户描述交给本地 LLM 分类。

## 建议输入

只传递分类所需的最少信息：

```json
{
  "merchant": "TST*TOFU STORY QUEENS 347-506-0797 NY",
  "allowed_categories": ["Dining", "Groceries", "Transportation", "Shopping", "Travel", "Utilities", "Entertainment", "Health", "Fees", "Other"]
}
```

不要把姓名、地址、账号、完整账单文本或其他交易发送给模型。

## 建议输出

模型必须返回结构化 JSON：

```json
{
  "category": "Dining",
  "confidence": 0.82,
  "reason": "Merchant name suggests a restaurant"
}
```

只有类别在允许列表中且置信度达到项目设定阈值时才自动采用。输出应在界面中标记为 `Local LLM`，不能伪装成银行 MCC 或已验证规则。

模型置信度是模型自报值，并非统计校准后的真实正确率。界面默认只显示建议，不自动改写类别；用户主动开启 `Auto-apply high-confidence results` 后，阈值才参与自动采用。

## 隐私与运行方式

- 模型必须在本机运行，默认不允许网络调用。
- 应支持关闭 LLM，让规则系统仍可独立工作。
- 模型名称、版本、提示词版本和置信度应记录到导出结果中。
- 首次下载模型需要用户明确同意，因为模型文件通常较大。
- 缓存键包含模型名和提示词版本，提示词升级后不会沿用旧判断。

## 评估方法

在启用自动分类前，先建立一组由用户确认的商户测试集，分别统计规则覆盖率、LLM 准确率、低置信度比例和人工纠错率。不能只用“Uncategorized 变少”作为成功标准，因为错误分类比保留未知更危险。

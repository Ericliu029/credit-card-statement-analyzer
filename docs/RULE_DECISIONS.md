# 分类规则判断记录

## 重要说明

下表记录项目开发过程中人工加入的部分商户规则。除非“验证方式”明确写为联网验证或 MCC，否则这些分类没有经过实时互联网查询，也不是银行提供的官方商户类别。

| 关键词 | 类别 | 判断依据 | 验证方式 |
| --- | --- | --- | --- |
| QATAR AIR | Travel | 明确的航空公司名称 | 常识识别，未实时联网 |
| OMNY | Transportation | 纽约公共交通支付名称 | 常识识别，未实时联网 |
| RENDR / PHYSICIAN | Health | 商户描述包含医疗机构与 physician | 名称推断，未实时联网 |
| CASTLE CHICKEN | Dining | 商户名称呈现餐饮特征 | 名称推断，未实时联网 |
| KYO RAMEN | Dining | 商户名称呈现餐饮特征 | 名称推断，未实时联网 |
| SHAXIAN XIAOCHI | Dining | 商户名称呈现餐饮特征 | 名称推断，未实时联网 |
| PARIS BAGUETTE | Dining | 已知烘焙餐饮品牌 | 常识识别，未实时联网 |
| WINGSTOP | Dining | 已知餐饮品牌 | 常识识别，未实时联网 |
| CHICK ROCKS | Dining | 商户名称呈现餐饮特征 | 名称推断，未实时联网 |
| TOFU STORY | Dining | 商户名称和账单上下文呈现餐饮特征 | 名称推断，未实时联网 |

## 以后如何记录

新增内置规则时，应写明关键词、目标类别、判断依据和验证方式。若用户通过界面保存自定义规则，则该规则代表用户偏好，不需要加入本表。

如果未来接入 MCC 或商户查询服务，应将来源、查询日期和隐私影响写入本表，并在界面中区分 `Bank MCC`、`Verified merchant service` 和 `Manual rule`。

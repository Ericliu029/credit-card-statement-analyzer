# Categorization Rule Decision Record

## Important Note

The table below records selected merchant rules that were added manually during project development. Unless the verification method explicitly states an online source or MCC data, these categories were not verified through a real-time internet lookup and are not official bank-provided merchant categories.

| Keyword | Category | Rationale | Verification Method |
| --- | --- | --- | --- |
| QATAR AIR | Travel | Identifiable airline name | General knowledge; no real-time lookup |
| OMNY | Transportation | New York public transportation payment name | General knowledge; no real-time lookup |
| RENDR / PHYSICIAN | Health | Description identifies a medical provider or physician | Name-based inference; no real-time lookup |
| CASTLE CHICKEN | Dining | Merchant name indicates a food business | Name-based inference; no real-time lookup |
| KYO RAMEN | Dining | Merchant name indicates a restaurant | Name-based inference; no real-time lookup |
| SHAXIAN XIAOCHI | Dining | Merchant name indicates a restaurant | Name-based inference; no real-time lookup |
| PARIS BAGUETTE | Dining | Recognized bakery and food-service brand | General knowledge; no real-time lookup |
| WINGSTOP | Dining | Recognized restaurant brand | General knowledge; no real-time lookup |
| CHICK ROCKS | Dining | Merchant name indicates a food business | Name-based inference; no real-time lookup |
| TOFU STORY | Dining | Merchant name and statement context indicate a restaurant | Name-based inference; no real-time lookup |

## Recording Future Decisions

When adding a built-in rule, record its keyword, target category, rationale, and verification method. A custom rule saved through the interface represents a user's preference and does not need to be added to this table.

If the project later integrates MCC data or a merchant lookup service, record the source, lookup date, and privacy impact. The interface should distinguish among `Bank MCC`, `Verified merchant service`, and `Manual rule` results.

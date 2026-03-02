# Exa.ai Neural Search Queries: Trade Finance Processor (UAE)

> **Role:** Officer (Processor - Trade Finance)  
> **Experience:** 0-3 years  
> **Location:** Sharjah or Dubai  
> **Skills:** Trade Finance operations, M-Base/OCB/MBASE, FTS, WPS, DDS

---

## How Exa Differs from Google X-Ray

| Google X-Ray | Exa.ai |
|--------------|--------|
| `site:linkedin.com/in/` + Boolean operators | Natural language semantic search |
| Exact keyword matching | Conceptual understanding |
| `AND`/`OR`/`NOT` syntax | Descriptive queries, no special operators |
| Filters by URL patterns | Finds semantically similar content anywhere |

**Key Principle:** Write Exa queries like you're describing the ideal candidate to a human recruiter.

---

## Exa Search Queries

### Query 1: Core Trade Finance Processor
```
LinkedIn profile of a junior Trade Finance Officer or Operations Processor working at a bank in Dubai or Sharjah. They process Letters of Credit, Documentary Collections, and Bank Guarantees. They use M-Base, OCB, or MBASE banking systems. They have 0-3 years of experience. They might have titles like Documentation Officer, LC Processor, Remittance Officer, or Trade Services Officer.
```

**Why This Works:**
- Exa understands "junior" maps to "0-3 years"
- Lists specific job titles without requiring exact matches
- Includes system names (M-Base, OCB) as semantic anchors
- Location is explicit but not restrictive

---

### Query 2: Recent Graduate / Entry Level
```
Recent graduate on LinkedIn working in Trade Finance or Trade Operations at a UAE bank in Dubai or Sharjah. They are a trainee, fresher, or entry-level analyst who started in 2023, 2024, or 2025. They work with Letters of Credit, Guarantees, or Remittance operations. They might use M-Base or OCB systems. Banking operations role with less than 3 years experience.
```

**Why This Works:**
- "Recent graduate" + year ranges targets fresh talent
- "Fresher" is a common UAE/India term Exa will recognize
- "Less than 3 years" reinforces junior level without exclusion syntax
- Trade Operations context narrows from generic banking

---

### Query 3: UAE Bank-Specific Targeting
```
LinkedIn profile of an Operations Processor or Trade Finance Officer at ADCB, Emirates NBD, First Abu Dhabi Bank, Mashreq, RAKBANK, Dubai Islamic Bank, Sharjah Islamic Bank, Invest Bank, or United Arab Bank. They work in Trade Finance operations processing LC, Letters of Credit, or Guarantees. Junior level role, not a manager or senior officer. Based in Dubai or Sharjah.
```

**Why This Works:**
- Specific bank names act as strong semantic signals
- Exa will find profiles mentioning these employers
- "Not a manager" filters seniority without negative operators
- Location + employer + function creates tight targeting

---

### Query 4: Skills-First / System Expert
```
LinkedIn profile of a banking operations professional who uses M-Base, OCB, MBASE, Finacle, Flexcube, or Temenos systems. They work in Trade Finance, LC Processing, Import Export operations, or Documentary Credits. They hold a title like Officer, Processor, Assistant, Analyst, or Associate. They are based in Sharjah or Dubai, UAE. Early career professional with trainee or junior level experience.
```

**Why This Works:**
- Leads with system expertise — very specific signal
- Includes related banking systems for broader net
- "Early career" + specific titles filters seniority
- Import/Export keywords catch Trade Finance context

---

### Query 5: Graduate Trainee Pipeline
```
LinkedIn profile of a Graduate Trainee, Management Trainee, or Banking Trainee at a UAE bank. They recently graduated in 2023, 2024, or 2025 and work in Trade Finance, Banking Operations, Loan Operations, or Credit Operations. Based in Dubai, Sharjah, or Abu Dhabi. They may use M-Base or OCB systems. Fresher or recent graduate starting their banking career.
```

**Why This Works:**
- Trainee program keywords target structured entry-level hiring
- Recent graduation years confirm experience level
- Broader operations keywords since trainees rotate
- Abu Dhabi included as nearby talent pool

---

### Query 6: Sharjah-Specific Hunt
```
LinkedIn profile of a Trade Finance or Operations professional working at Invest Bank, United Arab Bank, or Sharjah Islamic Bank in Sharjah, UAE. They process Letters of Credit, Guarantees, or Trade Finance transactions. Junior officer, processor, or assistant level. Experience in M-Base banking systems. 0-3 years in banking operations.
```

**Why This Works:**
- Sharjah-specific banks (Invest Bank, United Arab Bank) are key targets
- Location is locked to Sharjah
- Trade Finance function is explicit
- Experience level is clear

---

### Query 7: FTS/WPS/DDS System Users
```
LinkedIn profile of a banking operations officer in Dubai or Sharjah who works with FTS, WPS, or DDS wage protection systems. They process payroll, remittance, or Trade Finance operations. They use M-Base or OCB banking software. Junior level, analyst, or processor role at a UAE bank. 1-3 years experience in banking operations.
```

**Why This Works:**
- FTS/WPS/DDS are UAE-specific systems — strong signal
- These systems often overlap with Trade Finance operations
- Experience range is explicit
- Location + system + function is tight

---

## Exa Pro Tips

### 1. Use the `type` parameter
```json
{
  "query": "LinkedIn profile of a junior Trade Finance Officer...",
  "type": "keyword"  // or "neural" for broader semantic search
}
```
- `keyword`: Stricter matching, closer to Google X-Ray
- `neural`: Broader conceptual matches, may surface unexpected candidates

### 2. Use the `include_domains` filter
```json
{
  "query": "junior Trade Finance Officer Dubai banking...",
  "include_domains": ["linkedin.com"]
}
```
- Ensures results come from LinkedIn
- Reduces noise from job boards or news articles

### 3. Use the `start_published_date` for recency
```json
{
  "query": "Recent graduate Trade Finance trainee Dubai...",
  "start_published_date": "2023-01-01"
}
```
- Targets profiles updated since 2023
- Catches recent graduates and job changers

### 4. Iterate with `exclude` concepts
If Exa returns too many senior candidates, add to your query:
```
...junior or entry-level role, NOT a manager, director, or senior executive...
```

### 5. Save successful queries
Exa allows saving queries. Once you find a string that returns quality candidates, save it for future Trade Finance roles.

---

## Quick Reference: When to Use Each Query

| Query | Best For |
|-------|----------|
| **Query 1** | General Trade Finance candidate search |
| **Query 2** | Fresh graduates and trainees |
| **Query 3** | Targeting specific UAE banks |
| **Query 4** | System-first approach (M-Base experts) |
| **Query 5** | Graduate program pipeline |
| **Query 6** | Sharjah-specific hiring |
| **Query 7** | FTS/WPS/DSS system users |

---

## Sample Exa API Request

```bash
curl -X POST https://api.exa.ai/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "query": "LinkedIn profile of a junior Trade Finance Officer or Operations Processor working at a bank in Dubai or Sharjah. They process Letters of Credit, Documentary Collections, and Bank Guarantees. They use M-Base, OCB, or MBASE banking systems. They have 0-3 years of experience.",
    "type": "neural",
    "include_domains": ["linkedin.com"],
    "num_results": 20
  }'
```

---

*Generated: 2026-02-25*  
*Role: Officer (Processor - Trade Finance) | Sharjah/Dubai | 0-3 years experience*

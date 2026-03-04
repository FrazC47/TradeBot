# Exa.ai Websets Queries: Trade Finance Processor (UAE)

> **Role:** Officer (Processor - Trade Finance)  
> **Experience:** 0-3 years  
> **Location:** Sharjah or Dubai  
> **Webset Purpose:** Build a persistent, queryable talent pool of junior Trade Finance candidates in UAE

---

## Websets Overview

**What Websets Do:**
- Save search results to a named, persistent collection
- Query within the Webset (filter, sort, enrich)
- Update over time with new searches
- Export subsets for specific campaigns

**Your Webset Strategy:**
1. Create: `uae-trade-finance-junior-pool`
2. Populate with multiple query types (breadth)
3. Query within Webset for specific needs (depth)
4. Enrich promising profiles
5. Export for outreach

---

## Phase 1: Population Queries (Build the Webset)

Run these to populate your Webset with diverse candidates:

### Query A: Core Trade Finance Population
```
LinkedIn profiles of junior Trade Finance professionals working at banks in Dubai or Sharjah, UAE. They process Letters of Credit, Documentary Collections, Bank Guarantees, or Trade Finance operations. They use banking systems like M-Base, OCB, or MBASE. They hold titles such as Trade Finance Officer, Operations Processor, Documentation Officer, LC Processor, Remittance Officer, or Trade Services Officer. These are early-career professionals with 0 to 3 years of banking experience, not managers or senior executives.
```

**Save to Webset:** `uae-trade-finance-junior-pool`  
**Expected yield:** 40-80 profiles  
**Purpose:** Core talent pool

---

### Query B: Recent Graduate Pipeline
```
LinkedIn profiles of recent graduates and trainees working in Trade Finance, Trade Operations, or Banking Operations at UAE banks in Dubai, Sharjah, or Abu Dhabi. They are Graduate Trainees, Management Trainees, Banking Trainees, or fresh graduates from the Class of 2023, 2024, or 2025. They work with Letters of Credit, Guarantees, Remittance operations, or M-Base banking systems. These are entry-level professionals starting their banking careers with less than 2 years of experience.
```

**Add to Webset:** `uae-trade-finance-junior-pool`  
**Expected yield:** 30-60 profiles  
**Purpose:** Fresh talent pipeline

---

### Query C: UAE Bank-Specific Talent
```
LinkedIn profiles of banking operations professionals working at ADCB, Emirates NBD, First Abu Dhabi Bank, Mashreq Bank, RAKBANK, Dubai Islamic Bank, Sharjah Islamic Bank, Invest Bank, or United Arab Bank. They work in Trade Finance operations, LC processing, Documentary Credits, or Guarantees. They are Officers, Processors, Assistants, Analysts, or Associates — not Senior Managers, Directors, or VPs. Based in Dubai or Sharjah, UAE.
```

**Add to Webset:** `uae-trade-finance-junior-pool`  
**Expected yield:** 50-100 profiles  
**Purpose:** Target specific employers

---

### Query D: System-Specific Experts
```
LinkedIn profiles of banking operations professionals in Dubai or Sharjah who use M-Base, OCB, MBASE, Finacle, Flexcube, or Temenos core banking systems. They work in Trade Finance operations, Import Export processing, LC Processing, Documentary Credits, or Bank Guarantees. They hold junior titles like Officer, Processor, Assistant, Analyst, Associate, or Trainee. Early career stage with 1 to 3 years of experience in UAE banking.
```

**Add to Webset:** `uae-trade-finance-junior-pool`  
**Expected yield:** 30-50 profiles  
**Purpose:** System-skilled candidates

---

### Query E: Sharjah-Focused Search
```
LinkedIn profiles of Trade Finance and Operations professionals working in Sharjah, UAE at Invest Bank, United Arab Bank, Sharjah Islamic Bank, or other Sharjah-based financial institutions. They process Letters of Credit, Guarantees, Trade Finance transactions, or Remittance operations. Junior level Officers, Processors, or Assistants with M-Base or OCB system experience. 0 to 3 years in banking operations.
```

**Add to Webset:** `uae-trade-finance-junior-pool`  
**Expected yield:** 15-30 profiles  
**Purpose:** Location-specific talent

---

### Query F: FTS WPS DDS System Users
```
LinkedIn profiles of banking operations officers in Dubai or Sharjah, UAE who work with FTS, WPS, or DDS wage protection and remittance systems. They process payroll operations, remittance transactions, or Trade Finance operations. They use M-Base, OCB, or similar banking software. Junior level Analysts, Processors, or Officers with 1 to 3 years of UAE banking experience.
```

**Add to Webset:** `uae-trade-finance-junior-pool`  
**Expected yield:** 20-40 profiles  
**Purpose:** Niche system expertise

---

## Phase 2: Webset Internal Queries (Query Your Pool)

Once populated, query within your Webset for specific needs:

### Internal Query 1: M-Base Specialists Only
```
Candidates in this pool who specifically mention M-Base, MBASE, or OCB systems on their LinkedIn profiles. Trade Finance operations experience preferred.
```

### Internal Query 2: Emirates NBD Candidates
```
Candidates currently or previously employed at Emirates NBD bank in Dubai, working in Trade Finance or Operations roles.
```

### Internal Query 3: 2024 Graduates
```
Candidates who graduated in 2024 or started their first banking role in 2024. Recent graduates and fresh talent.
```

### Internal Query 4: LC Processing Experience
```
Candidates with specific experience processing Letters of Credit, LC operations, or Documentary Credits.
```

### Internal Query 5: Sharjah-Based Only
```
Candidates based in Sharjah, UAE, excluding Dubai candidates. Local talent for Sharjah-based roles.
```

### Internal Query 6: Immediate Availability Hints
```
Candidates whose profiles mention visit visa, cancelled visa, immediately available, or open to work status in the UAE.
```

---

## Phase 3: Enrichment Queries (Deep Dive)

For promising candidates, run enrichment to find more context:

### Enrichment Query: Company Research
```
Information about ADCB Trade Finance department, operations structure, and junior officer career paths. Recent news about ADCB banking operations in Dubai.
```

### Enrichment Query: Skills Verification
```
What is M-Base banking system used for in UAE banks? What skills does an M-Base operator need? Trade Finance operations using M-Base.
```

### Enrichment Query: Salary Benchmark
```
Junior Trade Finance Officer salary in Dubai and Sharjah banks. Operations Processor compensation UAE banking sector 2024 2025.
```

---

## Webset API Structure

### Create Webset
```bash
curl -X POST https://api.exa.ai/websets \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "name": "uae-trade-finance-junior-pool",
    "description": "Junior Trade Finance candidates in Dubai and Sharjah, 0-3 years experience"
  }'
```

### Search and Add to Webset
```bash
curl -X POST https://api.exa.ai/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "query": "LinkedIn profiles of junior Trade Finance professionals working at banks in Dubai or Sharjah...",
    "type": "neural",
    "include_domains": ["linkedin.com"],
    "num_results": 50,
    "webset_id": "YOUR_WEBSET_ID"
  }'
```

### Query Within Webset
```bash
curl -X POST https://api.exa.ai/websets/YOUR_WEBSET_ID/query \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "query": "Candidates who mention M-Base or OCB systems",
    "num_results": 20
  }'
```

### Export Webset Subset
```bash
curl -X POST https://api.exa.ai/websets/YOUR_WEBSET_ID/export \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "filter": "candidates at Emirates NBD with Trade Finance experience",
    "format": "csv"
  }'
```

---

## Webset Workflow Summary

```
Step 1: CREATE webset "uae-trade-finance-junior-pool"
    │
Step 2: POPULATE with Queries A-F (200-300 total profiles)
    │
Step 3: QUERY internally for specific needs
    ├── M-Base specialists
    ├── Emirates NBD candidates
    ├── 2024 graduates
    └── Sharjah-based only
    │
Step 4: ENRICH promising candidates
    ├── Company research
    ├── Skills verification
    └── Salary benchmarks
    │
Step 5: EXPORT subsets for outreach campaigns
```

---

## Pro Tips for Websets

1. **Overlap is good** — Same candidate from multiple queries = stronger signal
2. **Date-stamp additions** — Track when candidates were added for freshness
3. **Regular refresh** — Re-run population queries monthly to catch new profiles
4. **Tag internally** — Use Exa's metadata to tag: "hot lead", "M-Base expert", "Emirati"
5. **Export before outreach** — Always export a clean CSV before starting email campaigns

---

*Generated: 2026-02-26*  
*Webset: uae-trade-finance-junior-pool*  
*Target: 200-300 profiles | Junior Trade Finance | Dubai/Sharjah*

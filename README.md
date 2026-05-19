# Taiwan Semiconductor Sustainable Finance Analyzer

A focused MVP for analyzing ESG consistency and greenwashing risk in Taiwan semiconductor companies.

## Initial Scope

Companies:
- TSMC
- ASE Technology

Claim categories:
- Emissions and net-zero targets
- Renewable energy claims
- Supply-chain ESG commitments

Outputs:
- Extracted ESG claims in JSON/CSV
- Consistency and greenwashing-risk scoring
- Streamlit dashboard
- Short sustainable-finance research memo

## Project Philosophy

This is not a generic ESG platform. The goal is to ship a credible portfolio project that demonstrates sustainable finance research, AI-assisted analysis, and Taiwan semiconductor domain focus.

## Folder Structure

```text
reports/      Raw sustainability and annual reports
src/          Core Python modules
data/         Extracted structured data
outputs/      Scores, memos, and analysis outputs
dashboard/    Streamlit dashboard
/docs/        Premortem, methodology, notes
/tests/       Basic tests
```

## 4-Week Plan

### Week 1: Manual Foundation
- Download TSMC and ASE latest sustainability reports
- Download annual reports if available
- Manually extract first 10 ESG claims
- Define scoring rubric

### Week 2: Extraction Pipeline
- Build PDF text extraction
- Convert claims into structured JSON
- Store results in CSV/JSON

### Week 3: Scoring and Finance Layer
- Add greenwashing-risk scoring
- Add simple financial/carbon-risk interpretation
- Generate first memo draft

### Week 4: Dashboard and Polish
- Build Streamlit dashboard
- Finalize GitHub repo
- Write final case-study memo
- Record demo walkthrough
```

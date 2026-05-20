# Taiwan Semiconductor ESG Claim Extraction MVP

## Executive Summary

This project is a simple MVP for extracting and reviewing ESG claims from semiconductor sustainability reports. It uses a regex-first Python pipeline to identify ESG-related claims, apply confidence filtering, assign simple risk labels, and produce a final analyst shortlist.

The current final output is based on `data/extracted/final_claims.csv`, which contains 40 shortlisted claims. The shortlist is designed to assist human sustainable finance analysis. It is not an official ESG rating, does not provide investment advice, and should not be used as a substitute for expert review.

## Methodology

The pipeline reads report PDFs, extracts text page by page, and detects claims related to emissions, renewable energy, supply chain, and governance. It compares candidates against `claims_template.csv`, applies confidence scoring, filters weaker or duplicate claims, and ranks the remaining claims into a final review file.

The approach is intentionally lightweight:

- Local PDF text extraction with `pdfplumber`
- Regex-first ESG claim detection
- Confidence filtering and near-duplicate removal
- Simple risk scoring based on specificity, target years, metrics, and validation signals
- Final analyst-style review capped at 40 claims

No vector database, RAG system, LangChain workflow, or autonomous agent is used.

## Companies Analyzed

The current final shortlist includes claims labeled as:

- ASEH
- TSMC
- `e-all_2023`

The `e-all_2023` label is derived from a source filename and should be normalized in a future iteration. The MVP currently preserves that source label rather than guessing the company identity.

## Key Findings by Company

### ASEH

ASEH claims in the final shortlist emphasize emissions reductions, renewable energy targets, and supplier-related programs. Several claims include measurable language, such as greenhouse gas reduction percentages, renewable energy targets, and 2030 or 2050 timelines. Most ASEH claims are rated Medium risk because they are specific but often still require stronger validation or clearer source context.

### TSMC

TSMC claims focus on net-zero targets, renewable energy commitments, supplier selection criteria, and governance structures. The final shortlist includes claims around baseline years, emissions reduction programs, and supplier carbon performance. Most are Medium risk, reflecting useful but still review-dependent disclosures.

### e-all_2023

The `e-all_2023` source contributes claims across emissions, renewable energy, supply chain, and governance. Several renewable energy and supply-chain claims contain strong target or validation language, including RE100 and supplier disclosure references. Because the company label is filename-derived, these rows should be treated as source-specific until company normalization is added.

## Key Findings by Category

### Emissions

Emissions is the largest category in the final shortlist. Claims often reference greenhouse gas reductions, net-zero targets, carbon footprint assessment, 2030 goals, and 2050 pathways. These are useful for human review because they connect ESG statements to measurable decarbonization commitments, but many still require verification against original report context.

### Renewable Energy

Renewable energy claims include RE100 references, renewable electricity targets, and staged renewable energy goals such as 2025, 2040, and 2050 milestones. This category contains several of the strongest claims because percentages, target years, and validation language are more common.

### Supply Chain

Supply-chain claims focus on supplier carbon disclosure, supplier selection criteria, CDP questionnaires, and low-carbon procurement programs. These claims matter because semiconductor supply-chain emissions can be material, but most need follow-up on coverage, enforcement, and supplier-level verification.

### Governance

Governance claims are fewer in the final shortlist. They generally reference ESG governance structures, disclosure standards, committees, internal controls, or implementation plans. These claims are important context, but they are often less measurable than emissions or renewable energy claims.

## Risk Interpretation

### Low Risk

Low risk means the claim includes a specific metric, a target year, and evidence or validation language. These claims are stronger candidates for analyst review, although they still require source verification.

### Medium Risk

Medium risk means the claim is specific but is missing at least one important element, such as a measurable metric, target year, or external validation. Most current final claims fall into this group.

### High Risk

High risk means the claim is vague or aspirational and lacks a measurable KPI. The final review step currently excludes most High-risk claims from the 40-claim shortlist.

## Limitations

This is an MVP, not an official ESG rating system. It relies on PDF text extraction and regex-based logic, so it can still capture broken text fragments or miss claims expressed in tables, charts, footnotes, or unusual layouts.

The pipeline does not verify claims against external data, audited filings, emissions inventories, or financial performance. It also does not judge whether a claim is true. It only helps identify and prioritize claims for human sustainable finance analysis.

The current company labeling should be improved, especially for filename-derived labels such as `e-all_2023`.

## Next Steps

- Normalize company names across report filenames and extracted rows.
- Add source document and report year fields to the final analyst output.
- Improve table extraction for metrics that appear outside normal sentences.
- Add manual review flags for broken PDF fragments.
- Compare extracted claims against external assurance, SBTi, CDP, or regulatory sources.
- Expand dashboard views for company/category/risk drilldowns.
- Add a human-reviewed gold set to evaluate precision and recall.

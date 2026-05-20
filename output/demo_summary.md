# Demo Summary

## What the Project Does

- Extracts ESG-related claims from semiconductor sustainability reports using a local Python pipeline.
- Focuses on emissions, renewable energy, supply chain, and governance claims.
- Filters broad claim candidates into a smaller analyst-ready shortlist.
- Adds confidence scores, risk labels, and analyst notes for review.
- Presents the final claims in CSV form and a simple Streamlit dashboard.

## Why It Matters for Sustainable Finance

- Helps analysts quickly identify ESG claims that deserve deeper verification.
- Supports consistency checks between company disclosures, targets, and evidence.
- Reduces manual screening time while keeping humans responsible for interpretation.

## Future Improvements

- Normalize company names, report years, and source document metadata.
- Add stronger table extraction and better handling of PDF layout artifacts.
- Validate claims against external sources such as assurance statements, SBTi, CDP, and regulatory filings.

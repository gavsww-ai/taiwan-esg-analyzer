# ESG Consistency Insights Summary

## Overall Project-Level Findings

The current consistency analysis reviews 40 final shortlisted ESG claims. The stricter rule-based scoring identifies 2 Strong claims, 16 Moderate claims, and 22 Weak claims.

The main analyst takeaway is that most claims still require human review. Many claims contain useful measurable detail, but fewer include the full set of KPI, year, quantitative value, and external validation needed for Strong support.

## Company-Level Findings

- TSMC: 20 claims reviewed. Consistency mix is 1 Strong, 7 Moderate, 12 Weak. Review load is 12 High, 7 Medium, 1 Low priority. Most represented categories: emissions, renewable_energy.
- ASEH: 20 claims reviewed. Consistency mix is 1 Strong, 9 Moderate, 10 Weak. Review load is 10 High, 9 Medium, 1 Low priority. Most represented categories: emissions, renewable_energy.

## Category-Level Findings

- emissions: 10 claims. Consistency mix is 1 Strong, 7 Moderate, 2 Weak. Average scores: specificity 2.80, measurability 2.00, evidence 1.30.
- renewable_energy: 10 claims. Consistency mix is 1 Strong, 1 Moderate, 8 Weak. Average scores: specificity 1.90, measurability 2.00, evidence 1.10.
- supply_chain: 10 claims. Consistency mix is 0 Strong, 7 Moderate, 3 Weak. Average scores: specificity 2.10, measurability 2.10, evidence 1.70.
- governance: 10 claims. Consistency mix is 0 Strong, 1 Moderate, 9 Weak. Average scores: specificity 0.50, measurability 0.70, evidence 0.80.

## Review-Priority Findings

- High Review Priority: 22 claims
- Medium Review Priority: 16 claims
- Low Review Priority: 2 claims

## Most Important Claims Needing Human Review

- TSMC | emissions | page 5: energy solutions , and set 2025 as the baseline year for achieving Scope 1 to 3 absolute emission reduction implementation plan for the “IFRS Sustainability Disclosure
  - Reason: specificity=2, measurability=1, evidence=2; has target or reporting year, quantitative value, implementation detail; missing measurable KPI, standard or validation reference.
- TSMC | renewable_energy | page 108: to achieve target of 100% renewable energy TSMC's power consumption
  - Reason: specificity=2, measurability=2, evidence=1; has measurable KPI, quantitative value; missing target or reporting year, standard or validation reference, implementation detail.
- ASEH | renewable_energy | page 12: facilities’ energy consumption is sourced from renewables, with 88% upstream low-carbon transportation, and the development of a low
  - Reason: specificity=2, measurability=2, evidence=1; has measurable KPI, quantitative value; missing target or reporting year, standard or validation reference, implementation detail.
- TSMC | renewable_energy | page 267: Renewable energy used at overseas subsidiaries (%) 100% 100% 100%
  - Reason: specificity=2, measurability=2, evidence=1; has measurable KPI, quantitative value; missing target or reporting year, standard or validation reference, implementation detail.
- TSMC | renewable_energy | page 29: Climate and Energy 10% Percentage of renewable energy used at all TSMC operation sites 60% 13%
  - Reason: specificity=2, measurability=2, evidence=1; has measurable KPI, quantitative value; missing target or reporting year, standard or validation reference, implementation detail.

## Strongest Supported Claims

- ASEH | renewable_energy | page 116: the baseline, our goal is to increase the renewable energy share by 3% annually, reaching RE25 by 2025, RE72 by 2040, and RE100 by 2050.
  - Why strong: specificity=3, measurability=3, evidence=2; has measurable KPI, target or reporting year, quantitative value, standard or validation reference; missing implementation detail.
- TSMC | emissions | page 266: High-energy-consumption suppliers that have received ISO14064 certification for GHG emissions (%) (Base year: 2021) 65% 84% 90%
  - Why strong: specificity=3, measurability=3, evidence=2; has measurable KPI, target or reporting year, quantitative value, standard or validation reference; missing implementation detail.

## Limitations

- The method is regex-first and can miss claims in tables, charts, or unusual PDF layouts.
- Evidence is currently limited to the source reports and extracted text.
- The pipeline does not perform external validation against SBTi, CDP, filings, or assurance databases yet.
- This is not an official ESG rating.
- This is not investment advice.

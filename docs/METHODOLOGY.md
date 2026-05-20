# Methodology

## Research Question

Are Taiwan semiconductor companies' sustainability claims consistent with their disclosed data, targets, and external risk signals?

## Company Scope

Initial MVP:
- TSMC
- ASE Technology

## Claim Categories

1. Emissions and net-zero claims
2. Renewable energy claims
3. Supply-chain ESG claims

## Claim Schema

Each claim should be recorded as:

```json
{
  "company": "TSMC",
  "report_year": 2024,
  "claim_category": "emissions",
  "claim_text": "...",
  "source_document": "...",
  "source_page": null,
  "quantified": true,
  "target_year": 2050,
  "evidence_needed": "emissions trend / scope coverage / interim target",
  "initial_risk_flag": "medium",
  "notes": "..."
}
```

## Greenwashing Risk Dimensions

Each claim is scored from 0 to 2 on five dimensions:

1. Specificity: Is the claim measurable?
2. Evidence: Is supporting data disclosed?
3. Scope coverage: Does it include Scope 1, 2, and/or 3 where relevant?
4. Time-bound accountability: Are interim targets provided?
5. Consistency: Does the claim align with historical trend or external evidence?

Maximum risk score: 10

Suggested interpretation:
- 0-2: Low risk
- 3-5: Medium risk
- 6-8: High risk
- 9-10: Severe risk

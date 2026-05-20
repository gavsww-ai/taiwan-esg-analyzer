import pandas as pd

from src.claim_extraction import (
    extract_claims_from_pages,
    filter_claims,
    is_supported_report,
    score_risk,
)
from src.pdf_extract import PDFPageText


def test_extract_claims_from_pages_detects_categories_and_template_match():
    template = pd.DataFrame(
        [
            {
                "company": "TSMC",
                "claim_type": "renewable_energy",
                "claim": "Overseas sites used 100% renewable energy",
            }
        ]
    )
    pages = [
        PDFPageText(
            source_document="2024-TSMC-Sustainability-Report-e.pdf",
            page=108,
            text="Overseas sites used 100% renewable energy, accounting for 14.1% of power consumption.",
        )
    ]

    claims = extract_claims_from_pages(pages, template)

    assert len(claims) == 1
    assert claims[0].company == "TSMC"
    assert claims[0].page == 108
    assert claims[0].category == "renewable_energy"
    assert claims[0].confidence_score > 0.7
    assert claims[0].matched_template_claim == "Overseas sites used 100% renewable energy"


def test_filter_claims_removes_generic_and_near_duplicate_claims():
    template = pd.DataFrame(
        [
            {
                "company": "ASEH",
                "claim_type": "emissions",
                "claim": "SBTi-validated near-term 2030 greenhouse gas reduction targets",
            }
        ]
    )
    pages = [
        PDFPageText(
            source_document="aseh-2024-csr-en-final.pdf",
            page=4,
            text=(
                "We strive to create shared value and build a sustainable future. "
                "ASEH has SBTi-validated near-term 2030 greenhouse gas reduction targets of 25%. "
                "ASEH has SBTi validated near term 2030 greenhouse gas reduction targets of 25%."
            ),
        )
    ]

    candidates = extract_claims_from_pages(pages, template)
    filtered = filter_claims(candidates, min_confidence=0.65)

    assert len(filtered) == 1
    assert "2030 greenhouse gas reduction targets of 25%" in filtered[0].claim
    assert filtered[0].risk_level == "Low"


def test_score_risk_levels():
    assert score_risk("SBTi validated 2030 emissions reduction target of 25%.", 0.0)[0] == "Low"
    assert score_risk("Renewable energy accounted for 19% of consumption.", 0.0)[0] == "Medium"
    assert score_risk("We are committed to responsible governance.", 0.0)[0] == "High"


def test_is_supported_report_limits_default_scope_to_project_companies():
    assert is_supported_report("2024-TSMC-Sustainability-Report-e.pdf")
    assert is_supported_report("aseh-2024-csr-en-final.pdf")
    assert not is_supported_report("e-all_2023.pdf")

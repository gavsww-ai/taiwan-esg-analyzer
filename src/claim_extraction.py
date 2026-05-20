from concurrent.futures import ProcessPoolExecutor
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

import pandas as pd

from src.pdf_extract import PDFPageText, extract_pages_from_pdf


CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "emissions": [
        r"\b(?:greenhouse gas|ghg|carbon|co2e?|emissions?|net[- ]zero|scope\s*[123]|sbti)\b",
        r"\b(?:decarboni[sz]ation|carbon neutral|absolute emission reduction)\b",
    ],
    "renewable_energy": [
        r"\b(?:renewable energy|renewables|re100|solar|wind|green electricity|power purchase agreement|ppa)\b",
    ],
    "supply_chain": [
        r"\b(?:supply chain|supplier|procurement|vendor|scope\s*3|cdp|responsible sourcing)\b",
    ],
    "governance": [
        r"\b(?:governance|board|committee|ifrs|esrs|double materiality|internal controls?|task force|assurance)\b",
    ],
}
CATEGORY_REGEXES: Dict[str, List[re.Pattern[str]]] = {
    category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for category, patterns in CATEGORY_PATTERNS.items()
}

CLAIM_SIGNAL_PATTERN = re.compile(
    r"\b("
    r"target|goal|commit(?:ted|ment)?|achiev(?:ed|e)|reduc(?:ed|tion|e)|"
    r"increas(?:ed|e)|use(?:d|s)?|source(?:d|s)?|launch(?:ed)?|establish(?:ed)?|"
    r"adopt(?:ed)?|validat(?:ed|ion)|certif(?:ied|ication)|disclos(?:ed|ure)|"
    r"implement(?:ed|ation)|account(?:ed|ing)?"
    r")\b",
    re.IGNORECASE,
)
STRONG_ACTION_PATTERN = re.compile(
    r"\b(?:target|goal|commit(?:ted)? to|pledge(?:d)? to|will|shall|by\s+20[2-5]\d|"
    r"baseline|agreement|program|achiev(?:ed|e)|reduc(?:ed|e)|launch(?:ed)?|"
    r"establish(?:ed)?|adopt(?:ed)?|validat(?:ed)?|certif(?:ied)?|require(?:d|s)?|"
    r"incorporat(?:ed|e)|implement(?:ed)?)\b",
    re.IGNORECASE,
)

PERCENT_PATTERN = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s?%")
METRIC_PATTERN = re.compile(
    r"(?<!\w)\d+(?:,\d{3})*(?:\.\d+)?\s?"
    r"(?:tons?|tonnes?|mtco2e|tco2e|mwh|gwh|kwh|mw|gw|nt\$|usd|suppliers?|sites?|facilities?)\b",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"\b20[2-5]\d\b")
REDUCTION_PATTERN = re.compile(
    r"\b(?:reduc(?:e|ed|tion)|cut|lower|decarboni[sz]e|net[- ]zero|carbon neutral)\b",
    re.IGNORECASE,
)
SUPPLIER_REQUIREMENT_PATTERN = re.compile(
    r"\b(?:supplier|supply chain|vendor|procurement).{0,80}"
    r"(?:require|must|shall|code of conduct|audit|evaluation|assessment|screening|cdp)\b",
    re.IGNORECASE,
)
GOVERNANCE_ACTION_PATTERN = re.compile(
    r"\b(?:adopt(?:ed)?|establish(?:ed)?|appoint(?:ed)?|approve(?:d)?|"
    r"implement(?:ed|ation)|set up|formed|launched|disclos(?:ed|ure)|assurance|"
    r"board|committee|task force|ifrs|esrs|double materiality|internal controls?)\b",
    re.IGNORECASE,
)
EXTERNAL_VALIDATION_PATTERN = re.compile(
    r"\b(?:sbti|re100|cdp|iso\s?\d+|third[- ]party|externally assured|assurance|"
    r"verified|validated|certified|dnv|tuv|bureau veritas)\b",
    re.IGNORECASE,
)
GENERIC_MARKETING_PATTERN = re.compile(
    r"\b(?:sustainable future|better world|power to change|admired employer|"
    r"innovation pioneer|responsible purchaser|fostering a sustainable culture|"
    r"creating shared value|strive to|endeavor to|lead pioneering|"
    r"in this sustainability report|chairman and chief executive officer|"
    r"according to the latest studies)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractedClaim:
    company: str
    claim: str
    page: int
    category: str
    confidence_score: float
    source_document: str
    matched_template_claim: Optional[str] = None
    template_similarity: float = 0.0
    risk_level: str = "High"
    risk_reason: str = "Vague or aspirational claim without a measurable KPI."


@dataclass(frozen=True)
class PipelineResult:
    all_candidates: List[ExtractedClaim]
    filtered_claims: List[ExtractedClaim]


@dataclass(frozen=True)
class TemplateClaim:
    company: str
    category: str
    claim: str
    tokens: set[str]


def infer_company_from_filename(filename: str) -> str:
    name = filename.lower()
    if "tsmc" in name:
        return "TSMC"
    if "aseh" in name or "ase-" in name or "ase_" in name or "ase " in name:
        return "ASEH"
    return Path(filename).stem


def is_supported_report(filename: str) -> bool:
    company = infer_company_from_filename(filename)
    return company in {"TSMC", "ASEH"}


def load_claims_template(template_path: str | Path) -> pd.DataFrame:
    path = Path(template_path)
    if not path.exists():
        raise FileNotFoundError(f"Claims template not found: {template_path}")
    return pd.read_csv(path)


def is_reasonable_claim_segment(segment: str) -> bool:
    words = re.findall(r"\w+", segment)
    standalone_numbers = re.findall(r"\b\d{1,3}\b", segment)
    if len(words) < 6 or len(words) > 70:
        return False
    if len(segment) > 450:
        return False
    if segment.lower().startswith(("contents ", "table of contents ")):
        return False
    if len(standalone_numbers) >= 4:
        return False
    if re.search(r"\b(?:and|or|of|the|a|an|for|to|with|by|in|our|tsmc's)\s*$", segment, re.IGNORECASE):
        return False
    return True


def split_claim_candidates(text: str) -> List[str]:
    if not text.strip():
        return []

    candidates: List[str] = []
    for line in text.splitlines():
        normalized = re.sub(r"\s+", " ", line).strip(" -\t")
        if not normalized:
            continue
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", normalized)
        for part in parts:
            candidate = part.strip()
            if is_reasonable_claim_segment(candidate):
                candidates.append(candidate)
    return candidates


def detect_category(sentence: str) -> Optional[str]:
    matches = []
    for category, patterns in CATEGORY_REGEXES.items():
        score = sum(1 for pattern in patterns if pattern.search(sentence))
        if score:
            matches.append((score, category))
    if not matches:
        return None
    return sorted(matches, reverse=True)[0][1]


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def normalize_claim(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def build_template_index(template_df: pd.DataFrame) -> List[TemplateClaim]:
    if template_df.empty:
        return []

    template_claims: List[TemplateClaim] = []
    for _, row in template_df.iterrows():
        claim = str(row.get("claim", ""))
        tokens = token_set(claim)
        if not tokens:
            continue
        template_claims.append(
            TemplateClaim(
                company=str(row.get("company", "")).lower(),
                category=str(row.get("claim_type", "")).lower(),
                claim=claim,
                tokens=tokens,
            )
        )
    return template_claims


def compare_to_template(
    sentence: str,
    category: str,
    company: str,
    template_df: pd.DataFrame | List[TemplateClaim],
) -> tuple[Optional[str], float]:
    template_claims = (
        build_template_index(template_df)
        if isinstance(template_df, pd.DataFrame)
        else template_df
    )
    if not template_claims:
        return None, 0.0

    source_tokens = token_set(sentence)
    if not source_tokens:
        return None, 0.0

    category_key = category.lower()
    company_key = company.lower()
    category_matches = [
        item for item in template_claims if not item.category or item.category == category_key
    ]
    same_company = [item for item in category_matches if item.company == company_key]
    candidates = same_company or category_matches

    best_claim = None
    best_score = 0.0
    for template_claim in candidates:
        overlap = source_tokens & template_claim.tokens
        similarity = len(overlap) / len(source_tokens | template_claim.tokens)
        if similarity > best_score:
            best_claim = template_claim.claim
            best_score = similarity
    return best_claim, round(best_score, 3)


def score_confidence(sentence: str, category: str, template_similarity: float) -> float:
    keyword_hits = sum(
        1 for pattern in CATEGORY_REGEXES[category] if pattern.search(sentence)
    )
    has_claim_signal = bool(CLAIM_SIGNAL_PATTERN.search(sentence))
    has_number = bool(re.search(r"\b\d+(?:\.\d+)?%?\b", sentence))

    score = 0.45 + min(keyword_hits, 2) * 0.12
    if has_claim_signal:
        score += 0.15
    if has_number:
        score += 0.10
    score += min(template_similarity, 0.5) * 0.20
    return round(min(score, 0.99), 2)


def has_metric(sentence: str) -> bool:
    return bool(PERCENT_PATTERN.search(sentence) or METRIC_PATTERN.search(sentence))


def has_target_year(sentence: str) -> bool:
    return bool(YEAR_PATTERN.search(sentence))


def has_external_validation(sentence: str, template_similarity: float) -> bool:
    return bool(EXTERNAL_VALIDATION_PATTERN.search(sentence)) or template_similarity >= 0.2


def is_strict_claim(sentence: str, category: str) -> bool:
    if GENERIC_MARKETING_PATTERN.search(sentence):
        return False
    if has_metric(sentence) or has_target_year(sentence):
        return True
    if REDUCTION_PATTERN.search(sentence) and STRONG_ACTION_PATTERN.search(sentence):
        return True
    if category == "supply_chain" and SUPPLIER_REQUIREMENT_PATTERN.search(sentence):
        return True
    if category == "governance" and GOVERNANCE_ACTION_PATTERN.search(sentence) and STRONG_ACTION_PATTERN.search(sentence):
        return True
    return False


def score_risk(sentence: str, template_similarity: float) -> tuple[str, str]:
    metric = has_metric(sentence)
    target_year = has_target_year(sentence)
    evidence = has_external_validation(sentence, template_similarity)

    if metric and target_year and evidence:
        return "Low", "Specific metric, target year, and evidence or validation are present."
    if metric or target_year or evidence:
        missing = []
        if not metric:
            missing.append("specific metric")
        if not target_year:
            missing.append("target year")
        if not evidence:
            missing.append("external validation")
        return "Medium", f"Specific claim, but missing {', '.join(missing)}."
    return "High", "Vague or aspirational claim without a measurable KPI."


def is_near_duplicate(
    claim: ExtractedClaim,
    accepted: List[ExtractedClaim],
    threshold: float = 0.86,
) -> bool:
    claim_tokens = token_set(claim.claim)
    if not claim_tokens:
        return True

    for existing in accepted:
        if claim.company != existing.company or claim.category != existing.category:
            continue
        existing_tokens = token_set(existing.claim)
        if not existing_tokens:
            continue
        similarity = len(claim_tokens & existing_tokens) / len(claim_tokens | existing_tokens)
        if similarity >= threshold:
            return True
    return False


def filter_claims(
    claims: Iterable[ExtractedClaim],
    min_confidence: float = 0.65,
) -> List[ExtractedClaim]:
    filtered: List[ExtractedClaim] = []
    seen = set()

    for claim in claims:
        if claim.confidence_score < min_confidence:
            continue
        if not is_strict_claim(claim.claim, claim.category):
            continue

        dedupe_key = (claim.company, claim.category, normalize_claim(claim.claim))
        if dedupe_key in seen or is_near_duplicate(claim, filtered):
            continue
        filtered.append(claim)
        seen.add(dedupe_key)

    return filtered


def extract_claims_from_pages(
    pages: Iterable[PDFPageText],
    template_df: pd.DataFrame,
    company: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> List[ExtractedClaim]:
    claims: List[ExtractedClaim] = []
    seen = set()
    template_index = build_template_index(template_df)

    for page in pages:
        page_company = company or infer_company_from_filename(page.source_document)
        if not CLAIM_SIGNAL_PATTERN.search(page.text):
            continue
        if not any(pattern.search(page.text) for patterns in CATEGORY_REGEXES.values() for pattern in patterns):
            continue

        page_claim_count = 0
        for sentence in split_claim_candidates(page.text):
            category = detect_category(sentence)
            if not category or not CLAIM_SIGNAL_PATTERN.search(sentence):
                continue

            matched_claim, similarity = compare_to_template(
                sentence=sentence,
                category=category,
                company=page_company,
                template_df=template_index,
            )
            risk_level, risk_reason = score_risk(sentence, similarity)
            claim = ExtractedClaim(
                company=page_company,
                claim=sentence,
                page=page.page,
                category=category,
                confidence_score=score_confidence(sentence, category, similarity),
                source_document=page.source_document,
                matched_template_claim=matched_claim,
                template_similarity=similarity,
                risk_level=risk_level,
                risk_reason=risk_reason,
            )
            dedupe_key = (claim.company, claim.category, claim.page, claim.claim.lower())
            if dedupe_key not in seen:
                claims.append(claim)
                page_claim_count += 1
                seen.add(dedupe_key)
        if progress_callback and page_claim_count:
            progress_callback(
                f"  page {page.page}: found {page_claim_count} candidate claims"
            )

    return claims


def extract_claims_from_pdf(pdf_path: str | Path, template_df: pd.DataFrame) -> List[ExtractedClaim]:
    return extract_claims_from_pages(extract_pages_from_pdf(pdf_path), template_df)


def extract_claims_for_report(pdf_path: str | Path, template_df: pd.DataFrame) -> List[ExtractedClaim]:
    return extract_claims_from_pages(extract_pages_from_pdf(pdf_path), template_df)


def _extract_claims_for_report_worker(args: tuple[str, pd.DataFrame]) -> List[ExtractedClaim]:
    pdf_path, template_df = args
    return extract_claims_for_report(pdf_path, template_df)


def run_pipeline(
    reports_dir: str | Path = "data/reports",
    template_path: str | Path = "data/claims_template.csv",
    output_dir: str | Path = "data/extracted",
    min_confidence: float = 0.65,
    progress_callback: Optional[Callable[[str], None]] = None,
    include_unsupported_reports: bool = False,
    workers: int = 1,
) -> PipelineResult:
    reports_path = Path(reports_dir)
    output_path = Path(output_dir)
    template_df = load_claims_template(template_path)

    if not reports_path.exists():
        raise FileNotFoundError(f"Reports directory not found: {reports_dir}")

    output_path.mkdir(parents=True, exist_ok=True)
    all_claims: List[ExtractedClaim] = []

    all_pdf_paths = sorted(reports_path.glob("*.pdf"))
    pdf_paths = [
        path
        for path in all_pdf_paths
        if include_unsupported_reports or is_supported_report(path.name)
    ]
    skipped_paths = [path for path in all_pdf_paths if path not in pdf_paths]
    if progress_callback:
        progress_callback(f"Found {len(pdf_paths)} PDF reports in {reports_path}")
        for skipped_path in skipped_paths:
            progress_callback(
                f"Skipping unsupported report {skipped_path.name}; use --include-unsupported to parse it"
            )

    worker_count = max(1, min(workers, len(pdf_paths) or 1))
    if worker_count > 1 and progress_callback:
        progress_callback(f"Using {worker_count} document workers")

    if worker_count == 1:
        for index, pdf_path in enumerate(pdf_paths, start=1):
            if progress_callback:
                progress_callback(f"[{index}/{len(pdf_paths)}] Extracting {pdf_path.name}")
            claims = extract_claims_from_pages(
                extract_pages_from_pdf(pdf_path),
                template_df,
                progress_callback=progress_callback,
            )
            all_claims.extend(claims)
            if progress_callback:
                progress_callback(f"  {pdf_path.name}: {len(claims)} candidate claims")
    else:
        worker_args = [(str(pdf_path), template_df) for pdf_path in pdf_paths]
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            for index, (pdf_path, claims) in enumerate(
                zip(pdf_paths, executor.map(_extract_claims_for_report_worker, worker_args)),
                start=1,
            ):
                all_claims.extend(claims)
                if progress_callback:
                    progress_callback(
                        f"[{index}/{len(pdf_paths)}] {pdf_path.name}: {len(claims)} candidate claims"
                    )

    filtered_claims = filter_claims(all_claims, min_confidence=min_confidence)
    if progress_callback:
        progress_callback(
            f"Filtered {len(all_claims)} candidates to {len(filtered_claims)} claims"
        )

    write_claims_json(all_claims, output_path / "all_claim_candidates.json")
    write_filtered_claims_csv(filtered_claims, output_path / "filtered_claims.csv")
    return PipelineResult(all_candidates=all_claims, filtered_claims=filtered_claims)


def write_claims_json(claims: Iterable[ExtractedClaim], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(claim) for claim in claims]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_filtered_claims_csv(claims: Iterable[ExtractedClaim], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "company": claim.company,
            "category": claim.category,
            "claim": claim.claim,
            "page": claim.page,
            "confidence_score": claim.confidence_score,
            "risk_level": claim.risk_level,
            "risk_reason": claim.risk_reason,
        }
        for claim in claims
    ]
    pd.DataFrame(
        rows,
        columns=[
            "company",
            "category",
            "claim",
            "page",
            "confidence_score",
            "risk_level",
            "risk_reason",
        ],
    ).to_csv(path, index=False)

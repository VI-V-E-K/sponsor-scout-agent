import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent / "saas_database.csv"

SAAS_DATABASE = {}

def load_saas_database():
    global SAAS_DATABASE

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"saas_database.csv not found at {CSV_PATH}"
        )

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_id = row["company_id"].strip()
            SAAS_DATABASE[company_id] = {
                "name": row["name"],
                "category": row["category"],
                "niches": row["niches"],
                "description": row["description"],
                "ideal_creator": row["ideal_creator"],
                "audience": row["audience"],
                "pain_point": row["pain_point"],
                "why_sponsor": row["why_sponsor"],
                "pricing_range": row["pricing_range"],
                "website": row["website"],
                "funding": row["funding"],
                "region": row["region"],
            }

def format_for_claude_prompt() -> str:
    """
    Formats the SaaS database into a compact, Claude-friendly block.
    """
    lines = []

    for company in SAAS_DATABASE.values():
        lines.append(
            f"""
Company: {company['name']}
Category: {company['category']}
Niches: {company['niches']}
What they do: {company['description']}
Ideal creators: {company['ideal_creator']}
Audience: {company['audience']}
Pain point solved: {company['pain_point']}
Why they sponsor: {company['why_sponsor']}
Typical pricing: {company['pricing_range']}
Region: {company['region']}
Website: {company['website']}
""".strip()
        )

    return "\n\n".join(lines)

# Load immediately on import
load_saas_database()

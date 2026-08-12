"""
Creates the minimum data needed to actually call POST /api/processes/analyze:
one Industry, one Organization (Northstar Bank), one ValueChain. This is
NOT the full seed script (that's Phase 6 — 8-10 processes, ~30 activities,
etc. per the scoped-down plan in the architecture doc) — this exists so
the Surprise Record Test can be exercised live, today, against a real
Supabase project and a real Groq key, before that full seed script is built.

Usage:
    cd backend
    python scripts/bootstrap_minimal_data.py

Prints the value_chain_id to use in your POST /api/processes/analyze
request body.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Industry, Organization, ValueChain  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Industry).filter(Industry.name == "Banking & Financial Services").first()
        if existing:
            vc = db.query(ValueChain).filter(ValueChain.industry_id == existing.id).first()
            print("Bootstrap data already exists — nothing created.")
            print(f"Industry:   {existing.id}  ({existing.name})")
            if vc:
                print(f"ValueChain: {vc.id}  ({vc.name})")
            return

        industry = Industry(
            name="Banking & Financial Services",
            description="Synthetic industry for the AEGISAI challenge submission.",
        )
        org = Organization(
            name="Northstar Bank",
            description="Fictional retail bank created for this challenge. Not a real institution.",
            is_fictional=True,
            industry=industry,
        )
        value_chain = ValueChain(
            name="Retail Lending",
            description="Loan origination, underwriting, and servicing.",
            industry=industry,
            sequence_order=1,
        )
        db.add_all([industry, org, value_chain])
        db.commit()

        print("Bootstrap data created:")
        print(f"Industry:    {industry.id}  ({industry.name})")
        print(f"Organization: {org.id}  ({org.name})")
        print(f"ValueChain:  {value_chain.id}  ({value_chain.name})")
        print()
        print("Use this value_chain_id in your analyze request, e.g.:")
        print(f'''
curl -X POST http://localhost:8000/api/processes/analyze \\
  -H "Content-Type: application/json" \\
  -d '{{"process_name": "Warehouse Inventory Forecasting", "value_chain_id": "{value_chain.id}"}}'
'''.strip())
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
Seeds the initial process dataset for Northstar Bank — 10 processes across
two value chains (Retail Lending, Trade Finance & Compliance), per the
scoped-down target agreed in docs/architecture/decision-log.md (smaller
than MODUS's suggested 15-20 to fit a 2-day build; a working system with
10 processes beats a padded one with 20).

CRITICAL DESIGN POINT: this script calls the exact same
ProcessAnalysisPipeline.run() that POST /api/processes/analyze uses — the
only difference is `source="seed"` instead of the default "dynamic". This
is not a separate seed-data code path; it is proof that seed data and live
Surprise-Record-Test data are produced by the identical mechanism, per the
MODUS requirement that "a newly added record must use the same processing
mechanism." If you can seed 10 processes with this script, the pipeline
that handles a judge's live input during the interview has already been
exercised 10 times before they ever type anything.

This makes real Groq calls — one per process, 10 total, each 5-25 seconds
depending on retries. Expect this to take several minutes end to end.
Safe to re-run: each process name is checked against existing Process rows
before analysis, and an already-existing process is skipped, not
re-created or duplicated.

Usage:
    cd backend
    python scripts/seed_research_sources.py   # do this first, or seeded
                                                # processes will have no
                                                # evidence attached
    python scripts/seed_processes.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.intelligence.embeddings import get_embedding_provider  # noqa: E402
from app.intelligence.llm_provider import get_llm_provider  # noqa: E402
from app.models import Industry, Organization, ValueChain  # noqa: E402
from app.workers.analysis_pipeline import ProcessAnalysisPipeline  # noqa: E402

INDUSTRY_NAME = "Banking & Financial Services"
ORGANIZATION_NAME = "Northstar Bank"

# (value_chain_name, sequence_order, [(process_name, process_context), ...])
SEED_PLAN: list[tuple[str, int, list[tuple[str, str]]]] = [
    (
        "Retail Lending",
        1,
        [
            (
                "Personal Loan Underwriting",
                "Evaluating individual applicants' creditworthiness, income, and "
                "existing debt to approve or decline unsecured personal loans.",
            ),
            (
                "Mortgage Application Processing",
                "Intake, document verification, and underwriting for residential "
                "mortgage applications, including appraisal coordination and "
                "compliance with lending regulations.",
            ),
            (
                "Credit Card Application Review",
                "Assessing new credit card applications for approval, credit "
                "limit assignment, and risk-based pricing.",
            ),
            (
                "Loan Portfolio Risk Monitoring",
                "Ongoing monitoring of the bank's existing loan portfolio for "
                "early signs of default risk, concentration risk, and covenant "
                "breaches.",
            ),
            (
                "Customer Credit Score Assessment",
                "Pulling and interpreting credit bureau data to generate an "
                "internal creditworthiness assessment used across lending "
                "products.",
            ),
        ],
    ),
    (
        "Trade Finance & Compliance",
        2,
        [
            (
                "Letter of Credit Issuance",
                "Reviewing, structuring, and issuing letters of credit for "
                "corporate clients engaged in international trade.",
            ),
            (
                "Anti-Money Laundering Transaction Screening",
                "Screening customer transactions for suspicious patterns "
                "indicative of money laundering, per BSA/AML obligations.",
            ),
            (
                "Sanctions Compliance Screening",
                "Screening customers and transactions against OFAC and other "
                "sanctions lists before processing.",
            ),
            (
                "Trade Document Verification",
                "Examining shipping documents, invoices, and bills of lading "
                "against letter of credit terms for discrepancies.",
            ),
            (
                "Regulatory Reporting and Filing",
                "Preparing and submitting required regulatory filings (e.g. "
                "suspicious activity reports, call reports) to banking "
                "regulators on schedule.",
            ),
        ],
    ),
]


def _get_or_create_org_structure(db) -> dict[str, ValueChain]:
    """Idempotent — reuses bootstrap_minimal_data.py's Industry/Org/
    'Retail Lending' ValueChain if already present, creates only what's
    missing (notably the second value chain)."""
    industry = db.query(Industry).filter(Industry.name == INDUSTRY_NAME).first()
    if industry is None:
        industry = Industry(
            name=INDUSTRY_NAME,
            description="Synthetic industry for the AEGISAI challenge submission.",
        )
        db.add(industry)
        db.flush()

    org = db.query(Organization).filter(Organization.industry_id == industry.id).first()
    if org is None:
        org = Organization(
            name=ORGANIZATION_NAME,
            description="Fictional retail bank created for this challenge. Not a real institution.",
            is_fictional=True,
            industry=industry,
        )
        db.add(org)

    value_chains_by_name: dict[str, ValueChain] = {}
    for vc_name, seq, _ in SEED_PLAN:
        vc = db.query(ValueChain).filter(
            ValueChain.industry_id == industry.id, ValueChain.name == vc_name
        ).first()
        if vc is None:
            vc = ValueChain(name=vc_name, industry=industry, sequence_order=seq)
            db.add(vc)
            db.flush()
        value_chains_by_name[vc_name] = vc

    db.commit()
    return value_chains_by_name


def main(llm=None, embeddings=None) -> dict:
    """
    llm/embeddings are optional purely so this can be exercised in tests
    with fake providers (see tests/test_seed_scripts.py) — normal usage
    (`python scripts/seed_processes.py`, no arguments) always uses the
    real Groq/sentence-transformers providers exactly as before. Returns
    the results dict so tests can assert on outcomes without parsing
    stdout.
    """
    settings = get_settings()
    db = SessionLocal()

    print("Setting up Industry / Organization / Value Chains...")
    value_chains = _get_or_create_org_structure(db)
    for name, vc in value_chains.items():
        print(f"  {name}: {vc.id}")

    llm = llm or get_llm_provider()
    embeddings = embeddings or get_embedding_provider()

    results = {"seeded": [], "skipped_existing": [], "failed": []}
    total = sum(len(processes) for _, _, processes in SEED_PLAN)
    counter = 0

    for vc_name, _, processes in SEED_PLAN:
        value_chain = value_chains[vc_name]
        for process_name, context in processes:
            counter += 1
            print(f"\n[{counter}/{total}] {process_name} ({vc_name})...")
            start = time.monotonic()

            # Fresh session per process — mirrors how the real API handles
            # one request per session, and keeps one failure's rollback
            # from affecting any other process in this run.
            process_db = SessionLocal()
            try:
                pipeline = ProcessAnalysisPipeline(
                    db=process_db,
                    llm_provider=llm,
                    embedding_provider=embeddings,
                    entity_similarity_threshold=settings.entity_similarity_threshold,
                    evidence_relevance_threshold=settings.evidence_relevance_threshold,
                )
                job = pipeline.run(
                    process_name=process_name,
                    value_chain_id=value_chain.id,
                    process_context=context,
                    source="seed",
                )
                elapsed = time.monotonic() - start

                if job.status.value == "completed":
                    print(f"  DONE in {elapsed:.1f}s -> process_id={job.result_entity_id}")
                    results["seeded"].append(process_name)
                elif "already exists" in (job.error_message or ""):
                    print(f"  SKIPPED (already exists)")
                    results["skipped_existing"].append(process_name)
                else:
                    print(f"  FAILED: {job.error_message}")
                    results["failed"].append((process_name, job.error_message))
            except Exception as exc:  # noqa: BLE001 — keep seeding the rest even if one process errors
                print(f"  ERROR (unexpected): {exc}")
                results["failed"].append((process_name, str(exc)))
            finally:
                process_db.close()

    db.close()

    print("\n" + "=" * 60)
    print("SEED SUMMARY")
    print("=" * 60)
    print(f"Seeded:            {len(results['seeded'])}")
    print(f"Skipped (existing): {len(results['skipped_existing'])}")
    print(f"Failed:            {len(results['failed'])}")
    if results["failed"]:
        print("\nFailures:")
        for name, err in results["failed"]:
            print(f"  - {name}: {err}")
    print("\nRun `curl http://localhost:8000/api/dashboard` (with the server")
    print("running) to see the populated KPIs, or query the DB directly.")
    return results


if __name__ == "__main__":
    main()

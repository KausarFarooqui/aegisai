"""
Curated research corpus for AEGISAI's evidence layer.

Every entry below is a REAL, independently verifiable source with a real
URL — nothing here is invented. Retrieved via web search on 2026-08-12 and
summarized in original wording (not reproduced verbatim), per the MODUS
requirement to distinguish research-derived evidence from synthetic data
and to never fabricate citations.

This is deliberately a curated *sample* (~20 sources), not an exhaustive
literature review — sufficient to prove the evidence-retrieval mechanism
works end to end (semantic search -> Evidence record -> citation shown in
the UI), not a claim of comprehensive regulatory or academic coverage.
Loaded into the database by scripts/seed_research_sources.py, which embeds
each summary with the same EmbeddingProvider the rest of the app uses.

Fields match app/models/evidence.py's ResearchSource:
- source_type: one of law_regulation, regulatory_guidance, industry_standard,
  research, vendor_information, general_web_content (see SourceType enum)
- publication_date: best available estimate from the source itself; None
  where the source is undated (e.g. an evergreen product/framework page)
- retrieved_date: when this corpus was assembled
"""
from datetime import date

RETRIEVED_DATE = date(2026, 8, 12)

RESEARCH_SOURCES: list[dict] = [
    {
        "title": "Practical Applications of AI in Financial Institutions: Lending",
        "url": "https://www.bonadio.com/article/practical-applications-ai-financial-institutions-part-1-lending/",
        "source_type": "research",
        "publication_date": date(2026, 6, 1),
        "summary": (
            "Describes how supervised machine learning models are increasingly used in "
            "commercial loan underwriting to analyze collateral, income, and credit data "
            "faster than traditional rule-based review, with real-time integration into "
            "credit bureau and banking data feeds to support explainable, regulator-facing "
            "credit decisions."
        ),
    },
    {
        "title": "How AI Is Transforming Lending in 2026: Platforms, Automation, and What Actually Works",
        "url": "https://timvero.com/blog/how-ai-and-automation-are-transforming-lending",
        "source_type": "research",
        "publication_date": date(2026, 6, 8),
        "summary": (
            "Reports that AI-enhanced commercial underwriting, automated financial spreading, "
            "covenant monitoring, and portfolio risk alerting have become standard practice at "
            "competitive banks and fintech lenders, with the AI-powered lending market "
            "projected to grow at roughly 25% annually into the mid-2030s."
        ),
    },
    {
        "title": "Lending Transformation: AI, Private Credit, and the Battle for Borrowers",
        "url": "https://www.ccgcatalyst.com/thought-leadership/commentary/lending-transformation-ai-private-credit-and-the-battle-for-borrowers/",
        "source_type": "research",
        "publication_date": date(2026, 4, 8),
        "summary": (
            "Cites Accenture's 2026 Banking Technology Trends findings that AI-first credit "
            "systems can increase automated loan approval rates by roughly half and overall "
            "decisioning throughput by 70-90%, while banks retain relationship managers for "
            "complex, judgment-intensive transactions rather than automating them away."
        ),
    },
    {
        "title": "Generative AI in banking and financial services",
        "url": "https://www.mckinsey.com/industries/financial-services/our-insights/capturing-the-full-value-of-generative-ai-in-banking",
        "source_type": "research",
        "publication_date": date(2023, 12, 5),
        "summary": (
            "Analyzes generative AI's potential across banking functions, noting that large "
            "customer-facing workforces (call center agents, wealth advisers) and a heavily "
            "regulated environment make explainability and workforce transition central "
            "challenges, alongside emerging skill needs such as prompt engineering."
        ),
    },
    {
        "title": "The State of Organizations 2026",
        "url": "https://www.mckinsey.com/~/media/mckinsey/business%20functions/people%20and%20organizational%20performance/our%20insights/the%20state%20of%20organizations/2026/the-state-of-organizations-2026.pdf",
        "source_type": "research",
        "publication_date": date(2026, 1, 1),
        "summary": (
            "Survey research finding that among organizations that eliminated roles due to "
            "generative AI, the majority of leaders reported upskilling, reskilling, or "
            "redeploying affected employees rather than pursuing net headcount reduction — "
            "only about one in five eliminated the role outright."
        ),
    },
    {
        "title": "AI Reskilling in Banking: What Most Banks Are Getting Wrong",
        "url": "https://digitalbankexpert.com/2026/05/ai-reskilling-banking-workforce-transformation",
        "source_type": "general_web_content",
        "publication_date": date(2026, 5, 19),
        "summary": (
            "Argues that most bank AI reskilling programs focus on broad AI-literacy training "
            "rather than redesigning which tasks should remain human-led, framing that "
            "distinction as the actual determinant of whether workforce transformation "
            "efforts change how the institution operates."
        ),
    },
    {
        "title": "AI driven transformation in trade finance: A roadmap for automating letter of credit document examination",
        "url": "https://www.sciencedirect.com/science/article/pii/S2666954425000250",
        "source_type": "research",
        "publication_date": date(2025, 5, 24),
        "summary": (
            "Peer-reviewed roadmap describing how OCR, NLP, and machine learning can automate "
            "letter-of-credit document examination, while emphasizing that banks remain "
            "accountable for examination outcomes regardless of whether the process is manual "
            "or AI-assisted."
        ),
    },
    {
        "title": "Review of artificial intelligence-based applications for money laundering detection",
        "url": "https://www.sciencedirect.com/science/article/pii/S2667305325000985",
        "source_type": "research",
        "publication_date": date(2025, 8, 15),
        "summary": (
            "Academic review finding that AI and machine learning approaches, including "
            "anomaly detection and network-pattern analysis, increasingly outperform "
            "traditional rule-based AML systems, particularly for identifying previously "
            "unclassified fraud and money-laundering patterns."
        ),
    },
    {
        "title": "Exploring Explainable AI in the Financial Sector: Perspectives of Banks and Supervisory Authorities",
        "url": "https://arxiv.org/pdf/2111.02244",
        "source_type": "research",
        "publication_date": None,
        "summary": (
            "Case-study research on real bank AML deployments finding that explainability "
            "tools such as SHAP-based feature attribution are used specifically to support "
            "human investigators reviewing AI-flagged transactions, keeping a human "
            "decision-maker in the loop at the point of action."
        ),
    },
    {
        "title": "OCC Issues Updated Model Risk Management Guidance",
        "url": "https://www.occ.treas.gov/news-issuances/news-releases/2026/nr-occ-2026-29.html",
        "source_type": "regulatory_guidance",
        "publication_date": date(2026, 4, 17),
        "summary": (
            "Official OCC/Federal Reserve/FDIC release announcing revised, risk-based model "
            "risk management guidance that explicitly excludes generative and agentic AI "
            "models from its scope, while noting a forthcoming request for information "
            "specifically addressing banks' use of AI-based models."
        ),
    },
    {
        "title": "Federal Banking Agencies Issue Revised Guidance on Model Risk Management",
        "url": "https://www.sullcrom.com/insights/memo/2026/April/OCC-Fed-FDIC-Issue-Revised-Guidance-Model-Risk-Management",
        "source_type": "regulatory_guidance",
        "publication_date": date(2026, 4, 17),
        "summary": (
            "Legal analysis of the April 2026 interagency model risk management guidance, "
            "noting it narrows the definition of a 'model,' adopts a $30 billion asset "
            "threshold for full applicability, and confirms that AI tools not formally in "
            "scope remain subject to general risk-management expectations that apply to "
            "banking organizations broadly."
        ),
    },
    {
        "title": "OCC Report Signals AI Governance Guidance Is on the Horizon as Banks Navigate Dual-Edged Risks",
        "url": "https://www.consumerfinanceinsights.com/2026/05/19/4745/",
        "source_type": "general_web_content",
        "publication_date": date(2026, 5, 19),
        "summary": (
            "Reports Federal Reserve Vice Chair for Supervision Michelle Bowman's public call "
            "to assess whether existing AI supervisory guidance remains adequate, since "
            "current model risk guidance does not yet extend to generative or agentic AI "
            "systems used by banks."
        ),
    },
    {
        "title": "AI Act: implications for the EU banking and payments sector",
        "url": "https://www.eba.europa.eu/sites/default/files/2025-11/d8b999ce-a1d9-4964-9606-971bbc2aaf89/AI%20Act%20implications%20for%20the%20EU%20banking%20sector.pdf",
        "source_type": "law_regulation",
        "publication_date": date(2025, 11, 21),
        "summary": (
            "Official European Banking Authority analysis confirming that under the EU AI "
            "Act, AI systems used to evaluate consumer creditworthiness or establish credit "
            "scores are classified as high-risk, triggering specific documentation and "
            "compliance obligations for banks operating in the EU."
        ),
    },
    {
        "title": "AI creditworthiness assessment under the EU AI Act",
        "url": "https://www.euai-act.com/articles/credit-scoring-ai-compliance",
        "source_type": "law_regulation",
        "publication_date": date(2026, 8, 4),
        "summary": (
            "Explains that while EU AI Act transparency and registration obligations for "
            "high-risk systems applied from August 2026, the core Chapter III compliance "
            "obligations specific to creditworthiness-assessment systems were subsequently "
            "deferred to December 2027 under the EU's Digital Omnibus package — a concrete "
            "example of how AI governance timelines continue to shift after formal enactment."
        ),
    },
    {
        "title": "EU AI Act Article 6: High-Risk AI Requirements & Penalties",
        "url": "https://www.fluxforce.ai/regulations/eu-ai-act-article-6-high-risk",
        "source_type": "law_regulation",
        "publication_date": date(2026, 5, 29),
        "summary": (
            "Details that retail and commercial banks using AI to evaluate creditworthiness "
            "fall under Annex III, point 5(b) of the EU AI Act as high-risk deployers, facing "
            "documentation, risk-management, and human-oversight obligations, with penalties "
            "reaching a percentage of global annual turnover for violations."
        ),
    },
    {
        "title": "AI Risk Management Framework",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "source_type": "industry_standard",
        "publication_date": None,
        "summary": (
            "NIST's voluntary AI Risk Management Framework, including a generative-AI-specific "
            "profile released in 2024, structures AI governance around four functions "
            "(Govern, Map, Measure, Manage) and is widely referenced by financial institutions "
            "building internal AI governance programs."
        ),
    },
    {
        "title": "What Can Financial Institutions Learn From NIST's AI Risk Management Framework?",
        "url": "https://biztechmagazine.com/article/2026/04/what-can-financial-institutions-learn-nists-ai-risk-management-framework",
        "source_type": "general_web_content",
        "publication_date": date(2026, 4, 16),
        "summary": (
            "Frames NIST's AI RMF as a continuous-improvement discipline rather than a binary "
            "compliance checklist, recommending banks govern third-party AI vendors under "
            "existing third-party risk management practices given limited visibility into "
            "vendor model internals."
        ),
    },
    {
        "title": "AI Fraud Detection in Finance | Banks Using AI Against Money Laundering",
        "url": "https://bolster.ai/blog/the-evolution-of-finance-ais-growing-influence",
        "source_type": "general_web_content",
        "publication_date": date(2025, 10, 11),
        "summary": (
            "Describes HSBC's deployment of AI/ML-based transaction monitoring and NLP-based "
            "document screening to improve AML detection accuracy and reduce false positives "
            "in cross-border transaction review."
        ),
    },
    {
        "title": "JPMorgan, Citi, and Wells Fargo Are Transforming AML, Thanks to AI Tools",
        "url": "https://www.silenteight.com/blog/jpmorgan-citi-and-wells-fargo-are-transforming-aml-thanks-to-ai-tools",
        "source_type": "vendor_information",
        "publication_date": None,
        "summary": (
            "Vendor-published overview of how major US banks including Citi and Wells Fargo "
            "have moved from rule-based to machine-learning and behavioral-analytics "
            "transaction monitoring for AML/KYC compliance, citing reduced false-positive "
            "rates as a key operational benefit."
        ),
    },
    {
        "title": "Transforming trade finance: How AI is reshaping the future of global commerce",
        "url": "https://www.gtreview.com/magazine/gtr-issue-1-2026/transforming-trade-finance-how-ai-is-reshaping-the-future-of-global-commerce/",
        "source_type": "general_web_content",
        "publication_date": date(2026, 3, 26),
        "summary": (
            "Trade-industry publication describing how AI agents embedded in trade finance "
            "platforms support letter-of-credit issuance validation, bank guarantee vetting, "
            "and automated document data extraction alongside large language models."
        ),
    },
]

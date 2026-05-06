"""
Recall@k tests for the hybrid retriever.

For each reference question, we check whether the expected keywords appear
in at least one of the top-k retrieved excerpts.
Recall@k = fraction of questions where the expected content is found in top-k.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.retriever import retrieve

# (question, keywords that must appear in at least one excerpt)
REFERENCE = [
    (
        "What is Iran's nuclear program?",
        ["iran", "nuclear", "uranium", "iaea", "enrichment"],
    ),
    (
        "What are the Abraham Accords?",
        ["abraham accords", "israel", "uae", "bahrain", "normalization"],
    ),
    (
        "Who is Hezbollah and what is their role in Lebanon?",
        ["hezbollah", "lebanon", "iran", "militia"],
    ),
    (
        "What caused the Syrian civil war?",
        ["syria", "assad", "rebel", "protest", "civil war"],
    ),
    (
        "What is Hamas's position on the Israeli-Palestinian conflict?",
        ["hamas", "gaza", "palestine", "israel"],
    ),
    (
        "What is Saudi Arabia's foreign policy toward Iran?",
        ["saudi", "iran", "rivalry", "proxy", "sunni", "shia"],
    ),
    (
        "What role does Turkey play in the Middle East?",
        ["turkey", "erdogan", "nato", "syria", "kurdish"],
    ),
    (
        "What is the status of the West Bank?",
        ["west bank", "palestine", "israel", "settlement", "occupation"],
    ),
]


def _hit(sources, keywords: list[str]) -> bool:
    """Return True if any keyword appears in any excerpt (case-insensitive)."""
    combined = " ".join(s.excerpt.lower() + " " + s.title.lower() for s in sources)
    return any(kw in combined for kw in keywords)


@pytest.mark.asyncio
@pytest.mark.parametrize("question,keywords", REFERENCE)
async def test_recall(question: str, keywords: list[str], db_session: AsyncSession):
    sources = await retrieve(question, db_session)
    assert len(sources) > 0, f"No sources returned for: {question}"
    assert _hit(sources, keywords), (
        f"None of {keywords} found in top-{len(sources)} results for:\n"
        f"  '{question}'\n"
        f"  Titles: {[s.title for s in sources]}"
    )


@pytest.mark.asyncio
async def test_recall_summary(db_session: AsyncSession):
    """Print recall@5 and recall@10 summary (informational, always passes)."""
    hits_at_5 = 0

    for question, keywords in REFERENCE:
        sources = await retrieve(question, db_session)
        if _hit(sources[:5], keywords):
            hits_at_5 += 1

    recall_5 = hits_at_5 / len(REFERENCE)
    print(f"\nRecall@5 : {recall_5:.2%}  ({hits_at_5}/{len(REFERENCE)})")

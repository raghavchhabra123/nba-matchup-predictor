"""Lightweight basketball knowledge base for the chatbot (TF-IDF retrieval).

Documents (metric glossaries, strategy, scouting) were scraped by Blake Wood's
BenchGPT project. We keep it lean: no embeddings / vector DB, just TF-IDF over
chunked markdown (scikit-learn only). retrieve() returns the most relevant
chunks to drop into the assistant's context so it can explain concepts with a
source, while the live matchup numbers stay grounded separately.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KDIR = ROOT / 'knowledge'

# lines that are site nav / boilerplate, not content
_NOISE = re.compile(r'utm_source|sr_xsite|^\s*\*\s*\[|MENU|Logout|Ad-Free|'
                    r'Create Account|Your Account|Sports Reference|cookie', re.I)


def _clean(text: str) -> str:
    keep = [ln for ln in text.splitlines()
            if ln.strip() and not _NOISE.search(ln)]
    return re.sub(r'\s+', ' ', ' '.join(keep))


def _chunks(words: int = 380):
    out = []
    for f in sorted(KDIR.rglob('*.md')):
        clean = _clean(f.read_text(encoding='utf-8', errors='ignore'))
        toks = clean.split()
        if len(toks) < 40:
            continue
        title = f.stem.replace('_', ' ').title()
        for i in range(0, len(toks), words):
            out.append((title, f.parent.name, ' '.join(toks[i:i + words])))
    return out


class KnowledgeBase:
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.chunks = _chunks()
        self.vec = TfidfVectorizer(stop_words='english', ngram_range=(1, 2),
                                   max_features=40000, sublinear_tf=True)
        self.matrix = self.vec.fit_transform([c[2] for c in self.chunks])

    def retrieve(self, query: str, k: int = 3, min_score: float = 0.06):
        from sklearn.metrics.pairwise import linear_kernel
        sims = linear_kernel(self.vec.transform([query]), self.matrix).ravel()
        order = sims.argsort()[::-1][:k]
        return [(self.chunks[i][0], self.chunks[i][1], self.chunks[i][2], float(sims[i]))
                for i in order if sims[i] >= min_score]


def load_kb():
    """Return a KnowledgeBase, or None if docs/sklearn unavailable."""
    try:
        if not KDIR.exists() or not any(KDIR.rglob('*.md')):
            return None
        return KnowledgeBase()
    except Exception:
        return None

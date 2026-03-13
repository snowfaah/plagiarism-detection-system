"""
source_finder.py - Academic source identification and citation matching.
Simulates cross-referencing against major academic databases.
"""
import re
import random
import hashlib
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Academic domain sources with weights
ACADEMIC_SOURCES = [
    {"domain": "arxiv.org", "type": "preprint", "weight": 0.9},
    {"domain": "scholar.google.com", "type": "academic", "weight": 0.95},
    {"domain": "researchgate.net", "type": "academic", "weight": 0.85},
    {"domain": "pubmed.ncbi.nlm.nih.gov", "type": "medical", "weight": 0.9},
    {"domain": "jstor.org", "type": "academic", "weight": 0.88},
    {"domain": "springer.com", "type": "journal", "weight": 0.82},
    {"domain": "elsevier.com", "type": "journal", "weight": 0.8},
    {"domain": "ieee.org", "type": "technical", "weight": 0.85},
    {"domain": "acm.org", "type": "technical", "weight": 0.83},
    {"domain": "wiley.com", "type": "journal", "weight": 0.78},
    {"domain": "nature.com", "type": "journal", "weight": 0.87},
    {"domain": "sciencedirect.com", "type": "journal", "weight": 0.84},
    {"domain": "academia.edu", "type": "academic", "weight": 0.75},
    {"domain": "semanticscholar.org", "type": "academic", "weight": 0.82},
    {"domain": "wikipedia.org", "type": "encyclopedia", "weight": 0.6},
]

def extract_key_phrases(text: str, n: int = 5) -> list:
    """Extract key phrases for source searching."""
    # Extract capitalized phrases (titles, names)
    cap_phrases = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+){1,4}\b', text)
    
    # Extract quoted text
    quoted = re.findall(r'"([^"]{10,100})"', text)
    
    # Extract domain-specific terms (long technical words)
    tech_terms = re.findall(r'\b[a-z]{10,}\b', text.lower())
    
    all_phrases = cap_phrases[:3] + quoted[:2] + tech_terms[:3]
    return all_phrases[:n]


def find_sources(text: str, similarity_score: float) -> list:
    """
    Find potential source matches for the given text.
    Returns a list of potential source matches with similarity percentages.
    """
    if not text or len(text.split()) < 30:
        return []
    
    # Deterministic randomness based on text content
    seed = int(hashlib.md5(text[:200].encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    
    sources = []
    
    if similarity_score < 15:
        # Low plagiarism - maybe 1-2 minor matches
        num_sources = rng.randint(0, 2)
    elif similarity_score < 40:
        num_sources = rng.randint(2, 4)
    elif similarity_score < 70:
        num_sources = rng.randint(4, 7)
    else:
        num_sources = rng.randint(6, 10)
    
    selected_sources = rng.sample(ACADEMIC_SOURCES, min(num_sources, len(ACADEMIC_SOURCES)))
    
    remaining_score = similarity_score
    
    for i, source in enumerate(selected_sources):
        if remaining_score <= 0:
            break
        
        # Distribute similarity score across sources
        if i == len(selected_sources) - 1:
            match_pct = remaining_score
        else:
            max_share = remaining_score * 0.6
            match_pct = rng.uniform(5, max(6, max_share))
        
        match_pct = round(min(match_pct, remaining_score, 95), 1)
        remaining_score -= match_pct * 0.7
        
        if match_pct < 3:
            continue
        
        key_phrases = extract_key_phrases(text)
        query = quote(' '.join(key_phrases[:2])) if key_phrases else "academic+paper"
        
        sources.append({
            "domain": source['domain'],
            "type": source['type'],
            "match_percent": match_pct,
            "url": f"https://{source['domain']}/search?q={query}",
            "title": _generate_source_title(source['domain'], rng),
            "relevance": "high" if match_pct > 30 else "medium" if match_pct > 15 else "low"
        })
    
    return sorted(sources, key=lambda x: x['match_percent'], reverse=True)


def _generate_source_title(domain: str, rng: random.Random) -> str:
    """Generate plausible academic source titles."""
    templates = {
        "arxiv.org": [
            "Advances in {field}: A Comprehensive Survey",
            "Deep Learning Approaches for {topic} Analysis",
            "A Systematic Review of {topic} Methods"
        ],
        "scholar.google.com": [
            "Proceedings of the {year} International Conference on {field}",
            "Journal of {field} Research, Vol. {vol}"
        ],
        "wikipedia.org": [
            "{topic} — Wikipedia, the Free Encyclopedia",
            "Overview of {field} — Wikipedia"
        ]
    }
    
    fields = ["Machine Learning", "Natural Language Processing", "Computer Vision",
              "Biomedical Research", "Climate Science", "Economic Policy",
              "Quantum Computing", "Neural Networks", "Social Sciences"]
    
    default_templates = [
        "Research Paper on {field} ({year})",
        "A Study of {topic} in Academic Context",
        "Journal Article: {field} Methods and Applications"
    ]
    
    domain_templates = templates.get(domain, default_templates)
    template = rng.choice(domain_templates)
    
    return template.format(
        field=rng.choice(fields),
        topic=rng.choice(fields).lower(),
        year=rng.randint(2018, 2024),
        vol=rng.randint(10, 50)
    )


def generate_citation(source: dict, style: str = "APA") -> str:
    """Generate academic citations in various formats."""
    domain = source.get('domain', 'unknown')
    title = source.get('title', 'Untitled Document')
    url = source.get('url', '')
    
    if style.upper() == "APA":
        return f"Author, A. (2023). {title}. Retrieved from {url}"
    elif style.upper() == "MLA":
        return f"Author, Anon. \"{title}.\" {domain.title()}, 2023, {url}."
    elif style.upper() == "CHICAGO":
        return f"Author. \"{title}.\" Accessed 2023. {url}."
    else:
        return f"{title}. {url}"


def get_citations(sources: list, style: str = "APA") -> list:
    """Get formatted citations for all sources."""
    return [
        {
            "source": s['domain'],
            "citation": generate_citation(s, style),
            "style": style
        }
        for s in sources
    ]
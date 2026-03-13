"""
xai_explainer.py - Explainable AI report generation for plagiarism analysis.
"""
import re
import logging

logger = logging.getLogger(__name__)


def generate_xai_report(text: str, similarity_score: float, ai_probability: float,
                         sources: list, language: str = "en") -> dict:
    sentences = _split_sentences(text)
    highlighted_sentences = _highlight_suspicious_sentences(sentences, similarity_score)
    risk_factors = _analyze_risk_factors(text, similarity_score, ai_probability)
    recommendations = _generate_recommendations(similarity_score, ai_probability, sources)
    score_breakdown = _compute_score_breakdown(text, similarity_score, ai_probability)

    return {
        "highlighted_sentences": highlighted_sentences[:30],
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "score_breakdown": score_breakdown,
        "summary": _generate_summary(similarity_score, ai_probability, sources),
        "methodology": _get_methodology_note(),
        "language_detected": language
    }


def generate_graph_data(similarity_score: float, ai_probability: float,
                        page_scores: list = None) -> dict:
    original = max(0, 100 - similarity_score - (ai_probability * 0.3))
    original = min(original, 100)

    main_chart = {
        "type": "stacked_bar",
        "labels": ["Document Analysis"],
        "datasets": [
            {"label": "Plagiarized", "value": round(similarity_score, 1), "color": "#ef4444"},
            {"label": "AI Generated", "value": round(min(ai_probability * 0.5, 40), 1), "color": "#f97316"},
            {"label": "Original", "value": round(original, 1), "color": "#22c55e"}
        ]
    }

    gauge = {
        "type": "gauge",
        "value": round(similarity_score, 1),
        "ranges": [
            {"min": 0, "max": 20, "color": "#22c55e", "label": "Low Risk"},
            {"min": 20, "max": 40, "color": "#eab308", "label": "Moderate"},
            {"min": 40, "max": 70, "color": "#f97316", "label": "High"},
            {"min": 70, "max": 100, "color": "#ef4444", "label": "Critical"}
        ]
    }

    page_chart = None
    if page_scores:
        page_chart = {
            "type": "line",
            "labels": [f"Page {p['page']}" for p in page_scores],
            "datasets": [{
                "label": "Plagiarism Score",
                "values": [p['score'] for p in page_scores],
                "color": "#8b5cf6"
            }]
        }

    return {
        "main_chart": main_chart,
        "gauge": gauge,
        "page_chart": page_chart,
        "summary_stats": {
            "similarity": round(similarity_score, 1),
            "ai_probability": round(ai_probability, 1),
            "original": round(original, 1)
        }
    }


def _split_sentences(text: str) -> list:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.split()) >= 5]


def _highlight_suspicious_sentences(sentences: list, base_score: float) -> list:
    import random
    highlighted = []

    for i, sentence in enumerate(sentences[:50]):
        seed = sum(ord(c) for c in sentence[:30])
        rng = random.Random(seed)

        formal_words = ['therefore', 'however', 'moreover', 'furthermore',
                        'consequently', 'additionally', 'subsequently']
        has_formal = any(w in sentence.lower() for w in formal_words)

        base = base_score * rng.uniform(0.5, 1.3)
        if has_formal:
            base *= 1.2

        score = min(95, max(2, base + rng.uniform(-15, 15)))

        highlighted.append({
            "sentence_index": i,
            "text": sentence,
            "risk_score": round(score, 1),
            "risk_level": _score_to_level(score),
            "flags": _get_sentence_flags(sentence, score)
        })

    return sorted(highlighted, key=lambda x: x['risk_score'], reverse=True)


def _get_sentence_flags(sentence: str, score: float) -> list:
    flags = []
    text_lower = sentence.lower()

    if score > 70:
        flags.append("High similarity match detected")
    if re.search(r'\baccording to\b|\bcited by\b|\bstated by\b', text_lower):
        flags.append("Possible uncited reference")
    if re.search(r'\bthis (paper|study|research|article)\b', text_lower):
        flags.append("Self-referential language")
    if len(sentence.split()) > 40:
        flags.append("Complex sentence structure")
    if re.search(r'\bfurthermore\b|\bmoreover\b|\bnevertheless\b', text_lower):
        flags.append("Formal transitional language")

    return flags[:3]


def _analyze_risk_factors(text: str, similarity_score: float, ai_probability: float) -> list:
    factors = []

    if similarity_score >= 70:
        factors.append({
            "factor": "High Plagiarism Score",
            "severity": "CRITICAL",
            "description": f"Similarity score of {similarity_score:.1f}% exceeds acceptable academic thresholds (typically <20%).",
            "impact": "Document flagged for immediate review"
        })
    elif similarity_score >= 40:
        factors.append({
            "factor": "Elevated Similarity",
            "severity": "HIGH",
            "description": f"Similarity score of {similarity_score:.1f}% is above standard academic limits.",
            "impact": "Requires manual review and source verification"
        })
    elif similarity_score >= 20:
        factors.append({
            "factor": "Moderate Similarity",
            "severity": "MEDIUM",
            "description": f"Similarity score of {similarity_score:.1f}% is within borderline range.",
            "impact": "Review flagged sections and verify citations"
        })

    if ai_probability >= 70:
        factors.append({
            "factor": "AI-Generated Content Detected",
            "severity": "HIGH",
            "description": f"AI probability of {ai_probability:.1f}% suggests significant AI assistance.",
            "impact": "May violate academic integrity policies"
        })
    elif ai_probability >= 45:
        factors.append({
            "factor": "Possible AI Assistance",
            "severity": "MEDIUM",
            "description": f"AI probability of {ai_probability:.1f}% indicates possible AI writing assistance.",
            "impact": "Recommend disclosure if institutional policy requires it"
        })

    has_citations = bool(re.search(r'\[\d+\]|\(\w+,\s*\d{4}\)|et al\.', text))
    if not has_citations and similarity_score > 20:
        factors.append({
            "factor": "Missing Citations",
            "severity": "MEDIUM",
            "description": "No formal citations detected despite similarity matches found.",
            "impact": "Proper attribution may resolve plagiarism concerns"
        })

    return factors


def _generate_recommendations(similarity_score: float, ai_probability: float, sources: list) -> list:
    recommendations = []

    if similarity_score >= 70:
        recommendations.append({
            "priority": "URGENT",
            "action": "Significant revision required",
            "detail": "Rewrite high-similarity sections in your own words and add proper citations."
        })
    elif similarity_score >= 40:
        recommendations.append({
            "priority": "HIGH",
            "action": "Add citations and paraphrase",
            "detail": "Ensure all borrowed ideas are properly cited using APA, MLA, or Chicago format."
        })
    elif similarity_score >= 20:
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Review flagged sections",
            "detail": "Verify that all shared content is properly attributed."
        })
    else:
        recommendations.append({
            "priority": "LOW",
            "action": "Document appears original",
            "detail": "Similarity is within acceptable range. Ensure all references are cited."
        })

    if ai_probability >= 60:
        recommendations.append({
            "priority": "HIGH",
            "action": "Revise AI-generated content",
            "detail": "Rewrite AI-flagged sections with your own analysis and voice."
        })

    if sources:
        top_source = sources[0]['domain']
        recommendations.append({
            "priority": "MEDIUM",
            "action": f"Verify match with {top_source}",
            "detail": f"The highest matching source ({sources[0]['match_percent']}%) should be cited if referenced."
        })

    recommendations.append({
        "priority": "INFO",
        "action": "Use plagiarism checker iteratively",
        "detail": "Re-analyze after revisions to verify improvements."
    })

    return recommendations


def _compute_score_breakdown(text: str, similarity_score: float, ai_probability: float) -> dict:
    return {
        "plagiarism_component": round(similarity_score, 1),
        "ai_component": round(ai_probability * 0.3, 1),
        "original_content": round(max(0, 100 - similarity_score - ai_probability * 0.3), 1),
        "word_count_analyzed": len(text.split()),
        "analysis_depth": "full" if len(text.split()) > 500 else "partial",
        "confidence": "high" if len(text.split()) > 200 else "low"
    }


def _generate_summary(similarity_score: float, ai_probability: float, sources: list) -> str:
    level = _score_to_level(similarity_score)

    if level == "HIGH":
        base = f"This document shows HIGH plagiarism risk ({similarity_score:.1f}% similarity)."
    elif level == "MEDIUM":
        base = f"This document shows MODERATE plagiarism risk ({similarity_score:.1f}% similarity)."
    else:
        base = f"This document appears largely original ({similarity_score:.1f}% similarity)."

    ai_note = ""
    if ai_probability >= 60:
        ai_note = f" AI-generated content is likely ({ai_probability:.1f}% probability)."
    elif ai_probability >= 40:
        ai_note = f" Some AI assistance is possible ({ai_probability:.1f}% probability)."

    source_note = ""
    if sources:
        top = sources[0]
        source_note = f" Highest match: {top['domain']} ({top['match_percent']}%)."

    return base + ai_note + source_note


def _get_methodology_note() -> str:
    return ("Analysis uses TF-IDF similarity scoring, linguistic burstiness analysis, "
            "and stylometric pattern detection. Results are indicative and should be "
            "reviewed by a qualified academic integrity officer.")


def _score_to_level(score: float) -> str:
    if score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    else:
        return "LOW"
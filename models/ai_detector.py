"""
ai_detector.py - AI-generated content detection using linguistic analysis.
Uses burstiness, perplexity proxies, and stylometric features.
"""
import re
import math
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def compute_burstiness(text: str) -> float:
    """
    Burstiness measures variability in word usage.
    Human text has higher burstiness; AI text is more uniform.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < 50:
        return 0.5
    
    word_freq = Counter(words)
    frequencies = list(word_freq.values())
    
    mean = sum(frequencies) / len(frequencies)
    variance = sum((f - mean) ** 2 for f in frequencies) / len(frequencies)
    std = math.sqrt(variance)
    
    # Burstiness = (std - mean) / (std + mean)
    if std + mean == 0:
        return 0.0
    
    burstiness = (std - mean) / (std + mean)
    return round(burstiness, 4)


def compute_sentence_variance(text: str) -> float:
    """AI text tends to have very uniform sentence lengths."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 3]
    
    if len(sentences) < 3:
        return 50.0
    
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    
    return round(variance, 2)


def detect_ai_patterns(text: str) -> dict:
    """Detect common AI writing patterns."""
    patterns = {
        "transitional_phrases": [
            r'\bin conclusion\b', r'\bto summarize\b', r'\bfurthermore\b',
            r'\bmoreover\b', r'\badditionally\b', r'\bnotably\b',
            r'\bit is worth noting\b', r'\bthis highlights\b', r'\bthis demonstrates\b',
            r'\bin summary\b', r'\boverall\b', r'\bultimately\b'
        ],
        "hedging_language": [
            r'\bit is important to\b', r'\bit should be noted\b',
            r'\bit is worth\b', r'\bone might argue\b', r'\bsome may argue\b',
            r'\bit can be argued\b', r'\bthis suggests that\b'
        ],
        "ai_fillers": [
            r'\bdelve into\b', r'\bfascinating\b', r'\blandscape\b',
            r'\bevident\b', r'\bcertainly\b', r'\bclearly\b', r'\bundoubtedly\b',
            r'\bsignificant(ly)?\b', r'\bvarious\b', r'\bcomprehensive\b'
        ]
    }
    
    text_lower = text.lower()
    results = {}
    total_hits = 0
    
    for category, pattern_list in patterns.items():
        hits = sum(1 for p in pattern_list if re.search(p, text_lower))
        results[category] = hits
        total_hits += hits
    
    return results, total_hits


def analyze_ai_probability(text: str) -> dict:
    """
    Estimate probability of AI-generated content.
    Returns score 0-100 where higher = more likely AI.
    """
    if not text or len(text.split()) < 30:
        return {
            "ai_probability": 0.0,
            "confidence": "low",
            "indicators": {}
        }
    
    score = 0.0
    indicators = {}
    
    # 1. Burstiness (low burstiness = AI)
    burstiness = compute_burstiness(text)
    indicators['burstiness'] = burstiness
    if burstiness < -0.3:
        score += 30
    elif burstiness < 0:
        score += 15
    elif burstiness > 0.3:
        score -= 10  # More human-like
    
    # 2. Sentence length variance (low = AI)
    sent_variance = compute_sentence_variance(text)
    indicators['sentence_variance'] = sent_variance
    if sent_variance < 15:
        score += 25
    elif sent_variance < 30:
        score += 12
    
    # 3. AI linguistic patterns
    pattern_results, total_hits = detect_ai_patterns(text)
    indicators['ai_patterns'] = pattern_results
    word_count = len(text.split())
    pattern_density = total_hits / (word_count / 100)
    
    if pattern_density > 5:
        score += 25
    elif pattern_density > 2:
        score += 15
    elif pattern_density > 1:
        score += 8
    
    # 4. Vocabulary sophistication check
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    long_words = [w for w in words if len(w) > 8]
    long_word_ratio = len(long_words) / max(len(words), 1)
    indicators['long_word_ratio'] = round(long_word_ratio, 3)
    
    if long_word_ratio > 0.25:
        score += 15  # AI tends to use complex vocabulary
    elif long_word_ratio > 0.15:
        score += 8
    
    # 5. Punctuation patterns
    exclamation_count = text.count('!')
    question_count = text.count('?')
    punct_ratio = (exclamation_count + question_count) / max(word_count / 100, 1)
    indicators['punct_ratio'] = round(punct_ratio, 3)
    
    if punct_ratio < 0.5:
        score += 10  # AI uses fewer exclamations/questions
    
    # Normalize
    score = max(5, min(95, score))
    
    # Determine confidence
    confidence = "high" if score > 75 or score < 25 else "medium" if score > 60 or score < 40 else "low"
    
    return {
        "ai_probability": round(score, 1),
        "confidence": confidence,
        "indicators": indicators,
        "burstiness": burstiness,
        "pattern_breakdown": pattern_results
    }


def highlight_ai_sections(text: str) -> list:
    """Identify and score individual paragraphs for AI likelihood."""
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.split()) >= 15]
    
    highlighted = []
    for i, para in enumerate(paragraphs[:20]):  # Limit to 20 paragraphs
        result = analyze_ai_probability(para)
        highlighted.append({
            "paragraph_index": i,
            "text_preview": para[:200],
            "ai_probability": result['ai_probability'],
            "risk_level": _get_risk_level(result['ai_probability'])
        })
    
    return highlighted


def _get_risk_level(score: float) -> str:
    if score >= 75:
        return "HIGH"
    elif score >= 45:
        return "MEDIUM"
    else:
        return "LOW"
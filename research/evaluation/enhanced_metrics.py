"""
research/evaluation/enhanced_metrics.py

Provides enhanced linguistic quality metrics beyond HLS for research evaluation.

Includes:
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Sentence Length Variance
- Lexical Diversity (Type-Token Ratio)
- Grammatical Error Rate (simulated)
- Perplexity estimation (simulated)
"""

import re
from collections import Counter
from typing import Dict, List


def count_syllables(word: str) -> int:
    """Estimate syllable count for a word."""
    word = word.lower()
    if len(word) <= 3:
        return 1
    
    # Remove silent e
    word = re.sub(r'(?:[^laeiouy]es|ed|[^laeiouy]e)$', '', word)
    
    # Count vowel groups
    syllables = len(re.findall(r'[aeiouy]+', word))
    
    return max(1, syllables)


def flesch_reading_ease(text: str) -> Dict:
    """
    Calculate Flesch Reading Ease score.
    
    Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    
    Score ranges:
    - 90-100: Very Easy
    - 80-89: Easy
    - 70-79: Fairly Easy
    - 60-69: Standard
    - 50-59: Fairly Difficult
    - 30-49: Difficult
    - 0-29: Very Difficult
    """
    sentences = len(re.split(r'[.!?]+', text))
    words = len(text.split())
    syllables = sum(count_syllables(word) for word in text.split())
    
    if sentences == 0 or words == 0:
        return {"score": 0, "assessment": "Invalid text"}
    
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    score = max(0, min(100, score))  # Clamp to 0-100
    
    if score >= 90:
        assessment = "Very Easy"
    elif score >= 80:
        assessment = "Easy"
    elif score >= 70:
        assessment = "Fairly Easy"
    elif score >= 60:
        assessment = "Standard"
    elif score >= 50:
        assessment = "Fairly Difficult"
    elif score >= 30:
        assessment = "Difficult"
    else:
        assessment = "Very Difficult"
    
    return {
        "score": round(score, 2),
        "assessment": assessment,
        "sentences": sentences,
        "words": words,
        "syllables": syllables,
        "avg_sentence_length": round(words / sentences, 2),
        "avg_syllables_per_word": round(syllables / words, 2)
    }


def flesch_kincaid_grade(text: str) -> Dict:
    """
    Calculate Flesch-Kincaid Grade Level.
    
    Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    
    Returns US grade level equivalent.
    """
    sentences = len(re.split(r'[.!?]+', text))
    words = len(text.split())
    syllables = sum(count_syllables(word) for word in text.split())
    
    if sentences == 0 or words == 0:
        return {"grade_level": 0, "assessment": "Invalid text"}
    
    grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    grade = max(0, min(18, grade))  # Clamp to 0-18
    
    if grade < 1:
        assessment = "Elementary"
    elif grade < 6:
        assessment = "Elementary-Middle School"
    elif grade < 9:
        assessment = "Middle School"
    elif grade < 12:
        assessment = "High School"
    elif grade < 14:
        assessment = "College"
    else:
        assessment = "Graduate+"
    
    return {
        "grade_level": round(grade, 2),
        "assessment": assessment,
        "us_grade": f"Grade {round(grade, 1)}"
    }


def sentence_length_variance(text: str) -> Dict:
    """
    Calculate sentence length variance and standard deviation.
    
    Higher variance indicates more "burstiness" (human-like).
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) < 2:
        return {
            "variance": 0,
            "std_dev": 0,
            "mean": 0,
            "min": 0,
            "max": 0,
            "range": 0,
            "sentence_count": len(sentences)
        }
    
    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
    
    # Normalize variance to 0-1 scale (typical range is 0-100)
    normalized_variance = min(variance / 100, 1.0)
    
    return {
        "variance": round(variance, 2),
        "normalized_variance": round(normalized_variance, 3),
        "std_dev": round(std_dev, 2),
        "mean": round(mean_len, 2),
        "min": min(lengths),
        "max": max(lengths),
        "range": max(lengths) - min(lengths),
        "sentence_count": len(sentences)
    }


def lexical_diversity(text: str) -> Dict:
    """
    Calculate lexical diversity metrics.
    
    - Type-Token Ratio (TTR): unique words / total words
    - Moving Average TTR (MATTR): more robust for longer texts
    - Word frequency distribution
    """
    # Tokenize (simple word extraction)
    words = re.findall(r'\b\w+\b', text.lower())
    
    if len(words) == 0:
        return {
            "ttr": 0,
            "unique_words": 0,
            "total_words": 0,
            "top_10": []
        }
    
    # Type-Token Ratio
    unique_words = set(words)
    ttr = len(unique_words) / len(words)
    
    # Word frequency
    freq = Counter(words)
    top_10 = freq.most_common(10)
    
    # Hapax legomena (words appearing only once)
    hapax = [word for word, count in freq.items() if count == 1]
    hapax_ratio = len(hapax) / len(words)
    
    return {
        "ttr": round(ttr, 3),
        "hapax_ratio": round(hapax_ratio, 3),
        "unique_words": len(unique_words),
        "total_words": len(words),
        "top_10": top_10,
        "avg_word_frequency": round(len(words) / len(unique_words), 2)
    }


def grammatical_error_rate(text: str) -> Dict:
    """
    Estimate grammatical error rate.
    
    This is a simplified heuristic-based approach.
    For production use, integrate with grammar checking APIs.
    """
    errors_detected = []
    words = text.split()
    
    # Common grammar error patterns
    patterns = [
        (r'\ba\b\s+\be\b', 'Article misuse'),
        (r'\bthe\b\s+\bthe\b', 'Repeated article'),
        (r'\ba\b\s+\ba\b', 'Repeated article'),
        (r'\bi\b(?!\')', 'Lowercase "i"'),  # except in contractions
        (r'\s{2,}', 'Extra spaces'),
        (r'[.!?]\s*[a-z]', 'Missing capitalization after sentence'),
    ]
    
    for pattern, error_type in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            errors_detected.extend([error_type] * len(matches))
    
    # Calculate error rate per 100 words
    error_count = len(errors_detected)
    error_rate = (error_count / len(words)) * 100 if words else 0
    
    return {
        "error_count": error_count,
        "error_rate_per_100": round(error_rate, 2),
        "errors": errors_detected[:10],  # First 10 errors
        "is_clean": error_count == 0
    }


def perplexity_estimate(text: str) -> Dict:
    """
    Estimate text perplexity using n-gram statistics.
    
    Lower perplexity = more predictable (potentially AI-like)
    Higher perplexity = less predictable (potentially human-like)
    
    This is a simplified simulation. Real perplexity requires language models.
    """
    words = text.lower().split()
    
    if len(words) < 3:
        return {"perplexity": 0, "normalized": 0}
    
    # Calculate bigram uniqueness
    bigrams = [(words[i], words[i+1]) for i in range(len(words)-1)]
    unique_bigrams = set(bigrams)
    
    # Bigram diversity ratio
    bigram_ratio = len(unique_bigrams) / len(bigrams) if bigrams else 0
    
    # Simulate perplexity (inverse of predictability)
    # Higher ratio = higher perplexity = more human-like
    perplexity = bigram_ratio * 100
    
    # Normalize to 0-1 scale (typical perplexity range varies widely)
    normalized = min(perplexity / 200, 1.0)
    
    return {
        "perplexity_estimate": round(perplexity, 2),
        "normalized": round(normalized, 3),
        "bigram_count": len(bigrams),
        "unique_bigrams": len(unique_bigrams),
        "bigram_repetition_rate": round(1 - bigram_ratio, 3)
    }


def comprehensive_linguistic_analysis(text: str) -> Dict:
    """
    Run all linguistic metrics and return comprehensive analysis.
    """
    return {
        "readability": {
            "flesch_ease": flesch_reading_ease(text),
            "flesch_kincaid": flesch_kincaid_grade(text)
        },
        "sentence_structure": sentence_length_variance(text),
        "lexical_diversity": lexical_diversity(text),
        "grammar_quality": grammatical_error_rate(text),
        "perplexity": perplexity_estimate(text)
    }


def compare_texts(original: str, rewritten: str) -> Dict:
    """
    Compare linguistic metrics between original and rewritten text.
    """
    orig_metrics = comprehensive_linguistic_analysis(original)
    rewrite_metrics = comprehensive_linguistic_analysis(rewritten)
    
    # Calculate improvements
    improvements = {
        "flesch_ease_change": rewrite_metrics["readability"]["flesch_ease"]["score"] - 
                              orig_metrics["readability"]["flesch_ease"]["score"],
        "grade_level_change": orig_metrics["readability"]["flesch_kincaid"]["grade_level"] - 
                              rewrite_metrics["readability"]["flesch_kincaid"]["grade_level"],
        "variance_change": rewrite_metrics["sentence_structure"]["variance"] - 
                           orig_metrics["sentence_structure"]["variance"],
        "ttr_change": rewrite_metrics["lexical_diversity"]["ttr"] - 
                      orig_metrics["lexical_diversity"]["ttr"],
        "error_rate_change": orig_metrics["grammar_quality"]["error_rate_per_100"] - 
                             rewrite_metrics["grammar_quality"]["error_rate_per_100"],
        "perplexity_change": rewrite_metrics["perplexity"]["normalized"] - 
                             orig_metrics["perplexity"]["normalized"]
    }
    
    return {
        "original": orig_metrics,
        "rewritten": rewrite_metrics,
        "improvements": improvements
    }


if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    Machine learning represents a significant area of focus in contemporary discussions.
    Furthermore, the framework aspects require careful consideration of multiple factors.
    Additionally, the methodology aspects demonstrate substantial complexity.
    It is worth noting that understanding these dynamics remains crucial.
    This perspective highlights the complexity inherent in addressing machine learning applications.
    """
    
    print("Comprehensive Linguistic Analysis")
    print("=" * 60)
    
    results = comprehensive_linguistic_analysis(sample_text)
    
    print(f"\nReadability:")
    print(f"  Flesch Ease: {results['readability']['flesch_ease']['score']} ({results['readability']['flesch_ease']['assessment']})")
    print(f"  Grade Level: {results['readability']['flesch_kincaid']['grade_level']} ({results['readability']['flesch_kincaid']['assessment']})")
    
    print(f"\nSentence Structure:")
    print(f"  Variance: {results['sentence_structure']['variance']}")
    print(f"  Std Dev: {results['sentence_structure']['std_dev']}")
    print(f"  Mean Length: {results['sentence_structure']['mean']}")
    
    print(f"\nLexical Diversity:")
    print(f"  TTR: {results['lexical_diversity']['ttr']}")
    print(f"  Unique Words: {results['lexical_diversity']['unique_words']}")
    
    print(f"\nGrammar Quality:")
    print(f"  Errors: {results['grammar_quality']['error_count']}")
    print(f"  Clean: {results['grammar_quality']['is_clean']}")
    
    print(f"\nPerplexity:")
    print(f"  Estimate: {results['perplexity']['perplexity_estimate']}")
    print(f"  Normalized: {results['perplexity']['normalized']}")

"""
research/baselines/simple_paraphraser.py

Implements baseline paraphrasing methods for comparison with FlowWrite.

Baselines:
1. Simple synonym replacement
2. Rule-based sentence restructuring
3. Back-translation (simulated)

These provide lower-bound baselines to demonstrate FlowWrite's value.
"""

import random
from typing import Dict, List


# Simple synonym dictionary for baseline
SYNONYMS = {
    "important": ["crucial", "significant", "vital", "key", "essential"],
    "show": ["demonstrate", "reveal", "indicate", "display", "exhibit"],
    "use": ["utilize", "employ", "apply", "leverage", "implement"],
    "method": ["approach", "technique", "strategy", "procedure", "process"],
    "result": ["outcome", "finding", "conclusion", "effect", "consequence"],
    "change": ["alter", "modify", "adjust", "transform", "shift"],
    "help": ["assist", "aid", "support", "facilitate", "enable"],
    "problem": ["issue", "challenge", "difficulty", "obstacle", "concern"],
    "solution": ["answer", "resolution", "fix", "remedy", "approach"],
    "analyze": ["examine", "investigate", "study", "assess", "evaluate"],
    "significant": ["notable", "substantial", "considerable", "marked", "pronounced"],
    "research": ["study", "investigation", "analysis", "inquiry", "exploration"],
    "develop": ["create", "build", "establish", "formulate", "design"],
    "improve": ["enhance", "optimize", "refine", "advance", "upgrade"]
}


def synonym_replacement(text: str, replacement_rate: float = 0.3) -> str:
    """
    Replace words with synonyms at a given rate.
    
    This is a very basic paraphrasing baseline.
    """
    words = text.split()
    result = []
    
    for word in words:
        # Check if word (lowercase, stripped of punctuation) has synonyms
        clean_word = word.lower().strip('.,!?;:"()')
        
        if clean_word in SYNONYMS and random.random() < replacement_rate:
            synonym = random.choice(SYNONYMS[clean_word])
            # Preserve capitalization
            if word[0].isupper():
                synonym = synonym.capitalize()
            result.append(synonym)
        else:
            result.append(word)
    
    return ' '.join(result)


def sentence_restructure(text: str) -> str:
    """
    Apply simple rule-based sentence restructuring.
    
    Transformations:
    - Active to passive voice (simple patterns)
    - Sentence combining/splitting
    - Clause reordering
    """
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    restructured = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Simple active to passive transformation
        # Pattern: "X shows Y" -> "Y is shown by X"
        if ' shows ' in sentence:
            parts = sentence.split(' shows ')
            if len(parts) == 2:
                sentence = f"{parts[1].strip()} is shown by {parts[0].strip()}"
        
        # Pattern: "X demonstrates Y" -> "Y is demonstrated by X"  
        if ' demonstrates ' in sentence:
            parts = sentence.split(' demonstrates ')
            if len(parts) == 2:
                sentence = f"{parts[1].strip()} is demonstrated by {parts[0].strip()}"
        
        # Pattern: "X uses Y" -> "Y is used by X"
        if ' uses ' in sentence:
            parts = sentence.split(' uses ')
            if len(parts) == 2:
                sentence = f"{parts[1].strip()} is used by {parts[0].strip()}"
        
        # Add transition words occasionally
        transitions = ["Additionally, ", "Furthermore, ", "Moreover, ", "In addition, "]
        if random.random() < 0.2 and not any(sentence.startswith(t.split()[0]) for t in transitions):
            sentence = random.choice(transitions) + sentence.lower()
        
        restructured.append(sentence)
    
    return '. '.join(restructured) + '.'


def back_translate_simulated(text: str) -> str:
    """
    Simulate back-translation paraphrasing.
    
    Real back-translation would use translation APIs.
    This simulates the effect with word order changes and synonym substitution.
    """
    sentences = text.split('.')
    result = []
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        words = sentence.split()
        
        # Simulate translation variance by:
        # 1. Occasionally reversing clause order
        # 2. Replacing common words
        # 3. Adding/removing filler words
        
        if ',' in sentence and random.random() < 0.3:
            # Reverse clause order
            clauses = sentence.split(',')
            if len(clauses) >= 2:
                sentence = clauses[-1].strip() + ', ' + ', '.join(clauses[:-1]).strip()
        
        # Add/remove filler words
        fillers = ["it is worth noting that", "it should be mentioned", "essentially"]
        if random.random() < 0.2:
            sentence = random.choice(fillers).capitalize() + ', ' + sentence.lower()
        
        result.append(sentence)
    
    return '. '.join(result) + '.'


def combined_baseline(text: str, method: str = "all") -> Dict:
    """
    Apply one or all baseline methods.
    
    Returns paraphrased text and metadata.
    """
    import time
    start_time = time.time()
    
    if method == "synonym":
        paraphrased = synonym_replacement(text)
    elif method == "restructure":
        paraphrased = sentence_restructure(text)
    elif method == "backtranslate":
        paraphrased = back_translate_simulated(text)
    else:  # "all" - apply all methods sequentially
        paraphrased = synonym_replacement(text)
        paraphrased = sentence_restructure(paraphrased)
        paraphrased = back_translate_simulated(paraphrased)
    
    elapsed = time.time() - start_time
    
    return {
        "original": text,
        "paraphrased": paraphrased,
        "method": method,
        "processing_time": elapsed,
        "word_count_original": len(text.split()),
        "word_count_paraphrased": len(paraphrased.split())
    }


def run_baseline_comparison(texts: List[str]) -> Dict:
    """
    Run all baseline methods on a list of texts.
    
    Returns aggregated statistics.
    """
    results = {
        "synonym": [],
        "restructure": [],
        "backtranslate": [],
        "combined": []
    }
    
    for i, text in enumerate(texts):
        print(f"\rProcessing text {i+1}/{len(texts)}...", end="", flush=True)
        
        for method in results.keys():
            result = combined_baseline(text, method)
            results[method].append(result)
    
    print("\nBaseline comparison complete!")
    
    # Calculate average processing times
    stats = {}
    for method, method_results in results.items():
        avg_time = sum(r["processing_time"] for r in method_results) / len(method_results)
        avg_word_change = sum(
            abs(r["word_count_paraphrased"] - r["word_count_original"]) 
            for r in method_results
        ) / len(method_results)
        
        stats[method] = {
            "avg_processing_time": avg_time,
            "avg_word_change": avg_word_change,
            "samples_processed": len(method_results)
        }
    
    return {
        "detailed_results": results,
        "statistics": stats
    }


if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    Machine learning represents a significant area of focus in contemporary discussions.
    Furthermore, the framework aspects require careful consideration of multiple factors.
    Research has shown that these methodologies demonstrate substantial complexity.
    It is important to note that understanding these dynamics remains crucial.
    """
    
    print("=" * 70)
    print("Baseline Paraphrasing Methods Test")
    print("=" * 70)
    
    print("\nOriginal Text:")
    print("-" * 40)
    print(sample_text)
    
    methods = ["synonym", "restructure", "backtranslate", "all"]
    
    for method in methods:
        result = combined_baseline(sample_text, method)
        print(f"\n\n{method.upper()} Method:")
        print("-" * 40)
        print(result["paraphrased"])
        print(f"\nProcessing time: {result['processing_time']:.4f}s")
        print(f"Word count change: {result['word_count_paraphrased'] - result['word_count_original']:+d}")
    
    print("\n" + "=" * 70)

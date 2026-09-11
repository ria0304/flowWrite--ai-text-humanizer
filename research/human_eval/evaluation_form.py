"""
research/human_eval/evaluation_form.py

Generates human evaluation forms and collects ratings for FlowWrite research.

Human evaluators rate text samples on:
- Naturalness (1-5)
- Fluency (1-5)
- Coherence (1-5)
- Meaning Preservation (1-5)
- Overall Writing Quality (1-5)
- AI vs Human judgment
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict


OUTPUT_DIR = Path("research/human_eval")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset_samples(n_samples: int = 30) -> List[Dict]:
    """Load a representative sample of documents for human evaluation."""
    
    metadata_file = Path("research/datasets/generated/dataset_metadata.json")
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    
    documents = data["documents"]
    
    # Stratified sampling: ensure balance across domains and LLM sources
    domains = list(set(d["domain"] for d in documents))
    llm_sources = list(set(d["llm_source"] for d in documents))
    
    samples = []
    target_per_stratum = n_samples // (len(domains) * len(llm_sources))
    
    for domain in domains:
        for llm in llm_sources:
            stratum_docs = [d for d in documents if d["domain"] == domain and d["llm_source"] == llm]
            selected = random.sample(stratum_docs, min(target_per_stratum, len(stratum_docs)))
            samples.extend(selected)
    
    # Shuffle and limit to n_samples
    random.shuffle(samples)
    return samples[:n_samples]


def generate_evaluation_form(sample: Dict, form_id: int) -> Dict:
    """Generate a single evaluation form for one document."""
    
    return {
        "form_id": form_id,
        "document_id": sample["id"],
        "domain": sample["domain"],
        "llm_source": sample["llm_source"],
        "word_count": sample["word_count"],
        "text": sample["text"],
        "evaluation_criteria": {
            "naturalness": {
                "question": "How natural does this text sound?",
                "scale": "1 (Very Artificial) to 5 (Completely Natural)",
                "rating": None
            },
            "fluency": {
                "question": "How fluent is the writing?",
                "scale": "1 (Choppy/Disjointed) to 5 (Smooth/Flowing)",
                "rating": None
            },
            "coherence": {
                "question": "How coherent is the text?",
                "scale": "1 (Confusing) to 5 (Clear and Logical)",
                "rating": None
            },
            "meaning_preservation": {
                "question": "How well does the text preserve its intended meaning?",
                "scale": "1 (Meaning Lost) to 5 (Meaning Fully Preserved)",
                "rating": None,
                "note": "Compare against the original topic/intent"
            },
            "overall_quality": {
                "question": "What is your overall assessment of the writing quality?",
                "scale": "1 (Poor) to 5 (Excellent)",
                "rating": None
            }
        },
        "ai_human_judgment": {
            "question": "Do you think this text was written by:",
            "options": ["Definitely AI", "Probably AI", "Unsure", "Probably Human", "Definitely Human"],
            "selection": None
        },
        "comments": {
            "question": "Any additional comments or observations?",
            "response": ""
        },
        "evaluator_id": None,
        "timestamp": None
    }


def generate_comparison_form(original: Dict, rewritten: Dict, form_id: int) -> Dict:
    """Generate a side-by-side comparison form."""
    
    return {
        "form_id": form_id,
        "document_id_original": original["id"],
        "document_id_rewritten": rewritten["id"],
        "domain": original["domain"],
        "comparison_criteria": {
            "which_is_more_natural": {
                "question": "Which text sounds more natural?",
                "options": ["Text A", "Text B", "No clear difference"],
                "selection": None
            },
            "which_is_better_quality": {
                "question": "Which text has better overall quality?",
                "options": ["Text A", "Text B", "No clear difference"],
                "selection": None
            },
            "meaning_preserved": {
                "question": "Is the meaning preserved between the two texts?",
                "options": ["Yes, completely", "Mostly", "Partially", "No, significant changes"],
                "selection": None
            }
        },
        "text_a": original["text"],
        "text_b": rewritten["text"],
        "evaluator_id": None,
        "timestamp": None
    }


def create_evaluation_packet(n_samples: int = 30, output_dir: Path = OUTPUT_DIR):
    """Create complete evaluation packet for human evaluators."""
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Load samples
    samples = load_dataset_samples(n_samples)
    
    # Generate individual evaluation forms
    forms = []
    for i, sample in enumerate(samples):
        form = generate_evaluation_form(sample, form_id=i+1)
        forms.append(form)
    
    # Create evaluator instructions
    instructions = {
        "title": "FlowWrite Human Evaluation Study",
        "description": "This study evaluates the quality of AI-generated text after processing through the FlowWrite rewriting system.",
        "instructions": [
            "Read each text sample carefully.",
            "Rate each sample on the five criteria using the 1-5 scale.",
            "Make your AI vs Human judgment based on your intuition.",
            "Take breaks between samples to maintain consistency.",
            "There are no right or wrong answers - we want your honest assessment."
        ],
        "criteria_definitions": {
            "Naturalness": "Does the text sound like something a human would write, or does it feel robotic/artificial?",
            "Fluency": "Does the text flow smoothly from sentence to sentence, or is it choppy?",
            "Coherence": "Are the ideas logically connected and easy to follow?",
            "Meaning Preservation": "Does the text effectively communicate its intended message?",
            "Overall Quality": "Your holistic assessment of the writing quality."
        },
        "estimated_time": "15-20 minutes for 30 samples",
        "contact": "research@flowwrite.example.com"
    }
    
    # Package everything
    packet = {
        "study_info": instructions,
        "evaluation_forms": forms,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_samples": n_samples,
            "domains_covered": list(set(s["domain"] for s in samples)),
            "llm_sources_covered": list(set(s["llm_source"] for s in samples))
        }
    }
    
    # Save packet
    packet_file = output_dir / "human_evaluation_packet.json"
    with open(packet_file, 'w') as f:
        json.dump(packet, f, indent=2)
    
    # Also save as plain text for easy printing
    text_file = output_dir / "human_evaluation_packet.txt"
    with open(text_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("FLOWWRITE HUMAN EVALUATION STUDY\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("INSTRUCTIONS:\n")
        f.write("-" * 40 + "\n")
        for instruction in instructions["instructions"]:
            f.write(f"• {instruction}\n")
        f.write("\n")
        
        f.write("CRITERIA DEFINITIONS:\n")
        f.write("-" * 40 + "\n")
        for criterion, definition in instructions["criteria_definitions"].items():
            f.write(f"{criterion}: {definition}\n")
        f.write("\n")
        
        f.write("RATING SCALE:\n")
        f.write("-" * 40 + "\n")
        f.write("1 = Very Poor / Very Artificial\n")
        f.write("2 = Poor / Somewhat Artificial\n")
        f.write("3 = Acceptable / Neutral\n")
        f.write("4 = Good / Mostly Natural\n")
        f.write("5 = Excellent / Completely Natural\n")
        f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("EVALUATION FORMS\n")
        f.write("=" * 70 + "\n\n")
        
        for form in forms:
            f.write(f"Form ID: {form['form_id']}\n")
            f.write(f"Document: {form['document_id']}\n")
            f.write(f"Domain: {form['domain']}\n")
            f.write(f"LLM Source: {form['llm_source']}\n")
            f.write(f"Word Count: {form['word_count']}\n")
            f.write("\nTEXT:\n")
            f.write("-" * 40 + "\n")
            f.write(f"{form['text'][:500]}...\n")  # Preview only
            f.write("\n\nRATINGS:\n")
            f.write("-" * 40 + "\n")
            for criterion, data in form["evaluation_criteria"].items():
                f.write(f"{criterion.capitalize()}: ___ / 5\n")
            f.write(f"\nAI/Human Judgment: _______________\n")
            f.write(f"Comments: ________________________\n")
            f.write("\n" + "=" * 70 + "\n\n")
    
    print(f"Evaluation packet created:")
    print(f"  JSON: {packet_file}")
    print(f"  Text: {text_file}")
    print(f"  Samples: {n_samples}")
    print(f"  Domains: {packet['metadata']['domains_covered']}")
    print(f"  LLM Sources: {packet['metadata']['llm_sources_covered']}")
    
    return packet


def collect_responses(packet_file: Path) -> Dict:
    """Template for collecting and aggregating evaluator responses."""
    
    # This would be implemented when actual responses are collected
    # For now, returns a template structure
    
    return {
        "study_id": "flowwrite_human_eval_001",
        "responses": [],
        "aggregated_results": {
            "by_criterion": {},
            "by_domain": {},
            "by_llm_source": {},
            "ai_human_distribution": {}
        },
        "statistical_analysis": {
            "mean_scores": {},
            "std_dev": {},
            "inter_rater_reliability": None,
            "significance_tests": {}
        }
    }


if __name__ == "__main__":
    print("=" * 70)
    print("FlowWrite Human Evaluation Packet Generator")
    print("=" * 70)
    
    packet = create_evaluation_packet(n_samples=30)
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("1. Distribute evaluation packet to human evaluators")
    print("2. Collect completed forms")
    print("3. Enter responses into analysis spreadsheet")
    print("4. Run statistical analysis")
    print("=" * 70)

#!/usr/bin/env python3
"""
research/experiments/stage5_ablation/run_experiment.py

Stage 5 Ablation Experiment Runner

This script runs the Stage 5 ON/OFF ablation experiment using the REAL FlowWrite pipeline.
It does NOT use simulated transformations.

CONTROL: Stages 1-4, Stage 5 OFF
TREATMENT: Stages 1-4, Stage 5 ON
"""

import asyncio
import json
import os
import sys
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipeline.pipeline_controller_v2 import run_pipeline_v2
from evaluation.hls import compute_hls
from evaluation.semantic_similarity import semantic_similarity


def load_config() -> Dict:
    """Load experiment configuration."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def load_seeds() -> Dict:
    """Load random seed configuration."""
    seeds_path = Path(__file__).parent.parent.parent / "config" / "seeds.json"
    with open(seeds_path, 'r') as f:
        return json.load(f)


def get_document_paths(dataset_dir: str, sample_size: int = 20) -> List[Path]:
    """Get paths to documents for the experiment."""
    dataset_path = Path(dataset_dir)
    
    # Check for texts subdirectory (where actual documents are stored)
    texts_path = dataset_path / "texts"
    if texts_path.exists():
        dataset_path = texts_path
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")
    
    # Get all txt files (generated documents)
    doc_files = list(dataset_path.glob("*.txt"))
    
    if len(doc_files) == 0:
        # Try json files
        doc_files = list(dataset_path.glob("*.json"))
    
    if len(doc_files) == 0:
        raise FileNotFoundError(f"No documents found in {dataset_path}")
    
    # Load seeds for reproducible sampling
    seeds = load_seeds()
    random.seed(seeds["experiments"]["stage5_ablation"]["seed"])
    
    # Sample documents
    selected = random.sample(doc_files, min(sample_size, len(doc_files)))
    
    # Reset seed after sampling
    random.seed(seeds["default_seed"])
    
    return sorted(selected)


def load_document(doc_path: Path) -> Dict:
    """Load a document from the dataset."""
    if doc_path.suffix == '.json':
        with open(doc_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(doc_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return {
            "id": doc_path.stem,
            "text": text,
            "domain": doc_path.stem.split('_')[0] if '_' in doc_path.stem else "unknown"
        }


def compute_content_preservation(original: str, transformed: str) -> Dict:
    """Compute content preservation metrics between original and transformed text."""
    # Remove invisible characters for fair comparison
    ZWSP = "\u200b"
    SHY = "\u00ad"
    
    original_clean = original
    transformed_visible = ''.join(c for c in transformed if c not in [ZWSP, SHY])
    
    # Character-level comparison
    char_diff = abs(len(original_clean) - len(transformed_visible))
    
    # Word-level comparison
    original_words = set(original_clean.lower().split())
    transformed_words = set(transformed_visible.lower().split())
    
    word_intersection = original_words & transformed_words
    word_precision = len(word_intersection) / len(transformed_words) if transformed_words else 0
    word_recall = len(word_intersection) / len(original_words) if original_words else 0
    word_f1 = 2 * word_precision * word_recall / (word_precision + word_recall) if (word_precision + word_recall) > 0 else 0
    
    # Semantic similarity
    try:
        semantic_sim_result = semantic_similarity(original_clean, transformed_visible)
        semantic_sim = semantic_sim_result.get("score", 0.0) if isinstance(semantic_sim_result, dict) else 0.0
    except Exception as e:
        semantic_sim = {"similarity": 0.0, "error": str(e)}
    
    return {
        "char_difference": char_diff,
        "word_precision": round(word_precision, 4),
        "word_recall": round(word_recall, 4),
        "word_f1": round(word_f1, 4),
        "semantic_similarity": semantic_sim if not isinstance(semantic_sim, dict) else 0.0
    }


def get_system_metadata() -> Dict:
    """Get system metadata for reproducibility."""
    import platform
    
    # Get Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Try to get package versions
    try:
        import importlib.metadata
        packages = {}
        for pkg in ['torch', 'transformers', 'sentence-transformers', 'numpy', 'pandas']:
            try:
                packages[pkg] = importlib.metadata.version(pkg)
            except importlib.metadata.PackageNotFoundError:
                packages[pkg] = "not_installed"
    except Exception:
        packages = {}
    
    return {
        "python_version": python_version,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "package_versions": packages
    }


async def run_single_experiment(
    document: Dict,
    condition: str,
    enable_stage5: bool,
    config: Dict
) -> Dict:
    """Run a single experimental condition on a document."""
    
    experiment_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    result = {
        "experiment_id": experiment_id,
        "document_id": document.get("id", "unknown"),
        "dataset_id": "flowwrite_simulated_v1",
        "dataset_version": "1.0.0",
        "condition": condition,
        "stage5_enabled": enable_stage5,
        "timestamp": timestamp,
        "pipeline_success": False,
        "failure_reason": None,
        "input_text": document.get("text", "")[:500],  # Truncate for storage
        "input_length": len(document.get("text", "")),
        "intermediate_length": None,
        "final_output_length": None,
        "stage5_metadata": None,
        "evaluation_metrics": {},
        "content_preservation": {},
        "system_metadata": get_system_metadata()
    }
    
    try:
        # Get pipeline parameters
        tone = config["pipeline"]["tone"]
        aggressiveness = config["pipeline"]["aggressiveness"]
        
        # Run pipeline
        input_text = document.get("text", "")
        result["input_length"] = len(input_text)
        
        pipeline_result = await run_pipeline_v2(
            text=input_text,
            tone=tone,
            aggressiveness=aggressiveness,
            enable_stage5=enable_stage5
        )
        
        output_text = pipeline_result.get("final", "")
        result["intermediate_length"] = len(output_text)
        result["final_output_length"] = len(output_text)
        result["pipeline_success"] = True
        
        # Extract Stage 5 metadata if available
        if enable_stage5 and "stage5_applied" in pipeline_result:
            # We need to get Stage 5 metadata from line_breaker
            from pipeline.line_breaker import apply_line_break_trick_with_metadata
            
            # Get the text before Stage 5 (we need to reconstruct this)
            # For now, we'll analyze the final output
            stage5_meta = apply_line_break_trick_with_metadata(output_text)
            result["stage5_metadata"] = {
                "zwsp_count": stage5_meta.get("zwsp_count", 0),
                "shy_count": stage5_meta.get("shy_count", 0),
                "total_insertions": stage5_meta.get("total_insertions", 0),
                "utf8_valid": stage5_meta.get("utf8_valid", False),
                "success": stage5_meta.get("success", False)
            }
        
        # Compute HLS
        try:
            hls_result = compute_hls(input_text, output_text)
            result["evaluation_metrics"]["hls"] = {
                "total_score": hls_result.get("total_score", 0.0),
                "dimensions": {k: v.get("score", 0.0) for k, v in hls_result.get("dimensions", {}).items()}
            }
        except Exception as e:
            result["evaluation_metrics"]["hls_error"] = str(e)
        
        # Compute content preservation
        try:
            result["content_preservation"] = compute_content_preservation(input_text, output_text)
        except Exception as e:
            result["content_preservation_error"] = str(e)
        
        # Store full output (truncated for storage)
        result["output_text"] = output_text[:2000]
        
    except Exception as e:
        result["pipeline_success"] = False
        result["failure_reason"] = str(e)
        result["error_traceback"] = repr(e)
    
    return result


async def run_experiment(pilot: bool = True):
    """Run the complete Stage 5 ablation experiment."""
    
    print("=" * 60)
    print("STAGE 5 ABLATION EXPERIMENT")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    seeds = load_seeds()
    
    # Set random seed
    random.seed(seeds["experiments"]["stage5_ablation"]["seed"])
    
    # Determine sample size
    sample_size = 20 if pilot else config["dataset"]["sample_size"]
    print(f"\nMode: {'PILOT' if pilot else 'FULL'}")
    print(f"Sample size: {sample_size} documents")
    
    # Get documents
    dataset_dir = Path(config["dataset"]["source"])
    doc_paths = get_document_paths(str(dataset_dir), sample_size)
    print(f"Found {len(doc_paths)} documents")
    
    # Prepare results storage
    results_dir = Path(config["output"]["raw_results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    control_results = []
    treatment_results = []
    
    # Run experiment for each document
    for i, doc_path in enumerate(doc_paths):
        print(f"\n[{i+1}/{len(doc_paths)}] Processing {doc_path.name}...")
        
        try:
            document = load_document(doc_path)
            doc_id = document.get("id", doc_path.stem)
            
            # CONTROL: Stage 5 OFF
            print(f"  → Running CONTROL (Stage 5 OFF)...")
            control_result = await run_single_experiment(
                document=document,
                condition="control",
                enable_stage5=False,
                config=config
            )
            control_result["document_id"] = doc_id
            control_results.append(control_result)
            all_results.append(control_result)
            
            # Save control result
            control_path = results_dir / f"{doc_id}_control.json"
            with open(control_path, 'w', encoding='utf-8') as f:
                json.dump(control_result, f, indent=2, ensure_ascii=False)
            
            if control_result["pipeline_success"]:
                print(f"    ✓ Control successful")
            else:
                print(f"    ✗ Control failed: {control_result.get('failure_reason', 'Unknown')}")
            
            # TREATMENT: Stage 5 ON
            print(f"  → Running TREATMENT (Stage 5 ON)...")
            treatment_result = await run_single_experiment(
                document=document,
                condition="treatment",
                enable_stage5=True,
                config=config
            )
            treatment_result["document_id"] = doc_id
            treatment_results.append(treatment_result)
            all_results.append(treatment_result)
            
            # Save treatment result
            treatment_path = results_dir / f"{doc_id}_treatment.json"
            with open(treatment_path, 'w', encoding='utf-8') as f:
                json.dump(treatment_result, f, indent=2, ensure_ascii=False)
            
            if treatment_result["pipeline_success"]:
                print(f"    ✓ Treatment successful")
                if treatment_result.get("stage5_metadata"):
                    meta = treatment_result["stage5_metadata"]
                    print(f"      ZWSP: {meta['zwsp_count']}, SHY: {meta['shy_count']}, Total: {meta['total_insertions']}")
            else:
                print(f"    ✗ Treatment failed: {treatment_result.get('failure_reason', 'Unknown')}")
            
        except Exception as e:
            print(f"  ✗ Error processing document: {e}")
            continue
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    
    total_attempted = len(doc_paths)
    control_successful = sum(1 for r in control_results if r["pipeline_success"])
    treatment_successful = sum(1 for r in treatment_results if r["pipeline_success"])
    
    print(f"Documents attempted: {total_attempted}")
    print(f"Control (Stage 5 OFF) successful: {control_successful}/{total_attempted}")
    print(f"Treatment (Stage 5 ON) successful: {treatment_successful}/{total_attempted}")
    
    # Stage 5 statistics (for successful treatments)
    successful_treatments = [r for r in treatment_results if r["pipeline_success"] and r.get("stage5_metadata")]
    if successful_treatments:
        total_zwsp = sum(r["stage5_metadata"]["zwsp_count"] for r in successful_treatments)
        total_shy = sum(r["stage5_metadata"]["shy_count"] for r in successful_treatments)
        total_insertions = sum(r["stage5_metadata"]["total_insertions"] for r in successful_treatments)
        
        print(f"\nStage 5 Perturbations (across {len(successful_treatments)} successful treatments):")
        print(f"  ZWSP insertions: {total_zwsp}")
        print(f"  SHY insertions: {total_shy}")
        print(f"  Total insertions: {total_insertions}")
        print(f"  Average per document: {total_insertions / len(successful_treatments):.2f}")
    
    # Save aggregated results
    processed_dir = Path(config["output"]["processed_results_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    summary = {
        "experiment_name": config["experiment_name"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "pilot" if pilot else "full",
        "documents_attempted": total_attempted,
        "control_successful": control_successful,
        "treatment_successful": treatment_successful,
        "stage5_statistics": {
            "total_zwsp": total_zwsp if successful_treatments else 0,
            "total_shy": total_shy if successful_treatments else 0,
            "total_insertions": total_insertions if successful_treatments else 0,
            "avg_per_document": (total_insertions / len(successful_treatments)) if successful_treatments else 0
        }
    }
    
    summary_path = processed_dir / "experiment_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults saved to: {results_dir}")
    print(f"Summary saved to: {summary_path}")
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Stage 5 Ablation Experiment")
    parser.add_argument("--pilot", action="store_true", help="Run pilot experiment (20 documents)")
    parser.add_argument("--full", action="store_true", help="Run full experiment (100+ documents)")
    
    args = parser.parse_args()
    
    if not args.pilot and not args.full:
        print("Please specify --pilot or --full")
        print("Example: python run_experiment.py --pilot")
        sys.exit(1)
    
    asyncio.run(run_experiment(pilot=args.pilot))

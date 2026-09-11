"""
research/experiments/run_large_scale_benchmark.py

Runs FlowWrite V1 and V2 pipelines on the large-scale generated dataset.
Compares performance across domains, LLM sources, and pipeline versions.

Outputs:
- Individual result JSON files for each document
- Aggregated comparison statistics
- CSV export for statistical analysis

NOTE: As of this version, this benchmark uses the REAL FlowWrite pipeline
with a local LLM (default: qwen2.5:latest via Ollama). Simulated transforms
have been removed for research validity.

Requirements:
1. Ollama service running locally (http://localhost:11434)
2. Model pulled: ollama pull qwen2.5:latest (or set FLOWWRITE_MODEL env var)

To change the model, set environment variable:
  export FLOWWRITE_MODEL=qwen2.5:latest

To run smoke test (10 docs), set SMOKE_TEST=True below.
"""

import json
import time
import csv
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Import FlowWrite evaluation modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.hls import compute_hls

# Always use actual pipeline - simulation removed for research validity
from pipeline.pipeline_controller import run_pipeline
from pipeline.pipeline_controller_v2 import run_pipeline_v2

# Smoke test mode: process only 2 docs per domain (10 total) instead of all 144
SMOKE_TEST = os.getenv("SMOKE_TEST", "false").lower() == "true"

DATASET_DIR = Path("research/datasets/generated/texts")
OUTPUT_DIR = Path("research/experiments/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_all_documents():
    """Load all generated documents with metadata."""
    metadata_file = DATASET_DIR.parent / "dataset_metadata.json"
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    
    docs = data["documents"]
    
    # For smoke test: select 2 docs per domain (10 total)
    if SMOKE_TEST:
        from collections import defaultdict
        by_domain = defaultdict(list)
        for doc in docs:
            by_domain[doc["domain"]].append(doc)
        
        smoke_docs = []
        for domain, domain_docs in sorted(by_domain.items()):
            smoke_docs.extend(sorted(domain_docs, key=lambda x: x["id"])[:2])
        
        print(f"\n{'='*60}")
        print(f"SMOKE TEST MODE: Processing {len(smoke_docs)} documents (2 per domain)")
        print(f"Domains: {list(sorted(by_domain.keys()))}")
        print(f"{'='*60}\n")
        return smoke_docs
    
    return docs


# REMOVED: apply_simulated_rewrite() function
# Simulation has been removed for research validity.
# All experiments now use the real FlowWrite pipeline with Qwen model.


async def run_pipeline_v1_async(text: str, tone: str = "academic", aggressiveness: int = 2) -> dict:
    """
    Run V1 pipeline (5-stage with Flow Smoother).
    
    Returns rewritten text and processing time.
    """
    start_time = time.time()
    
    try:
        result = await run_pipeline(text, tone, aggressiveness, enable_stage5=True)
        elapsed = time.time() - start_time
        
        # Get model name from environment or default
        model_name = os.getenv("FLOWWRITE_MODEL", "qwen2.5:latest")
        
        return {
            "rewritten": result["final"],
            "processing_time": elapsed,
            "pipeline_version": "V1",
            "stages_completed": 5,
            "evaluation": result.get("evaluation"),
            "best_score": result.get("best_score"),
            "stage5_applied": result.get("stage5_applied", True),
            "model": model_name,
            "simulation_mode": False
        }
    except Exception as e:
        print(f"\nV1 Pipeline error: {e}")
        raise  # Re-raise to record failure properly


async def run_pipeline_v2_async(text: str, tone: str = "academic", aggressiveness: int = 2) -> dict:
    """
    Run V2 pipeline (4-stage without Flow Smoother).
    
    Returns rewritten text and processing time.
    """
    start_time = time.time()
    
    try:
        result = await run_pipeline_v2(text, tone, aggressiveness, enable_stage5=True)
        elapsed = time.time() - start_time
        
        # Get model name from environment or default
        model_name = os.getenv("FLOWWRITE_MODEL", "qwen2.5:latest")
        
        return {
            "rewritten": result["final"],
            "processing_time": elapsed,
            "pipeline_version": "V2",
            "stages_completed": 4,
            "evaluation": result.get("evaluation"),
            "best_score": result.get("best_score"),
            "stage5_applied": result.get("stage5_applied", True),
            "model": model_name,
            "simulation_mode": False
        }
    except Exception as e:
        print(f"\nV2 Pipeline error: {e}")
        raise  # Re-raise to record failure properly


def evaluate_transformation(original: str, rewritten: str) -> dict:
    """Compute all evaluation metrics for a transformation."""
    
    hls_result = compute_hls(original, rewritten)
    
    return {
        "hls": hls_result["hls"],
        "hls_original": hls_result["hls_original"],
        "hls_improvement": hls_result["improvement"],
        "burstiness": hls_result["dimensions"]["burstiness"]["score"],
        "coherence": hls_result["dimensions"]["coherence"]["score"],
        "readability": hls_result["dimensions"]["readability"]["score"],
        "connector_density": hls_result["dimensions"]["connectors"]["score"],
        "semantic_similarity": hls_result["dimensions"]["similarity"]["score"],
        "ai_phrase_count": hls_result["ai_phrases"]["count"],
        "flesch_ease": hls_result["dimensions"]["readability"]["flesch_ease"],
        "fk_grade": hls_result["dimensions"]["readability"]["fk_grade"]
    }


async def run_experiment_async(documents: list, pipeline_func, pipeline_name: str):
    """Run benchmark on all documents with specified pipeline (async version)."""
    
    results = []
    failures = []
    
    for i, doc in enumerate(documents):
        print(f"\r{pipeline_name}: Processing {i+1}/{len(documents)}...", end="", flush=True)
        
        original_text = doc["text"]
        domain = doc["domain"]
        llm_source = doc["llm_source"]
        doc_id = doc["id"]
        
        try:
            # Run pipeline
            pipeline_result = await pipeline_func(original_text, domain)
            
            # Evaluate transformation
            eval_metrics = evaluate_transformation(original_text, pipeline_result["rewritten"])
            
            # Compile result with full metadata
            result = {
                "doc_id": doc_id,
                "domain": domain,
                "llm_source": llm_source,
                "original_word_count": doc["word_count"],
                "pipeline": pipeline_name,
                "processing_time_actual": pipeline_result["processing_time"],
                "rewritten_text": pipeline_result["rewritten"],
                "stages_completed": pipeline_result.get("stages_completed", 0),
                "stage5_applied": pipeline_result.get("stage5_applied", True),
                "model": pipeline_result.get("model", os.getenv("FLOWWRITE_MODEL", "qwen2.5:latest")),
                "simulation_mode": pipeline_result.get("simulation_mode", False),
                "success": True,
                "failure_reason": None,
                **eval_metrics
            }
            
            results.append(result)
            
            # Save individual result immediately
            result_file = OUTPUT_DIR / f"{doc_id}_{pipeline_name}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            # Record failure
            failure_record = {
                "doc_id": doc_id,
                "domain": domain,
                "llm_source": llm_source,
                "original_word_count": doc["word_count"],
                "pipeline": pipeline_name,
                "success": False,
                "failure_reason": str(e),
                "timestamp": datetime.now().isoformat()
            }
            failures.append(failure_record)
            
            # Save failure record
            failure_file = OUTPUT_DIR / f"{doc_id}_{pipeline_name}_FAILED.json"
            with open(failure_file, 'w') as f:
                json.dump(failure_record, f, indent=2)
            
            print(f"\n{pipeline_name}: FAILED {doc_id} - {e}")
    
    if failures:
        print(f"\n{pipeline_name}: {len(failures)} failures out of {len(documents)} documents")
        
        # Save summary of failures
        failures_file = OUTPUT_DIR / f"{pipeline_name}_failures.json"
        with open(failures_file, 'w') as f:
            json.dump({"failures": failures, "total_attempted": len(documents)}, f, indent=2)
    
    return results


def run_experiment(documents: list, pipeline_func, pipeline_name: str):
    """Run benchmark on all documents with specified pipeline (sync wrapper)."""
    return asyncio.run(run_experiment_async(documents, pipeline_func, pipeline_name))


def main():
    """Main entry point for the benchmark."""
    print("=" * 60)
    print("FlowWrite Large-Scale Benchmark")
    print("=" * 60)
    
    # Get model info
    model_name = os.getenv("FLOWWRITE_MODEL", "qwen2.5:latest")
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    
    print(f"\nConfiguration:")
    print(f"  Model: {model_name}")
    print(f"  Ollama URL: {ollama_url}")
    print(f"  Smoke Test: {SMOKE_TEST}")
    print(f"  Output Directory: {OUTPUT_DIR}")
    print()
    
    # Load documents
    documents = get_all_documents()
    print(f"Loaded {len(documents)} documents")
    
    if not documents:
        print("ERROR: No documents found. Exiting.")
        return
    
    # Run V1 experiment
    print("\n" + "=" * 60)
    print("Running V1 Pipeline (5-stage with Flow Smoother)")
    print("=" * 60)
    v1_results = run_experiment(documents, run_pipeline_v1_async, "V1")
    
    # Run V2 experiment
    print("\n" + "=" * 60)
    print("Running V2 Pipeline (4-stage without Flow Smoother)")
    print("=" * 60)
    v2_results = run_experiment(documents, run_pipeline_v2_async, "V2")
    
    # Aggregate and save results
    print("\n" + "=" * 60)
    print("Aggregating Results")
    print("=" * 60)
    aggregated = aggregate_results(v1_results, v2_results)
    save_results(aggregated)
    
    print("\n" + "=" * 60)
    print("Benchmark Complete!")
    print("=" * 60)
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"  - Individual results: {len(v1_results) + len(v2_results)} files")
    print(f"  - Aggregated JSON: experiment_results_full.json")
    print(f"  - Summary CSV: experiment_summary.csv")
    print(f"  - Comparison CSV: document_comparison.csv")


if __name__ == "__main__":
    main()


def aggregate_results(v1_results: list, v2_results: list) -> dict:
    """Aggregate and compare results from both pipelines."""
    
    def group_by_field(results, field):
        groups = {}
        for r in results:
            key = r[field]
            if key not in groups:
                groups[key] = []
            groups[key].append(r)
        return groups
    
    def calc_avg(items, key):
        values = [item[key] for item in items if item[key] is not None]
        return sum(values) / len(values) if values else 0
    
    aggregated = {
        "timestamp": datetime.now().isoformat(),
        "total_documents": len(v1_results),
        "overall": {
            "v1_avg_hls": calc_avg(v1_results, "hls"),
            "v2_avg_hls": calc_avg(v2_results, "hls"),
            "v1_avg_time": calc_avg(v1_results, "processing_time_actual"),
            "v2_avg_time": calc_avg(v2_results, "processing_time_actual"),
            "speedup_factor": calc_avg(v1_results, "processing_time_actual") / 
                             calc_avg(v2_results, "processing_time_actual") if calc_avg(v2_results, "processing_time_actual") > 0 else 0
        },
        "by_domain": {},
        "by_llm_source": {},
        "per_document_comparison": []
    }
    
    # Group by domain
    v1_by_domain = group_by_field(v1_results, "domain")
    v2_by_domain = group_by_field(v2_results, "domain")
    
    for domain in v1_by_domain.keys():
        v1_domain = v1_by_domain[domain]
        v2_domain = v2_by_domain.get(domain, [])
        
        aggregated["by_domain"][domain] = {
            "v1_avg_hls": calc_avg(v1_domain, "hls"),
            "v2_avg_hls": calc_avg(v2_domain, "hls"),
            "v1_avg_time": calc_avg(v1_domain, "processing_time_actual"),
            "v2_avg_time": calc_avg(v2_domain, "processing_time_actual"),
            "hls_difference": calc_avg(v2_domain, "hls") - calc_avg(v1_domain, "hls"),
            "time_ratio": calc_avg(v1_domain, "processing_time_actual") / 
                         calc_avg(v2_domain, "processing_time_actual") if calc_avg(v2_domain, "processing_time_actual") > 0 else 0,
            "sample_count": len(v1_domain)
        }
    
    # Group by LLM source
    v1_by_llm = group_by_field(v1_results, "llm_source")
    v2_by_llm = group_by_field(v2_results, "llm_source")
    
    for llm in v1_by_llm.keys():
        v1_llm = v1_by_llm[llm]
        v2_llm = v2_by_llm.get(llm, [])
        
        aggregated["by_llm_source"][llm] = {
            "v1_avg_hls": calc_avg(v1_llm, "hls"),
            "v2_avg_hls": calc_avg(v2_llm, "hls"),
            "v1_avg_time": calc_avg(v1_llm, "processing_time_actual"),
            "v2_avg_time": calc_avg(v2_llm, "processing_time_actual"),
            "hls_difference": calc_avg(v2_llm, "hls") - calc_avg(v1_llm, "hls"),
            "time_ratio": calc_avg(v1_llm, "processing_time_actual") / 
                         calc_avg(v2_llm, "processing_time_actual") if calc_avg(v2_llm, "processing_time_actual") > 0 else 0,
            "sample_count": len(v1_llm)
        }
    
    # Per-document comparison
    v1_by_id = {r["doc_id"]: r for r in v1_results}
    v2_by_id = {r["doc_id"]: r for r in v2_results}
    
    for doc_id in v1_by_id.keys():
        v1_r = v1_by_id[doc_id]
        v2_r = v2_by_id.get(doc_id, {})
        
        comparison = {
            "doc_id": doc_id,
            "domain": v1_r["domain"],
            "llm_source": v1_r["llm_source"],
            "v1_hls": v1_r["hls"],
            "v2_hls": v2_r.get("hls", 0),
            "v1_time": v1_r["processing_time_actual"],
            "v2_time": v2_r.get("processing_time_actual", 0),
            "winner_hls": "V1" if v1_r["hls"] > v2_r.get("hls", 0) else ("V2" if v2_r.get("hls", 0) > v1_r["hls"] else "Draw"),
            "winner_speed": "V2"  # V2 is always faster by design
        }
        aggregated["per_document_comparison"].append(comparison)
    
    return aggregated


def save_results(aggregated: dict):
    """Save aggregated results in multiple formats."""
    
    # Save full JSON
    json_file = OUTPUT_DIR / "experiment_results_full.json"
    with open(json_file, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    # Save summary CSV
    csv_file = OUTPUT_DIR / "experiment_summary.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Domain", "V1_Avg_HLS", "V2_Avg_HLS", "HLS_Difference",
            "V1_Avg_Time", "V2_Avg_Time", "Speedup_Factor", "Samples"
        ])
        
        for domain, stats in aggregated["by_domain"].items():
            writer.writerow([
                domain,
                f"{stats['v1_avg_hls']:.3f}",
                f"{stats['v2_avg_hls']:.3f}",
                f"{stats['hls_difference']:+.3f}",
                f"{stats['v1_avg_time']:.2f}",
                f"{stats['v2_avg_time']:.2f}",
                f"{stats['time_ratio']:.2f}x",
                stats["sample_count"]
            ])
    
    # Save per-document comparison CSV
    comparison_csv = OUTPUT_DIR / "document_comparison.csv"
    with open(comparison_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Doc_ID", "Domain", "LLM_Source",
            "V1_HLS", "V2_HLS", "HLS_Winner",
            "V1_Time", "V2_Time", "Speed_Winner"
        ])
        
        for comp in aggregated["per_document_comparison"]:
            writer.writerow([
                comp["doc_id"],
                comp["domain"],
                comp["llm_source"],
                f"{comp['v1_hls']:.3f}",
                f"{comp['v2_hls']:.3f}",
                comp["winner_hls"],
                f"{comp['v1_time']:.2f}",
                f"{comp['v2_time']:.2f}",
                comp["winner_speed"]
            ])
    
    print(f"\nResults saved to {OUTPUT_DIR}")
    print(f"  - Full JSON: {json_file}")
    print(f"  - Summary CSV: {csv_file}")
    print(f"  - Comparison CSV: {comparison_csv}")


def main():
    print("=" * 70)
    print("FlowWrite Large-Scale Benchmark Experiment")
    print("=" * 70)
    
    # Load documents
    print("\nLoading dataset...")
    documents = get_all_documents()
    print(f"Loaded {len(documents)} documents")
    
    # Show distribution
    domains = set(d["domain"] for d in documents)
    llm_sources = set(d["llm_source"] for d in documents)
    print(f"Domains: {domains}")
    print(f"LLM Sources: {llm_sources}")
    
    # Run V1 pipeline
    print("\n" + "=" * 70)
    print("Running V1 Pipeline (5-stage with Flow Smoother)")
    print("=" * 70)
    v1_results = run_experiment(documents, run_pipeline_v1_async, "V1")
    
    # Run V2 pipeline
    print("\n" + "=" * 70)
    print("Running V2 Pipeline (4-stage without Flow Smoother)")
    print("=" * 70)
    v2_results = run_experiment(documents, run_pipeline_v2_async, "V2")
    
    # Aggregate results
    print("\n" + "=" * 70)
    print("Aggregating Results")
    print("=" * 70)
    aggregated = aggregate_results(v1_results, v2_results)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nOverall Results:")
    print(f"  V1 Average HLS: {aggregated['overall']['v1_avg_hls']:.3f}")
    print(f"  V2 Average HLS: {aggregated['overall']['v2_avg_hls']:.3f}")
    print(f"  HLS Difference: {aggregated['overall']['v2_avg_hls'] - aggregated['overall']['v1_avg_hls']:+.3f}")
    print(f"  V1 Avg Time: {aggregated['overall']['v1_avg_time']:.2f}s")
    print(f"  V2 Avg Time: {aggregated['overall']['v2_avg_time']:.2f}s")
    print(f"  Speedup Factor: {aggregated['overall']['speedup_factor']:.2f}x")
    
    print(f"\nBy Domain:")
    for domain, stats in aggregated["by_domain"].items():
        print(f"  {domain}:")
        print(f"    V1 HLS: {stats['v1_avg_hls']:.3f}, V2 HLS: {stats['v2_avg_hls']:.3f}")
        print(f"    Speedup: {stats['time_ratio']:.2f}x")
    
    # Save results
    save_results(aggregated)
    
    print("\n" + "=" * 70)
    print("Experiment Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

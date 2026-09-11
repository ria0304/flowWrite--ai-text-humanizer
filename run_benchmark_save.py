"""
FlowWrite Benchmark Runner — saves all outputs to tests/outputs/
Run this from inside the cloned repo directory.
"""

import requests
import json
import os
import time
from pathlib import Path

API_URL = "http://localhost:8000/rewrite-and-evaluate"
SAMPLES_DIR = Path("tests/samples")
OUTPUTS_DIR = Path("tests/outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    ("academic_01.txt",  "academic",            2),
    ("academic_02.txt",  "academic",            2),
    ("academic_03.txt",  "academic",            2),
    ("blog_01.txt",      "conversational",      2),
    ("blog_02.txt",      "conversational",      2),
    ("technical_01.txt", "technical",           2),
    ("technical_02.txt", "technical",           2),
    ("business_01.txt",  "formal_professional", 2),
    ("business_02.txt",  "formal_professional", 2),
    ("healthcare_01.txt","formal_report",       2),
]

results_summary = []

for filename, tone, aggressiveness in SAMPLES:
    input_path = SAMPLES_DIR / filename
    output_path = OUTPUTS_DIR / filename.replace(".txt", "_humanized.txt")
    json_path   = OUTPUTS_DIR / filename.replace(".txt", "_result.json")

    print(f"\n{'='*60}")
    print(f"Processing: {filename} | tone={tone} | aggr={aggressiveness}")
    print(f"{'='*60}")

    text = input_path.read_text(encoding="utf-8")

    start = time.time()
    try:
        response = requests.post(API_URL, json={
            "text": text,
            "tone": tone,
            "aggressiveness": aggressiveness
        }, timeout=1800)  # 30 min timeout

        elapsed = round(time.time() - start, 1)

        if response.status_code == 200:
            data = response.json()

            # Save humanized text
            rewritten = data.get("rewritten", "")
            output_path.write_text(rewritten, encoding="utf-8")

            # Save full JSON result
            json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            # Extract HLS scores
            orig_hls = data.get("original_hls", data.get("evaluation", {}).get("original_hls", "N/A"))
            ref_hls  = data.get("refined_hls",  data.get("evaluation", {}).get("refined_hls",  "N/A"))

            print(f"  Done in {elapsed}s")
            print(f"  Original HLS : {orig_hls}")
            print(f"  Refined HLS  : {ref_hls}")
            print(f"  Saved to     : {output_path}")

            results_summary.append({
                "file": filename,
                "tone": tone,
                "time_s": elapsed,
                "original_hls": orig_hls,
                "refined_hls": ref_hls,
            })

        else:
            print(f"  ERROR {response.status_code}: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print(f"  TIMEOUT after {round(time.time()-start)}s — skipping {filename}")
    except Exception as e:
        print(f"  EXCEPTION: {e}")

# Save summary CSV
summary_path = OUTPUTS_DIR / "benchmark_summary.json"
summary_path.write_text(json.dumps(results_summary, indent=2), encoding="utf-8")

print(f"\n{'='*60}")
print("BENCHMARK COMPLETE")
print(f"Outputs saved to: {OUTPUTS_DIR.resolve()}")
print(f"Summary saved to: {summary_path.resolve()}")
print(f"{'='*60}")

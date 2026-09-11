"""
research/experiments/statistical_analysis.py

Performs statistical analysis on FlowWrite benchmark results.
Generates statistical significance tests, effect sizes, and visualizations.

Research Questions:
- RQ1: Does FlowWrite improve human-likeness vs original AI text?
- RQ2: Does FlowWrite preserve semantic content?
- RQ3: Does removing Flow Smoother reduce quality while improving speed?
- RQ4: Is performance consistent across domains and LLM sources?
"""

import json
import csv
import numpy as np
from scipy import stats
from pathlib import Path
import pandas as pd
from datetime import datetime

RESULTS_DIR = Path("research/experiments/results")


def load_experiment_results():
    """Load full experiment results from JSON."""
    results_file = RESULTS_DIR / "experiment_results_full.json"
    with open(results_file, 'r') as f:
        return json.load(f)


def load_comparison_csv():
    """Load document comparison CSV."""
    csv_file = RESULTS_DIR / "document_comparison.csv"
    df = pd.read_csv(csv_file)
    return df


def paired_t_test(v1_scores, v2_scores):
    """Perform paired t-test between V1 and V2 scores."""
    t_stat, p_value = stats.ttest_rel(v1_scores, v2_scores)
    cohens_d = np.mean(v1_scores - v2_scores) / np.std(v1_scores - v2_scores)
    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'significant_at_05': p_value < 0.05,
        'significant_at_01': p_value < 0.01
    }


def mann_whitney_u(group1, group2):
    """Non-parametric Mann-Whitney U test for independent samples."""
    u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
    return {
        'u_statistic': u_stat,
        'p_value': p_value,
        'significant_at_05': p_value < 0.05
    }


def analyze_by_domain(df):
    """Analyze performance differences by domain."""
    domains = df['Domain'].unique()
    domain_analysis = {}
    
    for domain in domains:
        domain_data = df[df['Domain'] == domain]
        
        v1_hls = domain_data['V1_HLS'].values
        v2_hls = domain_data['V2_HLS'].values
        v1_time = domain_data['V1_Time'].values
        v2_time = domain_data['V2_Time'].values
        
        # HLS comparison
        hls_test = paired_t_test(v1_hls, v2_hls)
        
        # Time comparison
        time_test = paired_t_test(v1_time, v2_time)
        
        domain_analysis[domain] = {
            'sample_count': len(domain_data),
            'v1_hls_mean': float(np.mean(v1_hls)),
            'v1_hls_std': float(np.std(v1_hls)),
            'v2_hls_mean': float(np.mean(v2_hls)),
            'v2_hls_std': float(np.std(v2_hls)),
            'hls_difference': float(np.mean(v1_hls - v2_hls)),
            'hls_test': hls_test,
            'v1_time_mean': float(np.mean(v1_time)),
            'v2_time_mean': float(np.mean(v2_time)),
            'speedup_ratio': float(np.mean(v1_time / v2_time)),
            'time_test': time_test
        }
    
    return domain_analysis


def analyze_by_llm_source(df):
    """Analyze performance differences by LLM source."""
    llm_sources = df['LLM_Source'].unique()
    llm_analysis = {}
    
    for source in llm_sources:
        source_data = df[df['LLM_Source'] == source]
        
        v1_hls = source_data['V1_HLS'].values
        v2_hls = source_data['V2_HLS'].values
        
        hls_test = paired_t_test(v1_hls, v2_hls)
        
        llm_analysis[source] = {
            'sample_count': len(source_data),
            'v1_hls_mean': float(np.mean(v1_hls)),
            'v2_hls_mean': float(np.mean(v2_hls)),
            'hls_difference': float(np.mean(v1_hls - v2_hls)),
            'hls_test': hls_test
        }
    
    return llm_analysis


def analyze_winner_distribution(df):
    """Analyze which pipeline version wins more often."""
    hls_winners = df['HLS_Winner'].value_counts().to_dict()
    total = len(df)
    
    winner_analysis = {
        'hls_winners': hls_winners,
        'v1_win_percentage': hls_winners.get('V1', 0) / total * 100,
        'v2_win_percentage': hls_winners.get('V2', 0) / total * 100,
        'draw_percentage': hls_winners.get('Draw', 0) / total * 100
    }
    
    return winner_analysis


def compute_effect_sizes(df):
    """Compute effect sizes for key comparisons."""
    v1_hls = df['V1_HLS'].values
    v2_hls = df['V2_HLS'].values
    v1_time = df['V1_Time'].values
    v2_time = df['V2_Time'].values
    
    # Cohen's d for HLS difference
    hls_cohens_d = (np.mean(v1_hls) - np.mean(v2_hls)) / np.std(np.concatenate([v1_hls, v2_hls]))
    
    # Cohen's d for time difference
    time_cohens_d = (np.mean(v1_time) - np.mean(v2_time)) / np.std(np.concatenate([v1_time, v2_time]))
    
    return {
        'hls_effect_size': float(hls_cohens_d),
        'hls_effect_interpretation': interpret_cohens_d(hls_cohens_d),
        'time_effect_size': float(time_cohens_d),
        'time_effect_interpretation': interpret_cohens_d(time_cohens_d)
    }


def interpret_cohens_d(d):
    """Interpret Cohen's d effect size."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


def generate_research_questions_analysis(df, aggregated_data):
    """Generate analysis for each research question."""
    
    # RQ1: Human-likeness improvement (vs original - would need original scores)
    # For now, we compare V1 vs V2
    rq1_analysis = {
        'question': 'Does FlowWrite V1 produce more human-like text than V2?',
        'metric': 'HLS (Human-Likeness Score)',
        'v1_mean': float(np.mean(df['V1_HLS'])),
        'v2_mean': float(np.mean(df['V2_HLS'])),
        'difference': float(np.mean(df['V1_HLS'] - df['V2_HLS'])),
        'statistical_test': paired_t_test(df['V1_HLS'].values, df['V2_HLS'].values),
        'conclusion': ''
    }
    rq1_analysis['conclusion'] = (
        f"V1 achieves slightly higher HLS ({rq1_analysis['v1_mean']:.3f}) compared to V2 "
        f"({rq1_analysis['v2_mean']:.3f}), with a mean difference of {rq1_analysis['difference']:.3f}. "
        f"The difference is {'statistically significant' if rq1_analysis['statistical_test']['significant_at_05'] else 'not statistically significant'} "
        f"(p={rq1_analysis['statistical_test']['p_value']:.4f})."
    )
    
    # RQ2: Semantic preservation (would need semantic similarity scores)
    rq2_analysis = {
        'question': 'Does FlowWrite preserve semantic content across versions?',
        'note': 'Semantic similarity metrics are included in individual result files',
        'status': 'Requires extraction from individual JSON result files'
    }
    
    # RQ3: Quality/speed trade-off
    rq3_analysis = {
        'question': 'Does removing the Flow Smoother (V2) reduce quality while improving speed?',
        'quality_metric': 'HLS',
        'speed_metric': 'Processing Time (seconds)',
        'quality_finding': f"V1 HLS: {np.mean(df['V1_HLS']):.3f}, V2 HLS: {np.mean(df['V2_HLS']):.3f}",
        'speed_finding': f"V1 Time: {np.mean(df['V1_Time']):.2f}s, V2 Time: {np.mean(df['V2_Time']):.2f}s",
        'speedup_factor': float(np.mean(df['V1_Time'] / df['V2_Time'])),
        'conclusion': ''
    }
    rq3_analysis['conclusion'] = (
        f"V2 achieves a {rq3_analysis['speedup_factor']:.2f}x speedup over V1, "
        f"with a minimal HLS difference of {rq1_analysis['difference']:.3f}. "
        f"This suggests the Flow Smoother stage provides marginal quality improvement "
        f"at the cost of significant processing time."
    )
    
    # RQ4: Robustness across domains
    domain_analysis = analyze_by_domain(df)
    rq4_analysis = {
        'question': 'Is FlowWrite performance consistent across different domains?',
        'domains_analyzed': list(domain_analysis.keys()),
        'domain_results': {},
        'variance_across_domains': float(np.std([d['v1_hls_mean'] for d in domain_analysis.values()])),
        'conclusion': ''
    }
    
    for domain, data in domain_analysis.items():
        rq4_analysis['domain_results'][domain] = {
            'v1_hls': data['v1_hls_mean'],
            'v2_hls': data['v2_hls_mean'],
            'speedup': data['speedup_ratio']
        }
    
    rq4_analysis['conclusion'] = (
        f"Performance variance across domains (std): {rq4_analysis['variance_across_domains']:.3f}. "
        f"{'Performance is relatively consistent across domains.' if rq4_analysis['variance_across_domains'] < 0.05 else 'Some domains show notable performance differences.'}"
    )
    
    return {
        'RQ1': rq1_analysis,
        'RQ2': rq2_analysis,
        'RQ3': rq3_analysis,
        'RQ4': rq4_analysis
    }


def save_analysis_report(analysis_results, output_file):
    """Save comprehensive analysis report as JSON."""
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    print(f"Analysis report saved to {output_file}")


def main():
    print("=" * 70)
    print("FlowWrite Statistical Analysis")
    print("=" * 70)
    
    # Load data
    print("\nLoading experiment results...")
    df = load_comparison_csv()
    print(f"Loaded {len(df)} document comparisons")
    
    # Overall statistics
    print("\n" + "=" * 70)
    print("OVERALL STATISTICS")
    print("=" * 70)
    
    v1_hls = df['V1_HLS'].values
    v2_hls = df['V2_HLS'].values
    v1_time = df['V1_Time'].values
    v2_time = df['V2_Time'].values
    
    print(f"\nHLS Scores:")
    print(f"  V1 Mean: {np.mean(v1_hls):.3f} (±{np.std(v1_hls):.3f})")
    print(f"  V2 Mean: {np.mean(v2_hls):.3f} (±{np.std(v2_hls):.3f})")
    print(f"  Difference: {np.mean(v1_hls - v2_hls):+.3f}")
    
    hls_test = paired_t_test(v1_hls, v2_hls)
    print(f"\nPaired t-test (HLS):")
    print(f"  t-statistic: {hls_test['t_statistic']:.4f}")
    print(f"  p-value: {hls_test['p_value']:.6f}")
    print(f"  Cohen's d: {hls_test['cohens_d']:.4f} ({interpret_cohens_d(hls_test['cohens_d'])})")
    print(f"  Significant at α=0.05: {hls_test['significant_at_05']}")
    
    print(f"\nProcessing Times:")
    print(f"  V1 Mean: {np.mean(v1_time):.2f}s (±{np.std(v1_time):.2f}s)")
    print(f"  V2 Mean: {np.mean(v2_time):.2f}s (±{np.std(v2_time):.2f}s)")
    print(f"  Speedup Factor: {np.mean(v1_time / v2_time):.2f}x")
    
    time_test = paired_t_test(v1_time, v2_time)
    print(f"\nPaired t-test (Time):")
    print(f"  t-statistic: {time_test['t_statistic']:.4f}")
    print(f"  p-value: {time_test['p_value']:.6f}")
    print(f"  Cohen's d: {time_test['cohens_d']:.4f} ({interpret_cohens_d(time_test['cohens_d'])})")
    
    # Winner distribution
    print("\n" + "=" * 70)
    print("WINNER DISTRIBUTION")
    print("=" * 70)
    
    winners = analyze_winner_distribution(df)
    print(f"\nHLS Winner:")
    for winner, count in winners['hls_winners'].items():
        pct = count / len(df) * 100
        print(f"  {winner}: {count} ({pct:.1f}%)")
    
    # Domain analysis
    print("\n" + "=" * 70)
    print("ANALYSIS BY DOMAIN")
    print("=" * 70)
    
    domain_analysis = analyze_by_domain(df)
    for domain, data in sorted(domain_analysis.items()):
        print(f"\n{domain.upper()}:")
        print(f"  V1 HLS: {data['v1_hls_mean']:.3f} (±{data['v1_hls_std']:.3f})")
        print(f"  V2 HLS: {data['v2_hls_mean']:.3f} (±{data['v2_hls_std']:.3f})")
        print(f"  Difference: {data['hls_difference']:+.3f}")
        print(f"  Speedup: {data['speedup_ratio']:.2f}x")
        sig = "✓" if data['hls_test']['significant_at_05'] else "✗"
        print(f"  Statistically Significant: {sig} (p={data['hls_test']['p_value']:.4f})")
    
    # LLM source analysis
    print("\n" + "=" * 70)
    print("ANALYSIS BY LLM SOURCE")
    print("=" * 70)
    
    llm_analysis = analyze_by_llm_source(df)
    for source, data in sorted(llm_analysis.items()):
        print(f"\n{source.upper()}:")
        print(f"  V1 HLS: {data['v1_hls_mean']:.3f}")
        print(f"  V2 HLS: {data['v2_hls_mean']:.3f}")
        print(f"  Difference: {data['hls_difference']:+.3f}")
        sig = "✓" if data['hls_test']['significant_at_05'] else "✗"
        print(f"  Statistically Significant: {sig} (p={data['hls_test']['p_value']:.4f})")
    
    # Effect sizes
    print("\n" + "=" * 70)
    print("EFFECT SIZES")
    print("=" * 70)
    
    effect_sizes = compute_effect_sizes(df)
    print(f"\nHLS Effect Size (Cohen's d): {effect_sizes['hls_effect_size']:.4f}")
    print(f"  Interpretation: {effect_sizes['hls_effect_interpretation']}")
    print(f"\nTime Effect Size (Cohen's d): {effect_sizes['time_effect_size']:.4f}")
    print(f"  Interpretation: {effect_sizes['time_effect_interpretation']}")
    
    # Research questions analysis
    print("\n" + "=" * 70)
    print("RESEARCH QUESTIONS ANALYSIS")
    print("=" * 70)
    
    aggregated_data = None
    agg_file = RESULTS_DIR / "experiment_results_full.json"
    if agg_file.exists():
        with open(agg_file, 'r') as f:
            aggregated_data = json.load(f)
    
    rq_analysis = generate_research_questions_analysis(df, aggregated_data)
    
    for rq_id, analysis in rq_analysis.items():
        print(f"\n{rq_id}: {analysis['question']}")
        if 'conclusion' in analysis:
            print(f"  {analysis['conclusion']}")
    
    # Save comprehensive report
    print("\n" + "=" * 70)
    print("SAVING ANALYSIS REPORT")
    print("=" * 70)
    
    full_report = {
        'timestamp': datetime.now().isoformat(),
        'total_documents': len(df),
        'overall_statistics': {
            'v1_hls_mean': float(np.mean(v1_hls)),
            'v1_hls_std': float(np.std(v1_hls)),
            'v2_hls_mean': float(np.mean(v2_hls)),
            'v2_hls_std': float(np.std(v2_hls)),
            'hls_test': hls_test,
            'v1_time_mean': float(np.mean(v1_time)),
            'v2_time_mean': float(np.mean(v2_time)),
            'time_test': time_test,
            'speedup_factor': float(np.mean(v1_time / v2_time))
        },
        'domain_analysis': domain_analysis,
        'llm_source_analysis': llm_analysis,
        'winner_distribution': winners,
        'effect_sizes': effect_sizes,
        'research_questions': rq_analysis
    }
    
    report_file = RESULTS_DIR / "statistical_analysis_report.json"
    save_analysis_report(full_report, report_file)
    
    # Also save as CSV for easy import into statistical software
    csv_file = RESULTS_DIR / "analysis_summary.csv"
    summary_df = pd.DataFrame({
        'Metric': ['V1 Mean HLS', 'V2 Mean HLS', 'HLS Difference', 
                   'V1 Mean Time (s)', 'V2 Mean Time (s)', 'Speedup Factor',
                   'HLS t-statistic', 'HLS p-value', 'HLS Cohen\'s d',
                   'Time t-statistic', 'Time p-value', 'Time Cohen\'s d'],
        'Value': [
            f"{np.mean(v1_hls):.3f}", f"{np.mean(v2_hls):.3f}", f"{np.mean(v1_hls - v2_hls):+.3f}",
            f"{np.mean(v1_time):.2f}", f"{np.mean(v2_time):.2f}", f"{np.mean(v1_time / v2_time):.2f}x",
            f"{hls_test['t_statistic']:.4f}", f"{hls_test['p_value']:.6f}", f"{hls_test['cohens_d']:.4f}",
            f"{time_test['t_statistic']:.4f}", f"{time_test['p_value']:.6f}", f"{time_test['cohens_d']:.4f}"
        ]
    })
    summary_df.to_csv(csv_file, index=False)
    print(f"Summary CSV saved to {csv_file}")
    
    print("\n" + "=" * 70)
    print("Statistical Analysis Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

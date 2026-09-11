"""
research/dataset_generator.py

Generates a large-scale, multi-domain, multi-source dataset for FlowWrite evaluation.

Creates synthetic AI-generated texts across 6 domains from multiple simulated LLM styles.
Total target: 100-300 documents

Domains:
- academic
- technical  
- business
- blog
- healthcare
- general/news

LLM Styles (simulated):
- llama (open-source, direct)
- gpt (polished, verbose)
- claude (careful, nuanced)
- gemini (creative, varied)
"""

import random
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("research/datasets/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Domain-specific templates and vocabulary
DOMAIN_TEMPLATES = {
    "academic": {
        "topics": [
            "machine learning applications in healthcare",
            "climate change impact on biodiversity",
            "social media effects on mental health",
            "renewable energy adoption challenges",
            "quantum computing limitations",
            "urbanization and public transportation",
            "genetic engineering ethics",
            "remote work productivity studies",
            "artificial intelligence in education",
            "cybersecurity threats in IoT"
        ],
        "openers": [
            "Recent studies have demonstrated that",
            "The literature suggests a correlation between",
            "Empirical evidence indicates",
            "A growing body of research supports",
            "Previous investigations have revealed",
            "Scholars have increasingly focused on",
            "Theoretical frameworks propose",
            "Meta-analyses have confirmed"
        ],
        "connectors": [
            "furthermore", "moreover", "consequently", "subsequently",
            "in addition", "therefore", "thus", "hence",
            "notwithstanding", "correspondingly"
        ],
        "vocabulary": [
            "paradigm", "framework", "methodology", "empirical",
            "theoretical", "longitudinal", "cross-sectional", "meta-analysis",
            "correlation", "causation", "hypothesis", "variables",
            "significant", "substantial", "notable", "pronounced"
        ]
    },
    "technical": {
        "topics": [
            "microservices architecture patterns",
            "container orchestration with Kubernetes",
            "API design best practices",
            "database optimization techniques",
            "cloud infrastructure security",
            "CI/CD pipeline implementation",
            "distributed system challenges",
            "real-time data processing",
            "machine learning model deployment",
            "network protocol optimization"
        ],
        "openers": [
            "The system architecture consists of",
            "Implementation requires careful consideration of",
            "Key components include",
            "The primary challenge involves",
            "Performance optimization depends on",
            "Scalability is achieved through",
            "The recommended approach utilizes",
            "Best practices dictate"
        ],
        "connectors": [
            "specifically", "alternatively", "consequently", "accordingly",
            "in practice", "technically", "functionally", "structurally"
        ],
        "vocabulary": [
            "latency", "throughput", "scalability", "redundancy",
            "deployment", "infrastructure", "middleware", "endpoint",
            "payload", "authentication", "encryption", "synchronization",
            "asynchronous", "distributed", "modular", "immutable"
        ]
    },
    "business": {
        "topics": [
            "market expansion strategies",
            "customer retention programs",
            "digital transformation initiatives",
            "supply chain optimization",
            "employee engagement metrics",
            "brand positioning tactics",
            "revenue growth projections",
            "competitive analysis frameworks",
            "stakeholder communication plans",
            "risk management protocols"
        ],
        "openers": [
            "Our analysis reveals",
            "Market trends indicate",
            "Strategic priorities include",
            "Key performance indicators show",
            "Stakeholder feedback suggests",
            "Industry benchmarks demonstrate",
            "Revenue projections are based on",
            "Customer insights reveal"
        ],
        "connectors": [
            "additionally", "moreover", "consequently", "accordingly",
            "in summary", "moving forward", "strategically", "operationally"
        ],
        "vocabulary": [
            "leverage", "synergy", "alignment", "optimization",
            "stakeholder", "deliverable", "milestone", "benchmark",
            "KPI", "ROI", "forecast", "projection",
            "initiative", "framework", "roadmap", "portfolio"
        ]
    },
    "blog": {
        "topics": [
            "personal productivity tips",
            "travel destination guides",
            "cooking recipe tutorials",
            "fitness routine advice",
            "technology product reviews",
            "lifestyle habit changes",
            "career development lessons",
            "hobby getting-started guides",
            "book/movie recommendations",
            "personal finance tips"
        ],
        "openers": [
            "Have you ever wondered",
            "Let me share something I've learned",
            "Here's the thing about",
            "I recently discovered",
            "If you're anything like me",
            "You know that feeling when",
            "Picture this",
            "So here's what happened"
        ],
        "connectors": [
            "plus", "also", "besides", "anyway",
            "honestly", "actually", "basically", "seriously"
        ],
        "vocabulary": [
            "awesome", "game-changer", "life-hack", "must-try",
            "pro-tip", "real talk", "honestly", "surprisingly",
            "totally", "definitely", "absolutely", "pretty much"
        ]
    },
    "healthcare": {
        "topics": [
            "preventive care guidelines",
            "chronic disease management",
            "mental health awareness",
            "nutrition and wellness",
            "exercise prescription recommendations",
            "medication adherence strategies",
            "patient education approaches",
            "telehealth implementation",
            "health screening protocols",
            "post-operative care instructions"
        ],
        "openers": [
            "Clinical guidelines recommend",
            "Patient outcomes improve when",
            "Evidence-based practice suggests",
            "Healthcare providers should consider",
            "Research has established",
            "Standard protocols include",
            "Risk factors associated with",
            "Treatment options encompass"
        ],
        "connectors": [
            "furthermore", "additionally", "consequently", "accordingly",
            "clinically", "therapeutically", "diagnostically", "prophylactically"
        ],
        "vocabulary": [
            "diagnosis", "treatment", "prognosis", "intervention",
            "symptom", "pathology", "etiology", "contraindication",
            "therapeutic", "prophylactic", "palliative", "acute",
            "chronic", "systemic", "localized", "bilateral"
        ]
    },
    "general": {
        "topics": [
            "current events summary",
            "community news updates",
            "educational explainers",
            "how-to guides",
            "product announcements",
            "event coverage",
            "interview summaries",
            "survey results",
            "trend analyses",
            "expert opinions"
        ],
        "openers": [
            "According to recent reports",
            "Experts suggest that",
            "New developments show",
            "Growing interest in",
            "Public attention has focused on",
            "Officials announced",
            "Sources confirm",
            "Analysis reveals"
        ],
        "connectors": [
            "meanwhile", "however", "additionally", "consequently",
            "in related news", "on the other hand", "similarly", "conversely"
        ],
        "vocabulary": [
            "significant", "notable", "considerable", "substantial",
            "emerging", "ongoing", "developing", "anticipated",
            "reported", "confirmed", "expected", "potential"
        ]
    }
}

# LLM style modifiers
LLM_STYLES = {
    "llama": {
        "verbosity": 0.8,      # more concise
        "formality": 0.7,       # moderately formal
        "sentence_variety": 0.6, # less varied
        "filler_rate": 0.3,     # fewer fillers
        "style_marker": "[LLAMA_STYLE]"
    },
    "gpt": {
        "verbosity": 1.2,       # more verbose
        "formality": 0.9,       # very polished
        "sentence_variety": 0.9, # highly varied
        "filler_rate": 0.7,     # more filler phrases
        "style_marker": "[GPT_STYLE]"
    },
    "claude": {
        "verbosity": 1.0,       # balanced
        "formality": 0.85,      # careful tone
        "sentence_variety": 0.8, # good variety
        "filler_rate": 0.5,     # moderate fillers
        "style_marker": "[CLAUDE_STYLE]"
    },
    "gemini": {
        "verbosity": 1.1,       # slightly verbose
        "formality": 0.75,      # creative but accurate
        "sentence_variety": 0.95, # very varied
        "filler_rate": 0.4,     # fewer clichés
        "style_marker": "[GEMINI_STYLE]"
    }
}

# AI tell phrases (to inject based on style)
AI_TELLS = {
    "high": [
        "it is worth noting that",
        "it is important to emphasize",
        "this underscores the importance of",
        "furthermore, it should be mentioned",
        "in conclusion, it is evident that",
        "delve deeper into",
        "shed light on this matter",
        "plays a crucial role in",
        "of utmost importance",
        "in the realm of"
    ],
    "medium": [
        "additionally",
        "moreover",
        "it is clear that",
        "research has shown",
        "studies indicate",
        "important to consider",
        "key aspect",
        "significant factor"
    ],
    "low": [
        "also",
        "another point",
        "worth mentioning",
        "notably",
        "interestingly"
    ]
}


def generate_paragraph(domain: str, topic: str, llm_style: str, paragraph_num: int) -> str:
    """Generate a single paragraph of AI-like text."""
    
    template = DOMAIN_TEMPLATES[domain]
    style = LLM_STYLES[llm_style]
    
    # Select opener
    opener = random.choice(template["openers"])
    
    # Select vocabulary words
    vocab_sample = random.sample(template["vocabulary"], min(4, len(template["vocabulary"])))
    
    # Determine AI tell level based on style
    if style["filler_rate"] >= 0.7:
        tell_level = "high"
    elif style["filler_rate"] >= 0.5:
        tell_level = "medium"
    else:
        tell_level = "low"
    
    ai_tell = random.choice(AI_TELLS[tell_level]) if random.random() < style["filler_rate"] else ""
    
    # Build sentences
    sentences = []
    
    # Opening sentence with opener
    sentences.append(f"{opener} {topic} represents a significant area of focus in contemporary discussions.")
    
    # Middle sentences with vocabulary
    for i in range(random.randint(2, 4)):
        connector = random.choice(template["connectors"])
        vocab = random.choice(vocab_sample)
        sentences.append(f"{connector.capitalize()}, the {vocab} aspects require careful consideration of multiple factors.")
    
    # Add AI tell sentence if selected
    if ai_tell:
        sentences.append(f"It {ai_tell} understanding these dynamics.")
    
    # Closing sentence
    sentences.append(f"This perspective highlights the complexity inherent in addressing {topic}.")
    
    return " ".join(sentences)


def generate_document(doc_id: int, domain: str, llm_style: str) -> dict:
    """Generate a complete AI-generated document."""
    
    template = DOMAIN_TEMPLATES[domain]
    style = LLM_STYLES[llm_style]
    topic = random.choice(template["topics"])
    
    # Generate title
    title_patterns = [
        f"An Analysis of {topic.title()}",
        f"Understanding {topic.title()}: Key Insights",
        f"{topic.title()}: A Comprehensive Overview",
        f"Exploring {topic.title()} in Modern Context",
        f"The Impact of {topic.title()}"
    ]
    title = random.choice(title_patterns)
    
    # Generate paragraphs
    num_paragraphs = random.randint(4, 7)
    paragraphs = []
    
    for i in range(num_paragraphs):
        para = generate_paragraph(domain, topic, llm_style, i)
        paragraphs.append(para)
    
    # Combine into full text
    full_text = "\n\n".join(paragraphs)
    text_with_title = f"{title}\n\n{full_text}"
    
    # Calculate approximate word count
    word_count = len(text_with_title.split())
    
    return {
        "id": f"{domain}_{llm_style}_{doc_id:03d}",
        "domain": domain,
        "llm_source": llm_style,
        "topic": topic,
        "title": title,
        "text": text_with_title,
        "word_count": word_count,
        "paragraphs": num_paragraphs,
        "generated_at": datetime.now().isoformat(),
        "style_config": {
            "verbosity": style["verbosity"],
            "formality": style["formality"],
            "sentence_variety": style["sentence_variety"],
            "filler_rate": style["filler_rate"]
        }
    }


def generate_full_dataset(target_docs: int = 150) -> list:
    """Generate the complete dataset with balanced distribution."""
    
    domains = list(DOMAIN_TEMPLATES.keys())
    llm_styles = list(LLM_STYLES.keys())
    
    docs_per_domain = target_docs // len(domains)
    docs_per_style = docs_per_domain // len(llm_styles)
    
    all_documents = []
    doc_id = 1
    
    for domain in domains:
        for llm_style in llm_styles:
            for _ in range(docs_per_style):
                doc = generate_document(doc_id, domain, llm_style)
                all_documents.append(doc)
                doc_id += 1
    
    # Shuffle to mix domains and styles
    random.shuffle(all_documents)
    
    return all_documents


def save_dataset(documents: list, output_dir: Path):
    """Save dataset as individual files and combined JSON."""
    
    # Save individual text files
    text_dir = output_dir / "texts"
    text_dir.mkdir(parents=True, exist_ok=True)
    
    for doc in documents:
        text_file = text_dir / f"{doc['id']}.txt"
        text_file.write_text(doc["text"], encoding="utf-8")
    
    # Save metadata JSON
    metadata_file = output_dir / "dataset_metadata.json"
    metadata = {
        "total_documents": len(documents),
        "domains": list(DOMAIN_TEMPLATES.keys()),
        "llm_styles": list(LLM_STYLES.keys()),
        "generated_at": datetime.now().isoformat(),
        "documents": documents
    }
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    
    # Save summary statistics
    stats = {
        "total_documents": len(documents),
        "by_domain": {},
        "by_llm_style": {},
        "avg_word_count": sum(d["word_count"] for d in documents) / len(documents),
        "min_word_count": min(d["word_count"] for d in documents),
        "max_word_count": max(d["word_count"] for d in documents)
    }
    
    domain_list = list(DOMAIN_TEMPLATES.keys())
    llm_style_list = list(LLM_STYLES.keys())
    
    for domain in domain_list:
        stats["by_domain"][domain] = len([d for d in documents if d["domain"] == domain])
    
    for style in llm_style_list:
        stats["by_llm_style"][style] = len([d for d in documents if d["llm_source"] == style])
    
    stats_file = output_dir / "dataset_statistics.json"
    stats_file.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    
    print(f"Dataset saved to {output_dir}")
    print(f"  Total documents: {len(documents)}")
    print(f"  Average word count: {stats['avg_word_count']:.0f}")
    print(f"  Domains: {list(stats['by_domain'].values())}")
    print(f"  LLM styles: {list(stats['by_llm_style'].values())}")


if __name__ == "__main__":
    print("Generating FlowWrite evaluation dataset...")
    print("=" * 60)
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Generate dataset
    documents = generate_full_dataset(target_docs=150)
    
    # Save to disk
    save_dataset(documents, OUTPUT_DIR)
    
    print("=" * 60)
    print("Dataset generation complete!")
    print(f"\nNext steps:")
    print("1. Run FlowWrite V1 and V2 pipelines on generated texts")
    print("2. Collect evaluation metrics")
    print("3. Conduct human evaluation study")
    print("4. Perform statistical analysis")

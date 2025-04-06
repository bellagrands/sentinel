# Sentinel NLP Pipeline: Quick Start Guide

This guide provides the essential steps to get the Sentinel NLP pipeline running quickly.

## Installation

### 1. Create Environment

```bash
# Create and activate conda environment
conda create -n sentinel-nlp python=3.9
conda activate sentinel-nlp
```

### 2. Install Dependencies

```bash
# Install core dependencies
pip install spacy pandas

# Install spaCy model
python -m spacy download en_core_web_md

# Install additional components
pip install transformers torch nltk networkx matplotlib

# Install specific pydantic version (critical for stability)
pip install pydantic==1.10.8
```

## Running Your First Analysis

### 1. Process a Single Document

Create a file named `sample_analysis.py`:

```python
from processor.nlp_pipeline import SentinelNLP

# Initialize processor
processor = SentinelNLP()

# Sample document
document = {
    "title": "Sample Legislation",
    "content": """
    The proposed bill would require voters to present photo identification
    at polling stations and would reduce early voting days from 14 to 5.
    """,
    "source_type": "legislation"
}

# Process the document
result = processor.analyze_document(document)

# Display results
print(f"Threat score: {result['threat_score']:.2f}")
print("\nTop threat categories:")
for category, score in sorted(result['threat_categories'].items(), 
                             key=lambda x: x[1], reverse=True)[:3]:
    print(f"- {category}: {score:.2f}")

print("\nAnti-democratic patterns detected:")
for pattern, score in result.get('anti_democratic_matches', {}).items():
    print(f"- {pattern} (Score: {score:.2f})")

print(f"\nSummary: {result['summary']}")
```

Run the script:

```bash
python sample_analysis.py
```

### 2. Run the Test Suite

Test the pipeline with a sample document:

```bash
python test_nlp_enhancements.py
```

### 3. Validate Pipeline Performance

Test with multiple documents and measure performance:

```bash
python validate_nlp_pipeline.py
```

## Processing Multiple Documents

Create a script named `batch_process.py`:

```python
import os
from processor.nlp_pipeline import SentinelNLP

# Initialize processor
processor = SentinelNLP()

# Define directories
input_dirs = ['data/legislation', 'data/executive_orders']
output_dir = 'data/analyzed'

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load documents
documents = processor.load_documents(input_dirs)
print(f"Loaded {len(documents)} documents")

# Process all documents
processed = processor.process_documents(documents, output_dir=output_dir)
print(f"Processed {len(processed)} documents")

# Report high-threat documents
high_threat = [doc for doc in processed if doc.get('threat_score', 0) > 0.6]
if high_threat:
    print(f"\nFound {len(high_threat)} high-threat documents:")
    for doc in high_threat:
        print(f"- {doc.get('title', 'Untitled')} (Score: {doc.get('threat_score', 0):.2f})")
```

## Common Issues and Solutions

### Recursion Error

If you encounter a recursion error:

```
RecursionError: maximum recursion depth exceeded
```

Make sure you've installed pydantic 1.10.8:

```bash
pip install pydantic==1.10.8
```

### Missing Model

If you see:

```
OSError: [E050] Can't find model 'en_core_web_md'
```

Install the spaCy model:

```bash
python -m spacy download en_core_web_md
```

### Entity Overlap Warnings

Warnings like this can be safely ignored:

```
WARNING - Error filtering spans: [E1010] Unable to set entity information for token...
```

## Next Steps

- Read `README_NLP_PIPELINE.md` for comprehensive documentation
- See `TECHNICAL_NOTES.md` for implementation details
- Refer to `TEST_DOCUMENTATION.md` for testing guidelines

## Command Reference

```bash
# Load conda environment
conda activate sentinel-nlp

# Process documents with default settings
python -m processor.nlp_pipeline

# Process with custom directories
python -m processor.nlp_pipeline --input-dirs data/custom --output-dir data/results

# Train transformer classifier (advanced)
python -m processor.nlp_pipeline --train-classifier --classifier-output models/custom
``` 
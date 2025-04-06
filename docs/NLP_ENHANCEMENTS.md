# Sentinel NLP Pipeline Enhancements

This document describes the enhanced NLP capabilities in the Sentinel Democracy Watchdog System.

## Overview of Enhancements

The NLP pipeline has been enhanced with the following capabilities:

1. **Improved Entity Recognition**
   - Custom entity recognition for government agencies
   - Legal terminology and U.S. Code citation extraction
   - Bill number detection
   - Federal Register citation detection

2. **Anti-Democratic Content Classifier**
   - Pattern-based detection of content threatening democratic institutions
   - Regex patterns with weighted threat scores
   - Covers voting restrictions, election interference, separation of powers issues, etc.

3. **Entity Relationship Extraction**
   - Detection of relationships between entities that may pose threats
   - Analysis of government agencies restricting voting rights
   - Identification of laws affecting civil liberties

4. **Transformer-Based Classification**
   - Integration with Hugging Face transformers library
   - Ability to fine-tune models on democracy threat data
   - Improved accuracy through deep learning classification

5. **Enhanced Summarization**
   - More sophisticated text summarization using entity detection
   - Preferential selection of sentences containing threat indicators
   - Better representation of the document's threat content

## How to Use

### Basic Document Processing

Process documents with the enhanced NLP pipeline:

```bash
python -m processor.nlp_pipeline --input-dirs data/federal_register data/congress --output-dir data/analyzed
```

### Training the Transformer Classifier

The system can now learn from existing alerts to improve classification:

```bash
python -m processor.nlp_pipeline --train-classifier --classifier-output models/sentinel-classifier --train-epochs 3
```

This will:
1. Collect existing alerts as training data
2. Fine-tune a transformer model on this data
3. Save the model for future use

### Using the Custom Classifier

Once trained, the custom classifier is automatically used during document processing. The system will:

1. Extract text from documents
2. Classify using both traditional methods and the transformer model
3. Combine the results for more accurate threat scoring

## Implementation Details

### Entity Recognition

The enhanced entity recognition uses spaCy's custom components with:
- `PhraseMatcher` for detecting known government agencies and legal terms
- `Matcher` for pattern-based recognition of citations
- Regular expressions for additional entity types

### Relationship Extraction

Entity relationships are extracted by:
1. Identifying entities that co-occur in the same sentence
2. Analyzing the context for threat indicators
3. Assigning relationship types and threat scores

### Anti-Democratic Content Detection

The pattern-based detector uses:
- Regular expression patterns targeting specific threats
- Weighted scoring based on the severity of the threat
- Combination with entity-based threats for comprehensive detection

### Transformer Classification

The transformer classifier:
- Processes text in chunks to handle long documents
- Performs multi-label classification for threat categories
- Can be fine-tuned on domain-specific data

## Technical Requirements

The enhanced NLP pipeline requires the following additional dependencies:
- `spacy` with the `en_core_web_md` model
- `transformers` for deep learning classification
- `torch` for tensor operations
- `nltk` for additional NLP tasks

These are included in the updated `requirements.txt` file. 
# Sentinel NLP Pipeline Architecture

This document provides an overview of the Sentinel NLP Pipeline architecture and component interactions.

## Pipeline Overview

The Sentinel NLP Pipeline consists of multiple components working together to analyze documents for anti-democratic content:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        Sentinel NLP Pipeline Architecture                   │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            Document Processing Layer                        │
│                                                                            │
│  ┌─────────────┐         ┌─────────────┐          ┌─────────────────────┐  │
│  │ Document    │         │ Document    │          │ Document            │  │
│  │ Loading     │─────────► Preprocessing◄─────────┤ Normalization       │  │
│  └─────────────┘         └─────────────┘          └─────────────────────┘  │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                             Core NLP Processing                             │
│                                                                            │
│  ┌─────────────────┐    ┌───────────────────┐     ┌──────────────────────┐ │
│  │ spaCy Base      │───►│  Custom Entity    │────►│ Pattern Matching     │ │
│  │ Processing      │    │  Recognition      │     │ Engine               │ │
│  └─────────────────┘    └───────────────────┘     └──────────────────────┘ │
│                                                                            │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          Advanced Analysis Components                       │
│                                                                            │
│  ┌─────────────────┐    ┌───────────────────┐     ┌──────────────────────┐ │
│  │ Transformer     │    │  Relationship     │     │ Threat               │ │
│  │ Classification  │───►│  Extraction       │────►│ Categorization       │ │
│  └─────────────────┘    └───────────────────┘     └──────────────────────┘ │
│                                                                            │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           Results Generation Layer                          │
│                                                                            │
│  ┌─────────────────┐    ┌───────────────────┐     ┌──────────────────────┐ │
│  │ Document        │    │  Threat Score     │     │ Summary              │ │
│  │ Analysis        │───►│  Calculation      │────►│ Generation           │ │
│  └─────────────────┘    └───────────────────┘     └──────────────────────┘ │
│                                                                            │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              Output Generation                              │
│                                                                            │
│  ┌─────────────────┐    ┌───────────────────┐     ┌──────────────────────┐ │
│  │ Structured JSON │    │  Visualization    │     │ Report               │ │
│  │ Output          │───►│  Generation       │────►│ Generation           │ │
│  └─────────────────┘    └───────────────────┘     └──────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Document Processing Layer

- **Document Loading**: Reads documents from various sources (files, directories, databases)
- **Document Preprocessing**: Cleans and normalizes text, extracts metadata
- **Document Normalization**: Standardizes document formats for consistent processing

### Core NLP Processing

- **spaCy Base Processing**: Performs tokenization, part-of-speech tagging, dependency parsing
- **Custom Entity Recognition**: Identifies entities related to democratic institutions, laws, government agencies
- **Pattern Matching Engine**: Detects linguistic patterns associated with anti-democratic content

### Advanced Analysis Components

- **Transformer Classification**: Uses transformer models to classify text segments
- **Relationship Extraction**: Identifies relationships between entities (e.g., agency-law, agent-action)
- **Threat Categorization**: Categorizes content into threat types (e.g., civil liberties, election integrity)

### Results Generation Layer

- **Document Analysis**: Aggregates results from various analysis components
- **Threat Score Calculation**: Computes overall threat score based on multiple signals
- **Summary Generation**: Creates concise summary of document content and findings

### Output Generation

- **Structured JSON Output**: Produces machine-readable analysis results
- **Visualization Generation**: Creates graphs and charts of analysis results
- **Report Generation**: Formats results for human consumption

## Data Flow

1. Documents are loaded and normalized
2. Text is processed through spaCy pipeline
3. Custom entities are extracted
4. Anti-democratic patterns are matched
5. Transformer models classify content segments
6. Entity relationships are extracted
7. Content is categorized by threat type
8. Overall threat score is calculated
9. Document summary is generated
10. Results are output in structured format

## Key Interfaces

### `SentinelNLP` Class

Primary interface for using the pipeline:

```python
# Initialize
processor = SentinelNLP()

# Process single document
result = processor.analyze_document(document)

# Process multiple documents
results = processor.process_documents(documents)
```

### Document Format

Input documents should be dictionaries with:

```python
document = {
    "title": "Document title",
    "content": "Document content...",
    "source_type": "legislation|executive_order|court_ruling|media|other",
    "metadata": {
        # Optional additional metadata
    }
}
```

### Result Format

Analysis results are returned as dictionaries with:

```python
result = {
    "document_id": "unique_id",
    "title": "Document title",
    "content": "Original content",
    "entities": {...},
    "anti_democratic_matches": {...},
    "entity_relationships": [...],
    "threat_categories": {...},
    "threat_score": 0.75,
    "summary": "Generated summary..."
}
``` 
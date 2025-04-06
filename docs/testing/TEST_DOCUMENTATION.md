# Sentinel NLP Testing Documentation

This document provides detailed information about testing the Sentinel NLP pipeline, including test scripts, validation methodology, and interpreting results.

## Testing Components

The testing system consists of two main scripts:

1. **`test_nlp_enhancements.py`**: Tests basic functionality and individual components
2. **`validate_nlp_pipeline.py`**: Performs comprehensive validation with multiple test documents

## Basic Testing

### Running the Basic Test

To run the basic functionality test:

```bash
python test_nlp_enhancements.py
```

### Test Components and Methodology

The `test_nlp_enhancements.py` script breaks down testing into modular components:

#### 1. Basic NLP Testing

Tests core spaCy functionality without custom components:

```python
def test_nlp_simple():
    """Test basic NLP functionality without the custom entity extraction."""
    # Load spaCy directly
    nlp = spacy.load("en_core_web_md")
    
    # Simple test of the model
    test_text = "The Department of Justice has concerns about voting rights."
    doc = nlp(test_text)
    # Verify entity extraction works
```

#### 2. Custom Entity Extraction Testing

Tests the custom entity extraction in isolation:

```python
def test_custom_entity_extraction():
    """Test the custom entity extraction functionality separately."""
    # Manual implementation of entity extraction
    # Verify government agencies and legal terms are detected
```

#### 3. Full Pipeline Testing

Tests the complete NLP pipeline with a sample document:

```python
def test_nlp_enhancements():
    """Test the enhanced NLP pipeline with a sample document."""
    # First verify components work individually
    # Then test the full pipeline
    # Analyze and display results
```

### Sample Document

The test uses a sample document containing anti-democratic content:

```python
sample_document = {
    "title": "Proposed Legislation to Revise Voter ID Requirements",
    "content": """
    The proposed legislation would require voters to present two forms of photo identification
    at polling stations in order to cast a ballot. The bill would also reduce early voting days
    from 14 to 5 and eliminate same-day voter registration. Proponents argue these measures are
    necessary to ensure electoral integrity, while critics claim they will disproportionately
    affect minority and low-income voters.
    
    The Department of Justice has expressed concerns that the legislation may violate Section 2
    of the Voting Rights Act. The bill would also grant emergency powers to election officials
    to delay or relocate polling stations with minimal notice.
    
    Additionally, the legislation includes provisions to modify the state's electoral certification
    process, allowing the state legislature to review and potentially override county-level results
    under certain circumstances.
    """,
    "source_type": "state_legislature"
}
```

### Test Output

The test generates a detailed analysis output that includes:

- Extracted entities by type
- Detected anti-democratic patterns with scores
- Entity relationships and their threat implications
- Threat category scores
- Overall threat score
- Document summary

The full analysis is saved to `sample_analysis.json` for inspection.

## Comprehensive Validation

### Running the Validation

To run the comprehensive validation:

```bash
python validate_nlp_pipeline.py
```

### Validation Methodology

The validation system uses multiple test documents covering different types of anti-democratic content:

1. **Voting Rights Restrictions**: Tests detection of voter ID laws and polling place limitations
2. **Executive Power Expansion**: Tests detection of emergency powers and constitutional suspensions
3. **Judicial Independence Threats**: Tests detection of court reform that undermines separation of powers
4. **Media Restrictions**: Tests detection of press freedom limitations

### Validation Metrics

For each test document, the validation measures:

- **Processing Time**: How long it takes to analyze the document
- **Threat Score Accuracy**: Whether the document receives an appropriate threat score
- **Category Detection**: Whether expected threat categories are identified
- **Pattern Recognition**: Whether specific anti-democratic patterns are detected

### Expected Categories

Each test document has expected categories that should be detected:

```python
"expected_categories": ["voting_rights", "anti_democratic"]
```

The validation reports what percentage of expected categories were successfully detected.

### Validation Output

The validation generates:

1. **Console Output**: Real-time results of each test document
2. **Individual Analysis Files**: Detailed analysis of each test document in the `validation_results` directory
3. **Summary Report**: `validation_summary.json` with aggregate metrics

Example validation summary:

```json
{
  "timestamp": "2025-04-04 17:33:06",
  "documents_processed": 4,
  "average_processing_time": 1.38,
  "average_match_percentage": 87.5,
  "document_results": [
    {
      "id": "voting_restrictions",
      "title": "Proposed Legislation to Revise Voter ID Requirements",
      "threat_score": 0.75,
      "top_categories": [
        ["civil_liberties", 1.0],
        ["executive_power", 0.97],
        ["anti_democratic", 0.95]
      ],
      "expected_categories": ["voting_rights", "anti_democratic"],
      "match_percentage": 50.0,
      "processing_time": 4.87
    },
    // Additional document results...
  ]
}
```

## Interpreting Test Results

### Success Criteria

The NLP pipeline is considered successfully validated if:

1. **No Critical Errors**: All tests complete without critical errors
2. **Category Match Rate**: At least 80% of expected categories are detected
3. **Processing Speed**: Average processing time is under 2 seconds per document
4. **Threat Detection**: Anti-democratic documents receive a threat score > 0.6

### Common Warning Messages

During testing, you may see warnings that don't indicate failure:

1. **Entity Overlap Warnings**:
   ```
   WARNING - Error filtering spans: [E1010] Unable to set entity information for token 69...
   ```
   This warning occurs when entities overlap and is handled properly in the code.

2. **Transformer Model Warnings**:
   ```
   Some weights of DistilBertForSequenceClassification were not initialized...
   ```
   This is expected for the transformer model and doesn't affect functionality.

### Troubleshooting

If tests fail, check the following:

1. **spaCy Model**: Ensure the `en_core_web_md` model is installed
2. **Dependencies**: Verify all required packages are installed
3. **Pydantic Version**: Confirm that pydantic version 1.10.8 is installed

## Creating New Tests

### Adding Test Documents

To add new test documents, follow this template:

```python
{
    "id": "unique_test_id",
    "title": "Title of Test Document",
    "content": "Content with specific anti-democratic patterns...",
    "source_type": "document_type",
    "expected_categories": ["category1", "category2"]
}
```

Add your test to the `TEST_DOCUMENTS` list in `validate_nlp_pipeline.py`.

### Testing New Categories

To test a new threat category:

1. Add the category to `self.threat_categories` in `nlp_pipeline.py`
2. Create test documents that should trigger the category
3. Add the category name to `expected_categories` in your test documents
4. Run the validation to verify detection

## Continuous Integration

When integrating updates to the NLP pipeline, always run both test scripts:

```bash
python test_nlp_enhancements.py && python validate_nlp_pipeline.py
```

This ensures that both basic functionality and comprehensive validation pass before deploying changes. 
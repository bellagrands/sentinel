"""
Test script for Sentinel NLP enhancements.

This script tests the enhanced NLP pipeline with a sample document
containing anti-democratic content.
"""

import os
import json
import logging
import sys
import traceback
from processor.nlp_pipeline import SentinelNLP
import spacy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample document with anti-democratic content
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
    "source_type": "state_legislature",
    "date": "2025-04-04",
    "state": "TX",
    "bill_number": "SB 452"
}

def test_nlp_simple():
    """Test basic NLP functionality without the custom entity extraction."""
    print("\n=== Testing Basic NLP Functionality ===\n")
    
    try:
        # Load spaCy directly
        nlp = spacy.load("en_core_web_md")
        print("SpaCy model loaded successfully")
        
        # Simple test of the model
        test_text = "The Department of Justice has concerns about voting rights."
        doc = nlp(test_text)
        print("\nTest document processed. Entities found:")
        for ent in doc.ents:
            print(f"  - {ent.text} ({ent.label_})")
            
        return True
    except Exception as e:
        print(f"Error in basic NLP test: {e}")
        traceback.print_exc()
        return False

def test_custom_entity_extraction():
    """Test the custom entity extraction functionality separately."""
    print("\n=== Testing Custom Entity Extraction ===\n")
    
    try:
        # Load spaCy
        nlp = spacy.load("en_core_web_md")
        
        # Manual implementation of the gov_law_entities function
        gov_agencies = [
            "Department of Justice", "DOJ", "FBI", "Department of Homeland Security", "DHS", 
            "ICE", "Department of Defense", "DOD", "Department of State", "Department of the Interior"
        ]
        
        legal_terms = [
            "U.S. Code", "USC", "Title", "Section", "Public Law", "U.S.C.", 
            "Code of Federal Regulations", "CFR", "Federal Register", "Fed. Reg."
        ]
        
        # Process patterns one by one to avoid recursion errors
        test_text = "The Department of Justice has concerns about voting rights under Title 5 of the U.S. Code."
        doc = nlp(test_text)
        
        print("Test document processed. Default entities:")
        for ent in doc.ents:
            print(f"  - {ent.text} ({ent.label_})")
            
        # Check if agencies and terms are found in text
        print("\nMatched government agencies:")
        for agency in gov_agencies:
            if agency.lower() in test_text.lower():
                print(f"  - {agency}")
                
        print("\nMatched legal terms:")
        for term in legal_terms:
            if term.lower() in test_text.lower():
                print(f"  - {term}")
                
        return True
    except Exception as e:
        print(f"Error in custom entity extraction test: {e}")
        traceback.print_exc()
        return False

def test_nlp_enhancements():
    """Test the enhanced NLP pipeline with a sample document."""
    
    print("=== Testing Sentinel NLP Enhancements ===\n")
    
    try:
        # First test basic NLP functionality
        if not test_nlp_simple():
            print("Basic NLP test failed. Skipping full pipeline test.")
            return False
            
        # Then test custom entity extraction
        if not test_custom_entity_extraction():
            print("Custom entity extraction test failed. Skipping full pipeline test.")
            return False
        
        # Initialize NLP processor with error handling
        try:
            processor = SentinelNLP()
            print("NLP processor initialized.\n")
        except Exception as e:
            print(f"Failed to initialize NLP processor: {e}")
            traceback.print_exc()
            return False
        
        # Process the sample document with proper error handling
        try:
            print("Processing sample document...")
            processed_doc = processor.analyze_document(sample_document)
            print("Document processed.\n")
        except Exception as e:
            print(f"Failed to process document: {e}")
            traceback.print_exc()
            return False
        
        # Display results
        print("=== Analysis Results ===\n")
        
        # Print extracted entities
        print("Extracted entities:")
        for entity_type, entities in processed_doc.get('entities', {}).items():
            if entities:
                print(f"  {entity_type}: {', '.join(entities)}")
        print()
        
        # Print detected anti-democratic patterns
        print("Anti-democratic patterns:")
        for pattern, score in processed_doc.get('anti_democratic_matches', {}).items():
            print(f"  - {pattern} (Score: {score:.2f})")
        print()
        
        # Print entity relationships
        print("Entity relationships:")
        for relationship in processed_doc.get('entity_relationships', []):
            print(f"  - Type: {relationship.get('type')}")
            if 'agency' in relationship:
                print(f"    Agency: {relationship.get('agency')}")
            if 'law' in relationship:
                print(f"    Law: {relationship.get('law')}")
            print(f"    Sentence: {relationship.get('sentence')}")
            print(f"    Threat score: {relationship.get('threat_score'):.2f}")
        print()
        
        # Print threat categories
        print("Threat categories:")
        for category, score in processed_doc.get('threat_categories', {}).items():
            print(f"  - {category}: {score:.2f}")
        print()
        
        # Print overall threat score
        print(f"Overall threat score: {processed_doc.get('threat_score', 0):.2f}")
        print()
        
        # Print summary
        print("Summary:")
        print(processed_doc.get('summary', ''))
        
        # Save the processed document to a file for inspection
        with open('sample_analysis.json', 'w') as f:
            json.dump(processed_doc, f, indent=2)
        print("\nFull analysis saved to 'sample_analysis.json'")
        
        return True
        
    except Exception as e:
        print(f"Unexpected error in test_nlp_enhancements: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_nlp_enhancements()
    if not success:
        print("\nTest failed. See error messages above.")
        sys.exit(1) 
"""
Validation script for Sentinel Democracy Watchdog NLP Pipeline.

This script tests the enhanced NLP pipeline with multiple test documents
to validate different aspects of the system's functionality.
"""

import os
import json
import logging
import time
from processor.nlp_pipeline import SentinelNLP

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test documents covering different aspects of anti-democratic content
TEST_DOCUMENTS = [
    {
        "id": "voting_restrictions",
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
        """,
        "source_type": "state_legislature",
        "expected_categories": ["voting_rights", "anti_democratic"]
    },
    {
        "id": "executive_power",
        "title": "Executive Order on Emergency Powers",
        "content": """
        The President has signed a new executive order expanding emergency powers that allow for 
        the suspension of certain constitutional protections during periods of "national crisis," 
        as defined by the executive branch. The order grants the administration authority to 
        detain individuals without charges for up to 60 days if they are deemed a "potential threat 
        to national security."
        
        Legal experts from the American Civil Liberties Union have filed an emergency petition 
        challenging the constitutionality of the order, arguing it violates fundamental due process 
        rights protected under the Fifth Amendment.
        """,
        "source_type": "executive_branch",
        "expected_categories": ["executive_power", "civil_liberties"]
    },
    {
        "id": "judicial_independence",
        "title": "Proposed Court Reform Legislation",
        "content": """
        The newly proposed Court Reform Act would allow the legislative branch to override 
        judicial decisions with a simple majority vote. The bill would establish a review committee 
        composed of political appointees who could evaluate and potentially nullify court rulings 
        deemed "contrary to public interest."
        
        Constitutional scholars have raised alarms about the proposal, noting it effectively 
        eliminates the separation of powers doctrine established in Article III of the Constitution.
        The Department of Justice has not yet issued a formal position on the legislation.
        """,
        "source_type": "congress",
        "expected_categories": ["anti_democratic", "executive_power"]
    },
    {
        "id": "media_restrictions",
        "title": "New Media Credentialing Requirements",
        "content": """
        The Federal Communications Commission has announced new credentialing requirements for 
        journalists seeking to cover government proceedings. Under the new policy, reporters must 
        undergo background checks and receive approval from the Office of Media Affairs before 
        being granted access to press briefings or other official events.
        
        The policy also establishes a review process for news articles that report on "sensitive 
        government matters," with penalties for outlets that publish information deemed "harmful 
        to national interests" without prior clearance.
        
        The Press Freedom Coalition has condemned the policy as an unconstitutional restriction 
        on First Amendment rights and a dangerous precedent for government control of the press.
        """,
        "source_type": "federal_agency",
        "expected_categories": ["transparency", "civil_liberties"]
    }
]

def validate_nlp_pipeline():
    """Run comprehensive validation tests on the NLP pipeline."""
    print("=== Sentinel NLP Pipeline Validation ===\n")
    
    # Initialize NLP processor
    try:
        processor = SentinelNLP()
        print("NLP processor initialized successfully.\n")
    except Exception as e:
        logger.error(f"Failed to initialize NLP processor: {e}")
        return False
    
    # Create results directory
    results_dir = "logs/validation_results"
    os.makedirs(results_dir, exist_ok=True)
    
    all_results = []
    
    # Process each test document
    for i, doc in enumerate(TEST_DOCUMENTS):
        print(f"Test {i+1}/{len(TEST_DOCUMENTS)}: Processing '{doc['title']}'")
        
        try:
            start_time = time.time()
            processed = processor.analyze_document(doc)
            processing_time = time.time() - start_time
            
            # Save the processed document
            output_file = f"{results_dir}/{doc['id']}_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(processed, f, indent=2)
                
            # Display results and validate expectations
            print(f"  Threat score: {processed.get('threat_score', 0):.2f}")
            print("  Top threat categories:")
            
            # Sort categories by score
            top_categories = sorted(
                processed.get('threat_categories', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for category, score in top_categories:
                print(f"    - {category}: {score:.2f}")
                
            # Validate expected categories
            expected_found = 0
            for expected in doc.get("expected_categories", []):
                # Find this category in the results
                found = False
                for category, score in top_categories:
                    if expected.lower() in category.lower() and score > 0.5:
                        found = True
                        expected_found += 1
                        break
                if not found:
                    print(f"  WARNING: Expected category '{expected}' not found in top results")
            
            # Calculate expectation match percentage
            expected_count = len(doc.get("expected_categories", []))
            match_percentage = (expected_found / expected_count * 100) if expected_count > 0 else 0
            print(f"  Expected categories match: {match_percentage:.0f}%")
            
            # Print anti-democratic patterns detected
            if processed.get('anti_democratic_matches'):
                print("  Anti-democratic patterns detected:")
                for pattern, score in processed.get('anti_democratic_matches', {}).items():
                    print(f"    - {pattern} (Score: {score:.2f})")
            else:
                print("  No anti-democratic patterns detected")
                
            # Print summary
            print(f"  Summary: {processed.get('summary', 'No summary generated')}")
            print(f"  Processing time: {processing_time:.2f} seconds")
            print()
            
            # Add to results collection
            all_results.append({
                "id": doc['id'],
                "title": doc['title'],
                "threat_score": processed.get('threat_score', 0),
                "top_categories": top_categories[:5],
                "expected_categories": doc.get("expected_categories", []),
                "match_percentage": match_percentage,
                "processing_time": processing_time
            })
            
        except Exception as e:
            logger.error(f"Error processing test document '{doc['title']}': {e}")
            print(f"  ERROR: Failed to process document: {e}")
    
    # Generate summary report
    try:
        summary_report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "documents_processed": len(all_results),
            "average_processing_time": sum(r["processing_time"] for r in all_results) / len(all_results) if all_results else 0,
            "average_match_percentage": sum(r["match_percentage"] for r in all_results) / len(all_results) if all_results else 0,
            "document_results": all_results
        }
        
        # Save summary report
        with open(f"{results_dir}/validation_summary.json", 'w') as f:
            json.dump(summary_report, f, indent=2)
        
        # Print overall summary
        print("=== Validation Summary ===")
        print(f"Documents processed: {summary_report['documents_processed']}")
        print(f"Average processing time: {summary_report['average_processing_time']:.2f} seconds")
        print(f"Average category match: {summary_report['average_match_percentage']:.0f}%")
        print(f"Detailed results saved to: {results_dir}/validation_summary.json")
        
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        print(f"ERROR: Failed to generate summary report: {e}")
    
    return True

if __name__ == "__main__":
    validate_nlp_pipeline() 
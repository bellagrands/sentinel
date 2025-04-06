"""
Benchmark utility for the Sentinel NLP Pipeline.

This script measures performance metrics for the NLP pipeline, including:
- Processing time
- Memory usage
- Accuracy on test datasets
- Throughput (documents per minute)

Usage:
    python -m tests.benchmark_nlp --docs 50 --samples 5 --batch-size 10
"""

import argparse
import gc
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processor.nlp_pipeline import SentinelNLP
from processor.memory_optimization import log_memory_usage, memory_tracker, batch_process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Sample documents for benchmarking
SAMPLE_DOCS = [
    {
        "title": "Proposed Legislation to Revise Voter ID Requirements",
        "content": """
        The proposed legislation would require all eligible voters to present government-issued photo 
        identification at polling locations. The bill eliminates the current provisions that allow voters 
        to use utility bills, bank statements, or student IDs as valid identification. Additionally, 
        the early voting period would be reduced from 14 to 5 days, and same-day voter registration 
        would be eliminated. The bill also introduces stricter signature matching requirements for 
        mail-in ballots and limits the number of ballot drop boxes to one per county regardless of 
        population size. Proponents argue these measures enhance election integrity, while opponents 
        claim they create barriers to voting that will disproportionately impact low-income communities 
        and people of color. The state's ACLU chapter has already announced plans to challenge the 
        legislation if passed.
        """,
        "source_type": "legislation",
        "date": "2023-06-15",
        "state": "Georgia",
        "bill_number": "SB 202"
    },
    {
        "title": "Executive Order on Emergency Powers",
        "content": """
        Today, the President signed an executive order expanding emergency powers in response to 
        potential civil unrest. The order authorizes the domestic deployment of military personnel 
        to maintain order, suspends certain due process requirements for individuals deemed security 
        threats, and establishes a special task force to monitor and restrict online communications that 
        'encourage unlawful activity.' The order cites national security concerns and the need to protect 
        critical infrastructure as justification for these expanded authorities. Constitutional scholars 
        have raised concerns about the breadth of the order and its implications for civil liberties. 
        The American Civil Liberties Union has already filed a legal challenge, arguing that the order 
        violates constitutional protections for due process, free speech, and limits on executive power.
        """,
        "source_type": "executive_order",
        "date": "2023-07-10",
        "document_number": "EO-2023-15"
    },
    {
        "title": "New Media Credentialing Requirements",
        "content": """
        The Department of Communications has announced new credentialing requirements for journalists 
        seeking access to government press briefings and events. Under the new policy, reporters must be 
        employed by officially registered media organizations that have been operational for at least five 
        years and must submit to background checks conducted by the Bureau of Security. Independent journalists, 
        bloggers, and representatives from newer media outlets will be limited to a small pool of rotating 
        credentials that provide restricted access. Media organizations must also disclose their funding 
        sources and submit content for review if it directly quotes government officials. Press freedom 
        organizations have criticized the measures as an attempt to control media access and limit scrutiny 
        of government activities.
        """,
        "source_type": "government_notice",
        "date": "2023-08-05",
        "agency": "Department of Communications"
    },
    {
        "title": "Judicial Independence Protection Act",
        "content": """
        This bill aims to strengthen judicial independence by establishing stricter protections against political 
        interference in court proceedings. The legislation creates an independent oversight committee to review 
        complaints of political pressure on judges, establishes penalties for attempting to unduly influence 
        judicial decisions, and secures funding for courts that cannot be reduced during budget negotiations. 
        Additionally, it strengthens recusal requirements for judges with potential conflicts of interest 
        and mandates transparency in judicial appointment processes. The bill has received support from 
        bar associations and judicial reform advocates who argue it will help insulate courts from partisan 
        pressures and special interests.
        """,
        "source_type": "legislation",
        "date": "2023-05-20",
        "state": "Federal",
        "bill_number": "H.R. 1234"
    },
    {
        "title": "State Election Procedures Modernization Act",
        "content": """
        The proposed legislation aims to modernize the state's election procedures by expanding voting 
        options and streamlining registration processes. Key provisions include automatic voter registration 
        when obtaining or renewing driver's licenses, two weeks of early voting including weekends, 
        no-excuse absentee voting, and the establishment of vote centers where any county resident can 
        cast their ballot regardless of their assigned precinct. The bill also allocates funding for 
        upgraded voting equipment with paper backup systems and enhanced cybersecurity measures. 
        Additionally, the legislation creates a nonpartisan election administration board to oversee 
        implementation and address concerns. Proponents argue these changes will increase voter participation 
        and election security, while maintaining integrity through modern safeguards.
        """,
        "source_type": "legislation",
        "date": "2023-09-10",
        "state": "Michigan",
        "bill_number": "HB 4567"
    }
]

def generate_benchmark_documents(num_docs: int, base_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate a set of benchmark documents by duplicating and slightly modifying base documents.
    
    Args:
        num_docs: Number of documents to generate
        base_docs: Base documents to use as templates
        
    Returns:
        List of benchmark documents
    """
    result = []
    
    # Generate variations of base documents
    for i in range(num_docs):
        # Select a random base document
        base_doc = random.choice(base_docs).copy()
        
        # Add unique ID and modify slightly
        base_doc['document_id'] = f"benchmark-doc-{i+1}"
        
        # For some documents, add some random variations to test robustness
        if random.random() > 0.7:
            # Truncate content to test shorter documents
            content = base_doc['content']
            split_point = random.randint(len(content) // 3, len(content))
            base_doc['content'] = content[:split_point]
        
        result.append(base_doc)
    
    return result

@memory_tracker
def run_benchmark(docs: List[Dict[str, Any]], batch_size: int = 10) -> Dict[str, Any]:
    """
    Run benchmark on the NLP pipeline with the given documents.
    
    Args:
        docs: List of documents to process
        batch_size: Number of documents to process in each batch
        
    Returns:
        Dictionary with benchmark results
    """
    # Initialize NLP processor
    processor = SentinelNLP()
    
    # Start timing
    start_time = time.time()
    
    # Process documents in batches
    processed_docs = []
    
    def process_batch(batch):
        """Process a batch of documents and return the results."""
        return [processor.analyze_document(doc) for doc in batch]
    
    processed_docs = batch_process(
        docs, 
        process_batch, 
        batch_size=batch_size
    )
    
    # Calculate metrics
    total_time = time.time() - start_time
    docs_per_second = len(docs) / total_time
    docs_per_minute = docs_per_second * 60
    avg_time_per_doc = total_time / len(docs)
    
    # Calculate memory usage
    mem_info = {}
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = {
            "rss_mb": process.memory_info().rss / (1024 * 1024),
            "vms_mb": process.memory_info().vms / (1024 * 1024)
        }
    except ImportError:
        logger.warning("psutil not available, skipping memory usage metrics")
        mem_info = {"note": "psutil not available"}
    
    # Calculate result metrics
    avg_threat_score = sum(doc.get('threat_score', 0) for doc in processed_docs) / len(processed_docs)
    threat_scores = [doc.get('threat_score', 0) for doc in processed_docs]
    
    # Force garbage collection
    gc.collect()
    
    # Return benchmark results
    return {
        "num_documents": len(docs),
        "batch_size": batch_size,
        "total_time_seconds": total_time,
        "avg_time_per_doc_seconds": avg_time_per_doc,
        "throughput": {
            "docs_per_second": docs_per_second,
            "docs_per_minute": docs_per_minute
        },
        "memory_usage": mem_info,
        "results": {
            "avg_threat_score": avg_threat_score,
            "min_threat_score": min(threat_scores),
            "max_threat_score": max(threat_scores),
            "threat_score_distribution": {
                "0.0-0.2": len([s for s in threat_scores if 0.0 <= s < 0.2]),
                "0.2-0.4": len([s for s in threat_scores if 0.2 <= s < 0.4]),
                "0.4-0.6": len([s for s in threat_scores if 0.4 <= s < 0.6]),
                "0.6-0.8": len([s for s in threat_scores if 0.6 <= s < 0.8]),
                "0.8-1.0": len([s for s in threat_scores if 0.8 <= s <= 1.0])
            }
        },
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Main function to run the benchmark."""
    parser = argparse.ArgumentParser(description='Benchmark the Sentinel NLP Pipeline')
    parser.add_argument('--docs', type=int, default=20, help='Number of documents to process')
    parser.add_argument('--samples', type=int, default=3, help='Number of benchmark samples to run')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    parser.add_argument('--output', type=str, default='benchmark_results.json', help='Output file path')
    args = parser.parse_args()
    
    logger.info(f"Starting benchmark with {args.docs} documents, {args.samples} samples")
    log_memory_usage("Initial memory usage")
    
    results = []
    for i in range(args.samples):
        logger.info(f"Running benchmark sample {i+1}/{args.samples}")
        
        # Generate benchmark documents
        benchmark_docs = generate_benchmark_documents(args.docs, SAMPLE_DOCS)
        
        # Run benchmark
        sample_result = run_benchmark(benchmark_docs, batch_size=args.batch_size)
        results.append(sample_result)
        
        # Log results
        logger.info(f"Sample {i+1} results: "
                   f"Avg time per doc: {sample_result['avg_time_per_doc_seconds']:.2f}s, "
                   f"Throughput: {sample_result['throughput']['docs_per_minute']:.2f} docs/min")
        
        # Wait between samples to let system stabilize
        if i < args.samples - 1:
            logger.info("Waiting between samples...")
            time.sleep(2)
            gc.collect()
    
    # Calculate average metrics
    avg_results = {
        "num_samples": args.samples,
        "avg_time_per_doc_seconds": sum(r['avg_time_per_doc_seconds'] for r in results) / len(results),
        "avg_throughput_docs_per_minute": sum(r['throughput']['docs_per_minute'] for r in results) / len(results),
        "avg_threat_score": sum(r['results']['avg_threat_score'] for r in results) / len(results),
        "individual_samples": results,
        "parameters": vars(args),
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results
    os.makedirs('benchmark_results', exist_ok=True)
    output_path = os.path.join('benchmark_results', args.output)
    with open(output_path, 'w') as f:
        json.dump(avg_results, f, indent=2)
    
    logger.info(f"Benchmark complete. Results saved to {output_path}")
    logger.info(f"Average time per document: {avg_results['avg_time_per_doc_seconds']:.2f}s")
    logger.info(f"Average throughput: {avg_results['avg_throughput_docs_per_minute']:.2f} docs/min")
    
if __name__ == "__main__":
    main() 
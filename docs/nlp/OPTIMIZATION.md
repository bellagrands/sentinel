# Memory Optimization and Performance Benchmarking

This document describes the memory optimization techniques and performance benchmarking tools implemented in the Sentinel NLP Pipeline.

## Memory Optimization

The Sentinel NLP Pipeline includes several memory optimization strategies to handle large document collections efficiently. These optimizations are crucial when processing thousands of government documents that can vary significantly in size and complexity.

### Key Optimization Techniques

#### 1. Batch Processing

Process documents in configurable batches rather than all at once:

```python
from processor.memory_optimization import batch_process

# Process documents in batches of 10
results = batch_process(
    documents,
    process_function,
    batch_size=10
)
```

This prevents memory consumption from growing linearly with the number of documents.

#### 2. Selective Transformer Usage

Reduce memory consumption by only using transformer models when necessary:

```python
from processor.memory_optimization import should_use_transformer

# Determine if transformer processing is needed
if should_use_transformer(document, initial_nlp_score=0.35):
    # Use transformer-based analysis
    result = full_analysis(document)
else:
    # Use lighter analysis
    result = basic_analysis(document)
```

Transformer models require significantly more memory but may not be necessary for documents that show little potential for anti-democratic content.

#### 3. Text Length Limiting

Prevent memory issues with extremely large documents:

```python
from processor.memory_optimization import limit_text_length

# Limit text to 100,000 characters
content = limit_text_length(document['content'], max_length=100000)
```

#### 4. Memory Usage Tracking

Monitor memory consumption during processing:

```python
from processor.memory_optimization import memory_tracker

@memory_tracker
def my_memory_intensive_function():
    # Function logic here
    pass
```

The decorator logs memory usage before and after function execution to help identify memory bottlenecks.

#### 5. Automatic Garbage Collection

Force garbage collection between batch processing:

```python
import gc

# Process batch
process_batch(current_batch)

# Force garbage collection
collected = gc.collect()
logger.debug(f"Garbage collected {collected} objects")
```

### Two-Level Analysis Strategy

The pipeline implements a two-level analysis approach to conserve resources:

1. **Basic Analysis**: Fast, memory-efficient processing that:
   - Uses spaCy tokenization without full pipeline
   - Applies pattern matching for anti-democratic content
   - Calculates preliminary threat scores

2. **Full Analysis**: Comprehensive but more resource-intensive:
   - Uses complete spaCy pipeline with custom components
   - Employs transformer-based classification
   - Extracts entity relationships
   - Generates summaries

Documents are first processed with basic analysis, and only those meeting a certain threshold proceed to full analysis.

## Performance Benchmarking

The Sentinel project includes a benchmarking tool for measuring NLP pipeline performance:

### Running Benchmarks

```bash
# Run basic benchmark with default settings
python -m tests.benchmark_nlp

# Customize benchmark parameters
python -m tests.benchmark_nlp --docs 50 --samples 3 --batch-size 10
```

### Benchmark Parameters

- `--docs`: Number of documents to process in each benchmark sample
- `--samples`: Number of benchmark runs to average results across
- `--batch-size`: Document batch size for processing
- `--output`: Custom filename for benchmark results

### Metrics Measured

The benchmark tool reports:

1. **Processing Time**
   - Average time per document (seconds)
   - Throughput (documents per minute)
   - Total processing time

2. **Memory Usage**
   - Resident Set Size (RSS) in MB
   - Virtual Memory Size (VMS) in MB
   - Memory usage percentage

3. **Result Distribution**
   - Average threat score
   - Threat score distribution across categories
   - Min/max threat scores

### Sample Benchmark Results

```json
{
  "num_samples": 3,
  "avg_time_per_doc_seconds": 1.45,
  "avg_throughput_docs_per_minute": 41.3,
  "avg_threat_score": 0.37,
  "memory_usage": {
    "rss_mb": 854.2,
    "vms_mb": 1203.6
  },
  "threat_score_distribution": {
    "0.0-0.2": 8,
    "0.2-0.4": 21,
    "0.4-0.6": 12,
    "0.6-0.8": 7,
    "0.8-1.0": 2
  }
}
```

## Memory Tuning Guidelines

For optimal performance, consider these tuning guidelines:

1. **Batch Size Selection**
   - Smaller batches (5-10 documents): Use for higher memory conservation
   - Larger batches (20-50 documents): Use for higher throughput when memory is abundant

2. **Transformer Threshold**
   - Lower threshold (0.2-0.3): More documents get full analysis (higher accuracy, higher memory usage)
   - Higher threshold (0.4-0.5): Fewer documents get full analysis (lower memory usage, potential false negatives)

3. **System Requirements**
   - Minimum: 8GB RAM, dual-core processor
   - Recommended: 16GB RAM, quad-core processor
   - High-volume processing: 32GB+ RAM, 8+ cores

## Benchmarking Best Practices

1. Run benchmarks on a system similar to your production environment
2. Test with realistic document volumes and content
3. Monitor both average and peak memory usage
4. Benchmark after any significant pipeline changes
5. Save benchmark results for tracking performance over time

## Future Optimization Plans

- Implement multi-process document processing
- Add caching for frequently accessed entities and patterns
- Explore document chunking for extremely large documents
- Implement incremental memory monitoring during long runs 
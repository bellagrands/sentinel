"""
Memory optimization utilities for the Sentinel NLP Pipeline.

This module provides functions to optimize memory usage when processing
large document collections or lengthy individual documents.
"""

import gc
import logging
import os
import psutil
import time
from functools import wraps
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage information.
    
    Returns:
        Dict with memory usage metrics in MB
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss": memory_info.rss / (1024 * 1024),  # Resident Set Size in MB
        "vms": memory_info.vms / (1024 * 1024),  # Virtual Memory Size in MB
        "percent": process.memory_percent(),
        "available": psutil.virtual_memory().available / (1024 * 1024)  # Available system memory in MB
    }

def log_memory_usage(message: str = "Current memory usage"):
    """Log the current memory usage with an optional message."""
    mem_usage = get_memory_usage()
    logger.info(
        f"{message}: RSS: {mem_usage['rss']:.2f}MB, "
        f"Available: {mem_usage['available']:.2f}MB, "
        f"Usage: {mem_usage['percent']:.2f}%"
    )

def memory_tracker(func: Callable) -> Callable:
    """
    Decorator to track memory usage before and after function execution.
    
    Args:
        func: The function to be decorated
        
    Returns:
        Decorated function with memory usage tracking
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.info(f"Starting {func_name}")
        log_memory_usage(f"Memory before {func_name}")
        
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        log_memory_usage(f"Memory after {func_name}")
        logger.info(f"Completed {func_name} in {elapsed:.2f} seconds")
        
        return result
    return wrapper

def batch_process(items: List[Any], 
                  process_func: Callable, 
                  batch_size: int = 10, 
                  force_gc: bool = True,
                  **kwargs) -> List[Any]:
    """
    Process a list of items in batches to manage memory usage.
    
    Args:
        items: List of items to process
        process_func: Function to process each batch
        batch_size: Number of items to process in each batch
        force_gc: Whether to force garbage collection between batches
        **kwargs: Additional arguments to pass to process_func
        
    Returns:
        List of processed results
    """
    results = []
    total_items = len(items)
    
    for i in range(0, total_items, batch_size):
        batch = items[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(total_items + batch_size - 1)//batch_size} "
                   f"({len(batch)} items)")
        
        log_memory_usage("Memory before batch processing")
        batch_results = process_func(batch, **kwargs)
        results.extend(batch_results)
        
        if force_gc:
            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Garbage collected {collected} objects")
            
        log_memory_usage("Memory after batch processing")
        
    return results

def should_use_transformer(document: Dict[str, Any], 
                          content_key: str = 'content',
                          initial_nlp_score: Optional[float] = None,
                          threshold: float = 0.3) -> bool:
    """
    Decide whether to use transformer models based on initial analysis.
    
    This function helps optimize memory by only using transformer models
    on documents that have a higher likelihood of containing threats.
    
    Args:
        document: The document to analyze
        content_key: The key for accessing document content
        initial_nlp_score: Initial threat score from simpler analysis, if available
        threshold: Score threshold for using transformer models
        
    Returns:
        Boolean indicating whether to use transformer models
    """
    # If initial score is provided and below threshold, skip transformer
    if initial_nlp_score is not None:
        return initial_nlp_score >= threshold
    
    # Otherwise, use basic heuristics based on document content
    content = document.get(content_key, "")
    
    # Simple length-based decision - longer documents get analyzed
    # unless more sophisticated rules are added
    if len(content) > 20000:  # Very long document
        return True
    
    # Add more sophisticated rules here as needed
    
    # Default to using transformers for thorough analysis
    return True

def limit_text_length(text: str, max_length: int = 100000) -> str:
    """
    Limit text length to prevent memory issues with very large documents.
    
    Args:
        text: The text to limit
        max_length: Maximum character length
        
    Returns:
        Truncated text if necessary, original text otherwise
    """
    if len(text) <= max_length:
        return text
    
    logger.warning(f"Truncating text from {len(text)} to {max_length} characters to manage memory")
    return text[:max_length] 
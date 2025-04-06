from typing import Dict, List, TypeVar, Any

T = TypeVar('T')

def paginate_results(items: List[T], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Current page number (1-indexed)
        per_page: Number of items per page
        
    Returns:
        Dict containing:
        - items: List of items for the current page
        - total: Total number of items
        - total_pages: Total number of pages
        - current_page: Current page number
        - per_page: Number of items per page
        - has_next: Whether there is a next page
        - has_prev: Whether there is a previous page
    """
    # Validate inputs
    page = max(1, page)  # Ensure page is at least 1
    per_page = max(1, min(100, per_page))  # Limit items per page between 1 and 100
    
    # Calculate pagination values
    total = len(items)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    # Adjust page if it exceeds total pages
    page = min(page, total_pages) if total_pages > 0 else 1
    
    # Calculate start and end indices
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    return {
        'items': items[start_idx:end_idx],
        'total': total,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': page < total_pages,
        'has_prev': page > 1
    } 
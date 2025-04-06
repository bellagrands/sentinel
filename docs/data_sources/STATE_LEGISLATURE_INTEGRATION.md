# State Legislature Integration Guide (Beta)

This guide provides information about integrating with state legislature data sources in Sentinel. This feature is currently in beta and supports a limited number of states.

## Overview

The State Legislature integration allows Sentinel to monitor and analyze legislative documents from various U.S. state legislatures. Due to the varying data formats, access methods, and update frequencies across different states, this integration is currently experimental and supports a subset of states.

## Data Source Details

- **Coverage**: Currently supported states include:
  - California (leginfo.legislature.ca.gov)
  - New York (nysenate.gov)
  - Texas (capitol.texas.gov)
  - Florida (flsenate.gov)
  - Illinois (ilga.gov)
  
- **Document Types**:
  - Bills
  - Resolutions
  - Amendments
  - Committee Reports
  - Fiscal Notes
  - Voting Records

- **Update Frequency**: Varies by state
  - Most states update daily
  - Some states update in real-time during legislative sessions
  - Updates may be delayed during non-session periods

## Setup and Authentication

1. **API Access**:
   - Some states require API keys for access
   - Others provide public access with rate limiting
   - Contact each state's legislative services for API access details

2. **Configuration**:
   ```yaml
   state_legislature:
     enabled: true
     states:
       california:
         api_key: "YOUR_CA_API_KEY"
         enabled: true
       new_york:
         api_key: "YOUR_NY_API_KEY"
         enabled: true
       texas:
         enabled: true  # No API key required
       florida:
         api_key: "YOUR_FL_API_KEY"
         enabled: false
       illinois:
         enabled: true  # No API key required
   ```

## Configuration Options

The following options can be configured in your `config.yaml`:

```yaml
state_legislature:
  enabled: true                    # Enable/disable the entire integration
  update_frequency: 24             # Hours between updates
  max_days_back: 30               # Maximum days to look back for documents
  states:
    state_name:                   # State identifier (e.g., california)
      enabled: true               # Enable/disable specific state
      api_key: "API_KEY"         # API key if required
      document_types:            # List of document types to monitor
        - bills
        - resolutions
        - amendments
      chambers:                  # Legislative chambers to monitor
        - upper                 # Senate/Upper chamber
        - lower                 # House/Assembly/Lower chamber
      session_year: 2024        # Legislative session year
      topics:                   # Optional topic filtering
        - technology
        - healthcare
        - finance
```

## Document Collection Process

1. **State-Specific Adapters**:
   - Each state has a dedicated adapter class
   - Handles differences in API endpoints and data formats
   - Implements rate limiting and error handling

2. **Document Processing**:
   ```python
   class StateDocumentProcessor:
       def process_document(self, raw_document):
           # Extract common fields
           document = {
               'document_id': f"{state_code}_{doc_number}",
               'title': raw_document.get('title'),
               'content': self.extract_content(raw_document),
               'source_type': 'state_legislature',
               'state': state_code,
               'document_type': raw_document.get('type'),
               'publication_date': raw_document.get('date'),
               'metadata': {
                   'state': state_code,
                   'chamber': raw_document.get('chamber'),
                   'session': raw_document.get('session'),
                   'sponsors': raw_document.get('sponsors', []),
                   'status': raw_document.get('status'),
                   'last_action': raw_document.get('last_action')
               }
           }
           return document
   ```

## Data Structure

Documents collected from state legislatures follow this schema:

```json
{
    "document_id": "CA_AB1234_2024",
    "title": "An act to amend Section...",
    "content": "Full text of the bill...",
    "source_type": "state_legislature",
    "document_type": "bill",
    "publication_date": "2024-03-15",
    "state": "CA",
    "metadata": {
        "state": "CA",
        "chamber": "lower",
        "session": "2023-2024",
        "sponsors": ["Assembly Member Smith"],
        "status": "Introduced",
        "last_action": "Referred to Committee",
        "committee": "Judiciary",
        "fiscal_impact": "Yes",
        "urgency": false,
        "appropriation": false
    }
}
```

## Advanced Usage

### Custom State Adapters

You can create custom adapters for additional states:

```python
from sentinel.collectors.state_legislature import BaseStateAdapter

class CustomStateAdapter(BaseStateAdapter):
    def __init__(self, config):
        super().__init__(config)
        self.state_code = 'XX'
        self.base_url = 'https://legislature.state.xx.us/api'
    
    def fetch_documents(self, start_date, end_date):
        # Implement state-specific document fetching
        pass
    
    def parse_document(self, raw_document):
        # Implement state-specific document parsing
        pass
```

### Filtering Options

- Filter by committee
- Track specific bills
- Monitor particular legislators
- Focus on specific topics
- Track amendments to bills of interest

## Troubleshooting

Common issues and solutions:

1. **Rate Limiting**:
   - Most states implement rate limits
   - Use exponential backoff for retries
   - Cache responses when possible

2. **Session Changes**:
   - Document availability may change during session transitions
   - Update session years in configuration
   - Handle session-specific document IDs

3. **API Changes**:
   - States may update their APIs without notice
   - Monitor for parsing errors
   - Update adapters as needed

4. **Data Consistency**:
   - Document formats vary by state
   - Some fields may be missing
   - Handle incomplete data gracefully

## Limitations and Considerations

1. **Beta Status**:
   - This integration is experimental
   - Support for states may change
   - Features may be added or removed

2. **Data Quality**:
   - Varies by state
   - May have inconsistent formatting
   - Some documents may be incomplete

3. **Performance**:
   - Collection speed varies by state
   - Rate limits affect update frequency
   - Consider enabling only needed states

4. **Maintenance**:
   - Regular updates required
   - State-specific changes needed
   - Monitor for API changes

## Future Enhancements

Planned improvements:

1. Additional state support
2. Real-time updates where available
3. Enhanced document parsing
4. Improved error handling
5. Better session management
6. More filtering options

## Support

For issues with state legislature integration:

1. Check state-specific documentation
2. Verify API access and keys
3. Review error logs
4. Contact state technical support
5. Open a GitHub issue 
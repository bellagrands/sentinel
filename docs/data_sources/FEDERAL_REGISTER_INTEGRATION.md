# Federal Register Integration

## Overview

The Federal Register integration collects documents from the Federal Register API, including rules, notices, proposed rules, and executive orders. Documents are processed and stored in a standardized format, with alerts generated for significant changes.

## Data Storage

Documents and alerts are stored in the following locations:

```
/
├── data/
│   └── federal_register/  # Federal Register documents
│       ├── fr_2024-12345.json
│       └── fr_2024-67890.json
├── alerts/               # Alert notifications
│   ├── alert_federal_register_20240315_123456.json
│   └── alert_federal_register_20240315_123457.json
└── sources/             # Data source configuration
    └── federal_register.json
```

## Document Types

The integration supports the following document types:
- Rules
- Proposed Rules
- Notices
- Presidential Documents
- Executive Orders
- Other Executive Documents

## Alert Generation

Alerts are automatically generated for:
1. Executive Orders (high priority)
2. Significant regulatory changes
3. Emergency rules and notices
4. Documents matching custom alert criteria

Alert format:
```json
{
  "alert_id": "alert_federal_register_20240315_123456",
  "title": "New Executive Order: Title of the Order",
  "source_type": "federal_register",
  "date": "2024-03-15",
  "threat_score": 0.8,
  "categories": {
    "executive_action": 0.9,
    "policy_change": 0.7
  },
  "summary": "Brief description of the document",
  "document_id": "fr_2024-12345",
  "url": "https://www.federalregister.gov/documents/..."
}
```

## Configuration

Example configuration in `sources/federal_register.json`:
```json
{
  "source_id": "federal_register",
  "name": "Federal Register",
  "status": "active",
  "config": {
    "api_key": "your_api_key",
    "update_frequency": 24,
    "max_days_back": 7,
    "document_types": [
      "RULE",
      "PRORULE",
      "NOTICE",
      "PRESDOCU"
    ],
    "rate_limit": 60,
    "custom_fields": {
      "api_version": "v1",
      "base_url": "https://www.federalregister.gov/api/v1"
    }
  }
}
```

## Authentication

1. Register for an API key at https://www.federalregister.gov/developers
2. Set the API key in your environment:
   ```bash
   export FEDERAL_REGISTER_API_KEY=your_api_key
   ```

## Document Collection Process

1. **Initialization**:
   - Load configuration
   - Validate API key and settings
   - Create necessary directories

2. **Collection**:
   - Calculate date range based on `max_days_back`
   - Fetch documents page by page
   - Apply document type filters
   - Handle rate limiting

3. **Processing**:
   - Extract metadata
   - Generate document ID
   - Convert to standard format
   - Save to `data/federal_register/`

4. **Alert Generation**:
   - Check alert criteria
   - Generate alert if needed
   - Save to `/alerts/`

## Document Format

Collected documents are stored in JSON format:
```json
{
  "document_id": "fr_2024-12345",
  "title": "Document Title",
  "content": "Document abstract or content",
  "source_type": "federal_register",
  "date": "2024-03-15",
  "collected_at": "2024-03-15T12:34:56",
  "metadata": {
    "document_number": "2024-12345",
    "document_type": "Rule",
    "html_url": "https://www.federalregister.gov/documents/...",
    "pdf_url": "https://www.federalregister.gov/documents/.../pdf",
    "agencies": ["Agency Name"],
    "topics": ["Topic 1", "Topic 2"]
  }
}
```

## Advanced Usage

### Custom Alert Criteria

Add custom alert criteria in the configuration:
```json
{
  "alert_criteria": {
    "keywords": ["urgent", "emergency", "immediate"],
    "agencies": ["EPA", "FDA"],
    "topics": ["public health", "environment"],
    "min_threat_score": 0.7
  }
}
```

### Rate Limiting

The integration respects the Federal Register API rate limits:
- Default: 1000 requests per hour
- Configurable via `rate_limit` setting
- Implements exponential backoff on 429 responses

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**:
   - Verify key in environment variables
   - Check key validity at /api/v1/documents
   - Ensure key has necessary permissions

2. **Missing Documents**:
   - Check date range configuration
   - Verify document type filters
   - Review API response logs

3. **Rate Limiting**:
   - Adjust `rate_limit` setting
   - Check API quota usage
   - Implement request caching

## Limitations

1. Historical data limited to 2000-present
2. Some document types may have delayed availability
3. Full text search limited to available fields
4. Rate limits on bulk downloads

## Support

For issues:
1. Check error logs in `logs/federal_register.log`
2. Review API documentation
3. Submit issue with:
   - Configuration (without API key)
   - Error messages
   - Steps to reproduce 
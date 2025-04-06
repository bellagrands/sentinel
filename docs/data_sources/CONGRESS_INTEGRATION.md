# Congress.gov Integration

## Overview

The Congress.gov integration collects legislative documents from the Congress.gov API, including bills, resolutions, amendments, committee reports, and hearing records. Documents are processed and stored in a standardized format, with alerts generated for significant legislative activities.

## Data Storage

Documents and alerts are stored in the following locations:

```
/
├── data/
│   └── congress/           # Congress.gov documents
│       ├── congress_bill_hr1234.json
│       └── congress_resolution_sres567.json
├── alerts/                # Alert notifications
│   ├── alert_congress_20240315_123456.json
│   └── alert_congress_20240315_123457.json
└── sources/              # Data source configuration
    └── congress.json
```

## Document Types

The integration supports the following document types:
- Bills (House and Senate)
- Resolutions (Simple, Joint, and Concurrent)
- Amendments
- Committee Reports
- Hearing Records

## Alert Generation

Alerts are automatically generated for:
1. Bills and resolutions on key topics (e.g., civil rights, voting, elections)
2. Major legislative actions (e.g., passage, signing)
3. Committee activities on monitored topics
4. Documents matching custom alert criteria

Alert format:
```json
{
  "alert_id": "alert_congress_20240315_123456",
  "title": "New Bill: H.R. 1234 - Example Act",
  "source_type": "congress",
  "date": "2024-03-15",
  "threat_score": 0.7,
  "categories": {
    "legislation": 0.9,
    "policy_change": 0.7
  },
  "summary": "Brief description of the bill",
  "document_id": "congress_bill_hr1234",
  "url": "https://www.congress.gov/bill/118th-congress/house-bill/1234"
}
```

## Configuration

Example configuration in `sources/congress.json`:
```json
{
  "source_id": "congress",
  "name": "Congress.gov",
  "status": "active",
  "config": {
    "api_key": "your_api_key",
    "update_frequency": 24,
    "max_days_back": 7,
    "document_types": [
      "BILL",
      "RESOLUTION",
      "AMENDMENT",
      "REPORT",
      "HEARING"
    ],
    "rate_limit": 60,
    "custom_fields": {
      "api_version": "v3",
      "base_url": "https://api.congress.gov/v3"
    }
  }
}
```

## Authentication

1. Register for an API key at https://api.congress.gov/sign-up/
2. Set the API key in your environment:
   ```bash
   export CONGRESS_API_KEY=your_api_key
   ```

## Document Collection Process

1. **Initialization**:
   - Load configuration
   - Validate API key and settings
   - Create necessary directories

2. **Collection**:
   - Calculate date range based on `max_days_back`
   - Fetch documents page by page for each type
   - Apply document type filters
   - Handle rate limiting

3. **Processing**:
   - Extract metadata
   - Generate document ID
   - Convert to standard format
   - Save to `data/congress/`

4. **Alert Generation**:
   - Check alert criteria
   - Generate alert if needed
   - Save to `/alerts/`

## Document Format

Collected documents are stored in JSON format:
```json
{
  "document_id": "congress_bill_hr1234",
  "title": "H.R. 1234 - Example Act",
  "content": "Document summary or content",
  "source_type": "congress",
  "date": "2024-03-15",
  "collected_at": "2024-03-15T12:34:56",
  "metadata": {
    "congress": 118,
    "type": "BILL",
    "number": "H.R. 1234",
    "url": "https://www.congress.gov/bill/118th-congress/house-bill/1234",
    "latest_action": {
      "actionDate": "2024-03-15",
      "text": "Referred to the House Committee on Example"
    },
    "sponsors": [
      {
        "bioguideId": "A000000",
        "name": "Representative Name",
        "state": "ST",
        "party": "Party"
      }
    ],
    "committees": [
      {
        "systemCode": "HSEX",
        "name": "House Committee on Example"
      }
    ],
    "subjects": [
      "Example Subject",
      "Another Subject"
    ]
  }
}
```

## Advanced Usage

### Custom Alert Criteria

Add custom alert criteria in the configuration:
```json
{
  "alert_criteria": {
    "keywords": ["democracy", "election", "voting"],
    "committees": ["House Administration", "Judiciary"],
    "subjects": ["Civil Rights and Liberties", "Elections"],
    "min_threat_score": 0.7
  }
}
```

### Rate Limiting

The integration respects the Congress.gov API rate limits:
- Default: 5000 requests per hour
- Configurable via `rate_limit` setting
- Implements exponential backoff on 429 responses

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**:
   - Verify key in environment variables
   - Check key validity at /api/v3/bill
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

1. Historical data limited by API version
2. Some document types may have delayed availability
3. Full text content not available for all documents
4. Rate limits on bulk downloads

## Support

For issues:
1. Check error logs in `logs/congress.log`
2. Review API documentation
3. Submit issue with:
   - Configuration (without API key)
   - Error messages
   - Steps to reproduce 
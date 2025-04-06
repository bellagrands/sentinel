# PACER Integration

## Overview

The PACER (Public Access to Court Electronic Records) integration collects documents from federal court cases, including motions, orders, opinions, and judgments. Documents are processed and stored in a standardized format, with alerts generated for significant legal actions.

## Data Storage

Documents and alerts are stored in the following locations:

```
/
├── data/
│   └── pacer/             # PACER court documents
│       ├── pacer_123456_1.json
│       └── pacer_123456_2.json
├── alerts/               # Alert notifications
│   ├── alert_pacer_20240315_123456.json
│   └── alert_pacer_20240315_123457.json
└── sources/             # Data source configuration
    └── pacer.json
```

## Document Types

The integration supports the following document types:
- Motions
- Orders
- Opinions
- Judgments
- Temporary Restraining Orders
- Injunctions
- Emergency Motions

## Alert Generation

Alerts are automatically generated for:
1. Emergency motions and temporary restraining orders
2. Injunctions and significant orders
3. Cases involving civil rights, voting, or elections
4. Documents matching custom alert criteria

Alert format:
```json
{
  "alert_id": "alert_pacer_20240315_123456",
  "title": "New PACER Document: Emergency Motion for TRO",
  "source_type": "pacer",
  "date": "2024-03-15",
  "threat_score": 0.8,
  "categories": {
    "legal_action": 0.9,
    "civil_rights": 0.7
  },
  "summary": "New document filed in case 1:24-cv-12345",
  "document_id": "pacer_123456_1",
  "url": "https://pcl.uscourts.gov/cases/dcd/1:24-cv-12345"
}
```

## Configuration

Example configuration in `sources/pacer.json`:
```json
{
  "source_id": "pacer",
  "name": "PACER",
  "status": "active",
  "config": {
    "username": "your_username",
    "password": "your_password",
    "update_frequency": 24,
    "max_days_back": 7,
    "rate_limit": 60,
    "custom_fields": {
      "courts": [
        "dcd",  # DC District Court
        "cadc", # DC Circuit
        "nysd", # Southern District of NY
        "ca2"   # Second Circuit
      ],
      "api_version": "v1",
      "base_url": "https://pcl.uscourts.gov/pcl-public-api/v1"
    }
  }
}
```

## Authentication

1. Register for a PACER account at https://pacer.uscourts.gov/
2. Set credentials in your environment:
   ```bash
   export PACER_USERNAME=your_username
   export PACER_PASSWORD=your_password
   ```

## Document Collection Process

1. **Initialization**:
   - Load configuration
   - Validate credentials
   - Create necessary directories

2. **Authentication**:
   - Login to PACER
   - Obtain session token
   - Handle token refresh

3. **Collection**:
   - Calculate date range based on `max_days_back`
   - Search cases in each court
   - Get case details and docket entries
   - Handle rate limiting

4. **Processing**:
   - Filter relevant documents
   - Extract metadata
   - Generate document ID
   - Save to `data/pacer/`

5. **Alert Generation**:
   - Check alert criteria
   - Generate alert if needed
   - Save to `/alerts/`

6. **Cleanup**:
   - Logout from PACER
   - Clear session token

## Document Format

Collected documents are stored in JSON format:
```json
{
  "document_id": "pacer_123456_1",
  "title": "Emergency Motion for Temporary Restraining Order",
  "content": "Document text or summary",
  "source_type": "pacer",
  "date": "2024-03-15",
  "collected_at": "2024-03-15T12:34:56",
  "metadata": {
    "case_number": "1:24-cv-12345",
    "case_title": "Example v. Defendant",
    "court": "dcd",
    "nature_of_suit": "Civil Rights",
    "document_number": "1",
    "document_type": "Motion",
    "page_count": 25,
    "parties": [
      {
        "name": "Example Plaintiff",
        "type": "Plaintiff"
      },
      {
        "name": "Example Defendant",
        "type": "Defendant"
      }
    ],
    "cause": "Violation of Constitutional Rights"
  }
}
```

## Advanced Usage

### Custom Alert Criteria

Add custom alert criteria in the configuration:
```json
{
  "alert_criteria": {
    "document_types": ["TRO", "Injunction", "Emergency Motion"],
    "natures_of_suit": ["Civil Rights", "Voting", "Elections"],
    "courts": ["dcd", "cadc"],
    "min_threat_score": 0.7
  }
}
```

### Rate Limiting

The integration respects PACER's rate limits:
- Default: 60 requests per minute
- Configurable via `rate_limit` setting
- Implements exponential backoff on 429 responses

### Court Selection

Courts are specified using PACER court identifiers:
- District Courts: `{state}{district}d` (e.g., `dcd`, `nysd`)
- Circuit Courts: `ca{circuit}` (e.g., `cadc`, `ca2`)
- Bankruptcy Courts: `{state}{district}b` (e.g., `nysb`)

## Troubleshooting

Common issues and solutions:

1. **Authentication Issues**:
   - Verify credentials in environment variables
   - Check PACER account status
   - Ensure account has API access

2. **Missing Documents**:
   - Check court selection
   - Verify date range configuration
   - Review document type filters

3. **Rate Limiting**:
   - Adjust `rate_limit` setting
   - Implement request caching
   - Use multiple PACER accounts

## Limitations

1. Access requires PACER account and fees
2. Some documents may be sealed or restricted
3. Rate limits per account
4. Document content may require OCR
5. Historical data may be limited

## Support

For issues:
1. Check error logs in `logs/pacer.log`
2. Review PACER documentation
3. Submit issue with:
   - Configuration (without credentials)
   - Error messages
   - Steps to reproduce 
# Data Sources

Sentinel integrates with multiple data sources to monitor and analyze legal and regulatory documents.

## Directory Structure

```
/
├── data/
│   ├── federal_register/    # Federal Register documents
│   ├── congress/           # Congress.gov documents
│   ├── pacer/             # PACER court records
│   └── state_legislature/ # State legislature documents
├── alerts/                # Alert notifications
└── sources/              # Data source configurations
```

## Available Data Sources

### Federal Register
- **Status**: Active
- **Authentication**: API Key required
- **Coverage**: Federal regulations, notices, and executive orders
- **Update Frequency**: Daily
- **Integration Guide**: [Federal Register Integration](FEDERAL_REGISTER_INTEGRATION.md)

### Congress.gov
- **Status**: Active
- **Authentication**: API Key required
- **Coverage**: Bills, resolutions, and congressional records
- **Update Frequency**: Daily
- **Integration Guide**: [Congress.gov Integration](CONGRESS_INTEGRATION.md)

### PACER (Court Records)
- **Status**: Beta
- **Authentication**: PACER credentials required
- **Coverage**: Federal court records and filings
- **Update Frequency**: Real-time
- **Integration Guide**: [PACER Integration](PACER_INTEGRATION.md)

### State Legislatures
- **Status**: Beta
- **Authentication**: Varies by state
- **Coverage**: State bills, resolutions, and legislative records
- **Update Frequency**: Varies by state
- **Integration Guide**: [State Legislature Integration](STATE_LEGISLATURE_INTEGRATION.md)

## Quick Start

1. Configure data sources in `sources/`:
   ```json
   {
     "source_id": "federal_register",
     "name": "Federal Register",
     "status": "active",
     "config": {
       "api_key": "your_api_key",
       "update_frequency": 24,
       "document_types": ["RULE", "NOTICE", "PRORULE"]
     }
   }
   ```

2. Set required environment variables:
   ```bash
   export FEDERAL_REGISTER_API_KEY=your_api_key
   export CONGRESS_API_KEY=your_api_key
   export PACER_USERNAME=your_username
   export PACER_PASSWORD=your_password
   ```

3. Start document collection:
   ```bash
   python -m sentinel.collectors start federal_register
   ```

## Common Features

All data sources share these common features:

### Document Collection
- Configurable update frequency
- Rate limiting and throttling
- Error handling and retries
- Activity logging

### Document Processing
- Standardized document format
- Metadata extraction
- Full-text search indexing
- Alert generation

### Storage
- Documents are stored in source-specific directories under `data/`
- Alerts are stored in `/alerts`
- Source configurations in `sources/`

## Adding New Data Sources

1. Create a new collector class inheriting from `BaseCollector`
2. Implement required methods:
   - `collect()`
   - `validate_config()`
   - `test_connection()`
3. Add configuration schema
4. Update documentation

## Best Practices

1. **Rate Limiting**: Respect API rate limits
2. **Error Handling**: Implement retries with backoff
3. **Validation**: Validate all configurations
4. **Logging**: Use structured logging
5. **Testing**: Write unit tests for collectors

## Troubleshooting

Common issues and solutions:

1. **API Connection Failures**
   - Check API key validity
   - Verify network connectivity
   - Check rate limit status

2. **Missing Documents**
   - Verify date range configuration
   - Check document type filters
   - Review error logs

3. **Performance Issues**
   - Adjust update frequency
   - Optimize document processing
   - Check storage capacity

## Support

For issues and questions:
1. Check troubleshooting guide
2. Review error logs
3. Submit issue with:
   - Data source details
   - Error messages
   - Configuration (without credentials)
   - Steps to reproduce 
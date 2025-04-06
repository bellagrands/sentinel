# Sentinel Democracy Watchdog System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A comprehensive monitoring system that uses AI-powered NLP to track and analyze potential threats to democratic institutions from legislative, executive, and judicial sources.

## Key Features

- 🔍 **Multi-source document collection** from federal courts (PACER), legislative bodies, and executive agencies
- 🧠 **Advanced NLP analysis** with custom entity recognition and threat pattern detection
- 🚨 **Threat scoring** to identify documents posing risks to democratic norms
- 📊 **Interactive dashboard** for monitoring alerts and trends
- 📑 **Automated document processing** with text extraction and summarization
- 🔄 **Containerized deployment** for reliable operation

## Getting Started

### Prerequisites

- Python 3.8 or newer
- Docker and Docker Compose (optional, for containerized deployment)
- Git

### Quick Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. Run the installation script:
   ```bash
   ./install.sh
   ```
   
   This will:
   - Set up necessary directories
   - Install Python dependencies
   - Create a conda environment (optional)
   - Configure environment variables
   - Build Docker containers (optional)

3. Start the system:

   **Docker method (recommended):**
   ```bash
   docker compose up -d
   ```

   **Traditional method:**
   ```bash
   # For the web dashboard:
   python -m uvicorn interface.dashboard.app:app --host 0.0.0.0 --port 8000

   # For document processing:
   python scripts/process_documents.py

   # For document collection:
   python scripts/collect_documents.py
   ```

4. Access the dashboard at http://localhost:8000

### Configuration

Edit the `.env` file to configure:
- API keys for data sources
- Database credentials
- Processing settings
- Alerting thresholds

## Documentation

- [Dashboard Usage Guide](docs/DASHBOARD_USAGE.md)
- [NLP Pipeline Documentation](README_NLP_PIPELINE.md)
- [API Reference](docs/API_REFERENCE.md)
- [PACER Integration](docs/data_sources/PACER_INTEGRATION.md)
- [Technical Notes](TECHNICAL_NOTES.md)
- [Testing Documentation](TEST_DOCUMENTATION.md)

## System Architecture

```
sentinel/
├── interface/            # User interfaces
│   └── dashboard/        # Web dashboard (FastAPI)
├── processor/            # Document processing system
│   └── nlp_pipeline.py   # NLP analysis pipeline
├── scrapers/             # Data collection modules
│   └── pacer_scraper.py  # PACER integration
├── scripts/              # Utility scripts
│   ├── collect_documents.py  # Document collection service
│   └── process_documents.py  # Document processing service
├── data/                 # Data storage
│   ├── alerts/           # High-threat alerts
│   ├── analyzed/         # Processed documents
│   ├── pacer/            # Court documents
│   └── congress/         # Legislative documents
└── docker-compose.yml    # Container configuration
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
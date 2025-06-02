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

**Important Environment Variables for the Dashboard Frontend:**

*   `API_BASE_URL`: This variable **must** be set for the dashboard's Flask application. It should point to the full base URL of the backend API (e.g., `http://sentinel-api:8000/api` if running in Docker, or `http://localhost:8000/api` if running locally). The dashboard relies on this to fetch data for display.
*   `JWT_SECRET_KEY`: This secret key is used for encoding and decoding JSON Web Tokens (JWTs) for user authentication. It **must** be set and should be a strong, unique secret. It needs to be consistent between the authentication module (issuing tokens) and any part of the system that validates them.
*   `SECRET_KEY`: This is a standard Flask secret key used for session management and other security-related features. It **must** be set to a strong, unique secret.

**External Dependencies for Dashboard Frontend:**

*   **Internet Access for CDNs:** The dashboard frontend (`interface/dashboard`) relies on Content Delivery Networks (CDNs) to load:
    *   **Tailwind CSS:** For styling.
    *   **Chart.js:** For rendering charts.
    If the environment where the dashboard is running does not have internet access, these libraries will fail to load, and the dashboard will not render correctly (e.g., it will be unstyled, and charts will be missing). For air-gapped environments, these assets would need to be served locally.

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
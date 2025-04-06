# Sentinel Web Dashboard Guide

This document provides instructions on how to set up, run, and use the Sentinel web dashboard for monitoring democratic threats.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
  - [Docker Setup](#docker-setup)
  - [Manual Setup](#manual-setup)
- [Using the Dashboard](#using-the-dashboard)
  - [Dashboard Home](#dashboard-home)
  - [Alerts](#alerts)
  - [Document Analysis](#document-analysis)
  - [Visualizations](#visualizations)
- [Administration](#administration)
  - [Managing Docker Services](#managing-docker-services)
  - [Logs and Debugging](#logs-and-debugging)
  - [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The Sentinel Web Dashboard provides a user-friendly interface for:

- Monitoring alerts on potential threats to democratic institutions
- Analyzing documents for anti-democratic content
- Visualizing threat trends and patterns
- Managing document collection and processing

The dashboard is built with FastAPI and uses a containerized architecture with Docker for reliable deployment.

## Setup

### Docker Setup (Recommended)

The easiest way to run the Sentinel dashboard is with Docker and Docker Compose.

#### Prerequisites

- Docker and Docker Compose installed
- At least 8GB of RAM available for Docker
- Git to clone the repository

#### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. Create a `.env` file with your configuration:

   ```bash
   # API keys
   CONGRESS_API_KEY=your_congress_api_key
   PACER_USERNAME=your_pacer_username
   PACER_PASSWORD=your_pacer_password
   
   # Optional: OpenAI API key for enhanced summarization
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Build and start the services:

   ```bash
   docker-compose up -d
   ```

4. The dashboard will be available at `http://localhost:8000`

#### Services

The Docker Compose setup includes the following services:

- `dashboard`: The web interface (port 8000)
- `redis`: For caching and inter-service communication
- `processor`: For document analysis
- `collector`: For periodic document collection

### Manual Setup

For development or if you prefer not to use Docker:

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Download the SpaCy model:

   ```bash
   python -m spacy download en_core_web_md
   ```

5. Create necessary directories:

   ```bash
   mkdir -p data/alerts data/analyzed logs
   ```

6. Start the dashboard:

   ```bash
   uvicorn interface.dashboard.app:app --host 0.0.0.0 --port 8000 --reload
   ```

7. The dashboard will be available at `http://localhost:8000`

## Using the Dashboard

### Dashboard Home

The home page provides an overview of the system's status:

- Total documents processed
- Active alerts count
- High-threat document count
- Average threat score
- Recent threat trend chart
- Top threat categories
- Recent alerts table

### Alerts

The alerts page displays all generated alerts:

1. Navigate to "Alerts" in the main navigation
2. View all alerts sorted by threat score
3. Filter alerts by:
   - Minimum threat score
   - Date range
   - Source type
4. Click on any alert to view the associated document details
5. Acknowledge alerts to mark them as reviewed

### Document Analysis

The analysis page allows you to manually analyze documents:

1. Navigate to "Analyze" in the main navigation
2. Enter document details:
   - Title: A descriptive title for the document
   - Content: The full text content to analyze
   - Source Type: The type of document (e.g., pacer, congress, custom)
3. Click "Analyze Document" to process the document
4. View results showing:
   - Overall threat score
   - Top threat categories
   - Entities detected
   - Entity relationships
   - Document summary

### Visualizations

The visualizations page provides insights into the data:

1. Navigate to "Visualize" in the main navigation
2. View various visualizations:
   - Threat trend over time
   - Category distribution
   - Source distribution
   - Entity relationship network
3. Filter visualizations by:
   - Date range
   - Minimum threat score
   - Source types

## Administration

### Managing Docker Services

To manage the Docker services:

#### View service status:

```bash
docker-compose ps
```

#### View logs from all services:

```bash
docker-compose logs
```

#### View logs from a specific service:

```bash
docker-compose logs dashboard
# or
docker-compose logs processor
```

#### Restart a service:

```bash
docker-compose restart dashboard
```

#### Stop all services:

```bash
docker-compose down
```

#### Update services after code changes:

```bash
docker-compose build
docker-compose up -d
```

### Logs and Debugging

Logs are stored in the `logs` directory and are also output to the Docker logs. Key log files:

- `logs/dashboard_YYYYMMDD.log`: Dashboard application logs
- `logs/processor_YYYYMMDD.log`: Document processing logs
- `logs/collector_YYYYMMDD.log`: Document collection logs

For debugging issues:

1. Check the logs for errors
2. Verify Redis is running if cache-related issues occur
3. Check memory usage on the host system (NLP processing can be memory-intensive)

### Configuration

The dashboard and related services can be configured through:

1. Environment variables (set in `.env` file or via Docker Compose)
2. Configuration files in the `config` directory:
   - `processor_config.json`: Document processing settings
   - `collector_config.json`: Document collection settings

### Memory Optimization

For large document collections, consider:

1. Adjusting the batch size in `config/processor_config.json`:

   ```json
   {
     "processing": {
       "batch_size": 5  // Reduce for lower memory usage
     }
   }
   ```

2. Modifying Docker memory limits in `docker-compose.yml`:

   ```yaml
   services:
     processor:
       deploy:
         resources:
           limits:
             memory: 6G  # Increase for larger document batches
   ```

## Troubleshooting

### Common Issues

#### Dashboard cannot connect to Redis

- Check if Redis service is running: `docker-compose ps redis`
- Verify Redis port is exposed: `docker-compose logs redis`

#### Out of memory errors during processing

- Reduce batch size in `config/processor_config.json`
- Increase Docker container memory limits
- Set max document length to a lower value

#### Slow document processing

- Check if the system has sufficient CPU resources
- Monitor memory usage during processing
- Consider using a more powerful machine for production deployments

#### No alerts being generated

- Check collector logs to ensure documents are being collected
- Verify processor logs to confirm documents are being processed
- Check the alert threshold setting in the configuration
- Ensure data directories have proper permissions

### Getting Help

If you encounter issues not covered in this guide:

1. Check the full documentation in the `docs` directory
2. Create an issue on the GitHub repository
3. Join the Sentinel community forum for support 
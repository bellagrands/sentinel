# Sentinel Installation Guide

This guide will help you set up the Sentinel Democracy Watchdog System on your machine.

## Prerequisites

- Python 3.7 or higher
- Git (for cloning the repository)
- API keys for data sources (optional, but enhances functionality)

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/sentinel.git
cd sentinel
```

## Step 2: Set Up Python Environment

Create and activate a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

If you encounter any missing package errors during runtime, you can install them manually:

```bash
pip install package-name
```

## Step 4: Set Up API Keys

Create a `.env` file in the root directory to store your API keys:

```
# .env file
CONGRESS_API_KEY=your_congress_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PACER_USERNAME=your_pacer_username
PACER_PASSWORD=your_pacer_password
OPENSTATES_API_KEY=your_openstates_api_key
```

### How to Obtain API Keys

- **Congress.gov API**: Request an API key from the Library of Congress at [api.congress.gov/sign-up/](https://api.congress.gov/sign-up/)
- **PACER**: Register for a PACER account at [pacer.uscourts.gov](https://pacer.uscourts.gov)
- **Open States API**: Sign up at [openstates.org/api/register/](https://openstates.org/api/register/)
- **OpenAI API** (optional for enhanced analysis): Sign up at [platform.openai.com](https://platform.openai.com)

## Step 5: Initialize Configuration

Generate a default configuration file:

```bash
python main.py --init-config
```

This will create a `config.yaml` file that you can customize for your specific needs.

## Step 6: Directory Structure

Ensure your project has the proper directory structure:

```
sentinel/
├── scrapers/
│   ├── federal_register.py
│   ├── congress_api.py
│   ├── congress_gov.py (optional)
│   ├── pacer_scraper.py (optional)
│   ├── state_legislature.py (optional)
│   └── local_gov.py (optional)
├── processor/
│   └── nlp_pipeline.py
├── alerts/
│   └── rules_engine.py
├── interface/
│   └── chat_integration.py (optional)
├── data/
│   ├── federal_register/
│   ├── congress/
│   ├── pacer/
│   ├── state_legislature/
│   ├── local_government/
│   └── analyzed/
├── logs/
├── alerts/
├── main.py
├── config.yaml
├── requirements.txt
└── .env
```

## Step 7: Verify Installation

Run a basic test to verify that your installation is working:

```bash
python main.py --collect-only --source federal_register
```

This should collect documents from the Federal Register using the default keywords.

## Step 8: Running Sentinel

### Complete Pipeline

To run the complete Sentinel pipeline (collect, analyze, and generate alerts):

```bash
python main.py
```

### Individual Components

You can run each component of Sentinel separately:

```bash
# Only collect documents
python main.py --collect-only

# Only analyze documents
python main.py --analyze-only

# Only generate alerts
python main.py --alerts-only
```

### Working with Alerts

```
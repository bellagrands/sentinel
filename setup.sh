#!/bin/bash
# Sentinel Setup Script
# This script sets up the Sentinel Democracy Watchdog System

set -e

echo "============================================"
echo "  Sentinel Democracy Watchdog Setup Script  "
echo "============================================"

# Create directory structure
echo "Creating directory structure..."
mkdir -p sentinel/scrapers sentinel/processor sentinel/alerts sentinel/interface
mkdir -p sentinel/data/federal_register sentinel/data/congress sentinel/data/pacer sentinel/data/analyzed
mkdir -p sentinel/logs sentinel/alerts

# Move to the sentinel directory
cd sentinel

# Create virtual environment if not using Docker
if [ "$1" != "--docker" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install pyyaml requests beautifulsoup4 pandas numpy scikit-learn spacy python-dotenv
    
    # Download SpaCy model
    echo "Downloading SpaCy language model..."
    python -m spacy download en_core_web_md
fi

# Create .env file template
echo "Creating .env file template..."
cat > .env << EOL
# Sentinel API Keys

# Required for Congress.gov API
# Get from: https://api.congress.gov/sign-up/
CONGRESS_API_KEY=your_congress_api_key_here

# Optional for enhanced NLP analysis
OPENAI_API_KEY=your_openai_api_key_here

# Optional for PACER court records
PACER_USERNAME=your_pacer_username_here
PACER_PASSWORD=your_pacer_password_here

# Optional for state legislature monitoring
OPENSTATES_API_KEY=your_openstates_api_key_here
EOL

# Create initial config file
echo "Creating initial config file..."
cat > config.yml << EOL
# Sentinel Configuration

# Sources to monitor
sources:
  federal_register:
    enabled: true
    scan_frequency_hours: 24
    lookback_days: 7
  
  congress:
    enabled: true
    scan_frequency_hours: 24
    lookback_days: 30
  
  congress_scraper:
    enabled: false
    scan_frequency_hours: 24
    lookback_days: 30
  
  pacer:
    enabled: false
    scan_frequency_hours: 24
    lookback_days: 7
  
  state_legislature:
    enabled: false
    scan_frequency_hours: 24
    lookback_days: 30
    states: ["ca", "ny", "tx"]
  
  local_government:
    enabled: false
    scan_frequency_hours: 24
    jurisdictions: []

# Keywords and terms to monitor
keywords:
  - voting rights
  - civil rights
  - election
  - ballot
  - census
  - executive power
  - emergency declaration
  - citizenship
  - immigration enforcement
  - freedom of information
  - freedom of press
  - media access
  - public education

# NLP settings
nlp:
  threat_threshold: 0.65
  similarity_threshold: 0.75
  summarization_length: 150

# Alert settings
alerts:
  email_enabled: false
  email_recipients: []
  slack_enabled: false
  slack_webhook: ""
EOL

# Create requirements.txt
echo "Creating requirements.txt..."
cat > requirements.txt << EOL
beautifulsoup4==4.12.2
numpy==1.24.3
pandas==2.0.3
python-dotenv==1.0.0
pyyaml==6.0.1
requests==2.31.0
scikit-learn==1.3.0
spacy==3.6.1
EOL

echo "Setup complete! Next steps:"
echo "1. Edit the .env file to add your API keys"
echo "2. Review and customize config.yml as needed"
echo "3. Run 'python main.py' to start Sentinel"

if [ "$1" != "--docker" ]; then
    echo ""
    echo "To activate the environment in the future, run:"
    echo "cd sentinel && source venv/bin/activate"
fi
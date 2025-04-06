#!/bin/bash
# Sentinel Democracy Watchdog System
# Installation Script

set -e

# Color variables
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Sentinel Democracy Watchdog System${NC}"
echo -e "${BLUE}Installation Script${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Check for prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check for Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}Python not found. Please install Python 3.8 or newer.${NC}"
    exit 1
fi

python_version=$(python --version 2>&1 | awk '{print $2}')
echo -e "Python version: ${GREEN}$python_version${NC}"

# Check for pip
if ! command -v pip &> /dev/null; then
    echo -e "${RED}pip not found. Please install pip.${NC}"
    exit 1
fi

# Check for Docker (optional)
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "Docker: ${GREEN}$docker_version${NC}"
    has_docker=true
else
    echo -e "Docker: ${YELLOW}Not found. Docker is optional but recommended for deployment.${NC}"
    has_docker=false
fi

if command -v docker-compose &> /dev/null || command -v docker &> /dev/null && docker compose &> /dev/null; then
    echo -e "Docker Compose: ${GREEN}Found${NC}"
    has_compose=true
else
    echo -e "Docker Compose: ${YELLOW}Not found. Optional for deployment.${NC}"
    has_compose=false
fi

# Create directories
echo -e "\n${YELLOW}Creating necessary directories...${NC}"
mkdir -p data/alerts data/analyzed data/pacer data/congress data/federal_register logs validation_results

# Check for conda and create environment
if command -v conda &> /dev/null; then
    echo -e "\n${YELLOW}Conda found. Would you like to create a conda environment? (y/n)${NC}"
    read -p "> " create_conda_env
    
    if [[ $create_conda_env == "y" || $create_conda_env == "Y" ]]; then
        environment_name="sentinel-nlp"
        echo -e "${YELLOW}Creating conda environment '$environment_name'...${NC}"
        conda create -n $environment_name python=3.9 -y
        echo -e "${GREEN}Conda environment created.${NC}"
        
        echo -e "${YELLOW}Activating conda environment...${NC}"
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate $environment_name
        
        # Install dependencies
        echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
        pip install -r requirements.txt
        
        # Install spaCy model
        echo -e "\n${YELLOW}Installing spaCy model...${NC}"
        python -m spacy download en_core_web_md
        
        echo -e "\n${GREEN}Dependencies installed in conda environment.${NC}"
        echo -e "${YELLOW}To activate the environment, run:${NC}"
        echo -e "conda activate $environment_name"
    else
        # Install dependencies globally
        echo -e "\n${YELLOW}Installing Python dependencies globally...${NC}"
        pip install -r requirements.txt
        
        # Install spaCy model
        echo -e "\n${YELLOW}Installing spaCy model...${NC}"
        python -m spacy download en_core_web_md
    fi
else
    # Install dependencies globally
    echo -e "\n${YELLOW}Conda not found. Installing Python dependencies globally...${NC}"
    pip install -r requirements.txt
    
    # Install spaCy model
    echo -e "\n${YELLOW}Installing spaCy model...${NC}"
    python -m spacy download en_core_web_md
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp -n .env.example .env 2>/dev/null || cp -n .env-sample .env 2>/dev/null || :
    if [ -f .env ]; then
        echo -e "${GREEN}.env file created. Please edit it with your API keys and settings.${NC}"
    else
        echo "# Sentinel Democracy Watchdog System Environment Variables" > .env
        echo "" >> .env
        echo "# API Keys (replace with your actual values)" >> .env
        echo "CONGRESS_API_KEY=your_api_key_here" >> .env
        echo "OPENAI_API_KEY=your_api_key_here" >> .env
        echo "" >> .env
        echo "# PACER Credentials" >> .env
        echo "PACER_USERNAME=your_username_here" >> .env
        echo "PACER_PASSWORD=your_password_here" >> .env
        echo -e "${GREEN}.env file created. Please edit it with your API keys and settings.${NC}"
    fi
fi

# Run validation tests
echo -e "\n${YELLOW}Would you like to run validation tests? (y/n)${NC}"
read -p "> " run_validation
if [[ $run_validation == "y" || $run_validation == "Y" ]]; then
    echo -e "${YELLOW}Running validation tests...${NC}"
    if command -v conda &> /dev/null && [[ $create_conda_env == "y" || $create_conda_env == "Y" ]]; then
        conda activate $environment_name
    fi
    python validate_nlp_pipeline.py
    echo -e "${GREEN}Validation tests completed.${NC}"
fi

# Docker setup
if $has_docker && $has_compose; then
    echo -e "\n${YELLOW}Would you like to build and run using Docker? (y/n)${NC}"
    read -p "> " use_docker
    if [[ $use_docker == "y" || $use_docker == "Y" ]]; then
        echo -e "${YELLOW}Building Docker images...${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose build
        else
            docker compose build
        fi
        
        echo -e "\n${YELLOW}Would you like to start the services now? (y/n)${NC}"
        read -p "> " start_services
        if [[ $start_services == "y" || $start_services == "Y" ]]; then
            echo -e "${YELLOW}Starting services...${NC}"
            if command -v docker-compose &> /dev/null; then
                docker-compose up -d
            else
                docker compose up -d
            fi
            echo -e "${GREEN}Services started. Dashboard available at http://localhost:8000${NC}"
        else
            echo -e "${YELLOW}You can start the services later with:${NC}"
            echo -e "docker-compose up -d"
            echo -e "or"
            echo -e "docker compose up -d"
        fi
    fi
fi

echo -e "\n${GREEN}=============================================${NC}"
echo -e "${GREEN}Sentinel installation completed successfully!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo -e "To run the dashboard: ${YELLOW}python -m uvicorn interface.dashboard.app:app --host 0.0.0.0 --port 8000${NC}"
echo -e "To process documents: ${YELLOW}python scripts/process_documents.py${NC}"
echo -e "To collect documents: ${YELLOW}python scripts/collect_documents.py${NC}"
echo -e "For more information, see the documentation in the docs/ directory." 
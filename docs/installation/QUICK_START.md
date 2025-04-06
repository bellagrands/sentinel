# Sentinel Quick Start Guide

This guide covers how to quickly set up and run the Sentinel Democracy Watchdog System using Docker or a shell script.

## Option 1: Using Docker (Recommended for Contributors)

Docker provides a consistent environment for development and deployment, making it easier for contributors to get started.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. **Create the .env file:**
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file to add your API keys.

3. **Build and start the container:**
   ```bash
   docker-compose up --build
   ```

4. **Run specific components:**
   ```bash
   # Collect documents only
   docker-compose run --rm sentinel python main.py --collect-only
   
   # Analyze documents
   docker-compose run --rm sentinel python main.py --analyze-only
   
   # Generate alerts
   docker-compose run --rm sentinel python main.py --alerts-only
   
   # List pending alerts
   docker-compose run --rm sentinel python main.py --list-pending
   ```

### Docker Tips

- Data is persisted in volumes, so your collected documents will remain even if you restart the container.
- To view logs: `docker-compose logs -f`
- To stop the container: `docker-compose down`
- To rebuild after changes: `docker-compose up --build`

## Option 2: Using the Setup Script

If you prefer a traditional installation, the setup script will create the necessary directory structure and install dependencies.

### Prerequisites

- Python 3.7+
- Bash shell (Linux/macOS/WSL)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure API keys:**
   Edit the `.env` file to add your API keys.

4. **Activate the environment and run Sentinel:**
   ```bash
   source venv/bin/activate
   python main.py
   ```

## API Keys

For full functionality, you'll need the following API keys:

- **Congress.gov API Key** (required): [https://api.congress.gov/sign-up/](https://api.congress.gov/sign-up/)
- **PACER Account** (optional): [https://pacer.uscourts.gov](https://pacer.uscourts.gov)
- **Open States API Key** (optional): [https://openstates.org/api/register/](https://openstates.org/api/register/)
- **OpenAI API Key** (optional): [https://platform.openai.com](https://platform.openai.com)

## Contributing

After setting up the environment, you can start contributing:

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Test your changes:**
   ```bash
   # Using Docker
   docker-compose up --build
   
   # Or using Python directly
   python main.py
   ```

4. **Submit a pull request**

## Troubleshooting

### Docker Issues

- **Error: "Couldn't connect to Docker daemon"**: Make sure Docker is running on your system.
- **Port conflicts**: If port 8080 is already in use, modify the port mapping in `docker-compose.yml`.

### Python Environment Issues

- **Missing modules**: Run `pip install -r requirements.txt` to ensure all dependencies are installed.
- **SpaCy model errors**: Run `python -m spacy download en_core_web_md` to download the required language model.

For more detailed setup instructions, see [INSTALLATION.md](INSTALLATION.md).
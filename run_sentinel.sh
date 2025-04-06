#!/bin/bash
# Run Sentinel with different modes and options

# Display help information
show_help() {
    echo "Sentinel Democracy Watchdog - Run Script"
    echo ""
    echo "Usage: ./run_sentinel.sh [options]"
    echo ""
    echo "Options:"
    echo "  --help                Show this help message"
    echo "  --collect             Only collect documents"
    echo "  --analyze             Only analyze documents"
    echo "  --alerts              Only generate alerts"
    echo "  --list-alerts         List pending alerts"
    echo "  --ack ALERT_ID        Acknowledge an alert by ID"
    echo "  --source SOURCE       Run only for a specific source"
    echo "                        (federal_register, congress, pacer, etc.)"
    echo "  --keywords \"KW1 KW2\"  Override keywords to search for"
    echo "  --docker              Run using Docker"
    echo "  --scheduler           Set up a scheduled run using cron"
    echo ""
    echo "Examples:"
    echo "  ./run_sentinel.sh                     # Run complete pipeline"
    echo "  ./run_sentinel.sh --collect           # Only collect documents"
    echo "  ./run_sentinel.sh --docker            # Run using Docker"
    echo "  ./run_sentinel.sh --source congress   # Only collect from Congress.gov"
    echo "  ./run_sentinel.sh --keywords \"voter suppression\" \"gerrymandering\""
    echo ""
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    # No arguments, run the full pipeline
    if [ -d "venv" ]; then
        echo "Running Sentinel (full pipeline) with Python environment..."
        source venv/bin/activate
        python main.py
    else
        echo "Running Sentinel (full pipeline) with Docker..."
        if command -v docker &> /dev/null && [ -f "docker-compose.yml" ]; then
            docker-compose up --build
        else
            echo "Error: Docker or docker-compose.yml not found"
            echo "Install Docker or run setup.sh to create a Python environment"
            exit 1
        fi
    fi
    exit 0
fi

# Parse arguments
USE_DOCKER=false
CMD_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --collect)
            CMD_ARGS="$CMD_ARGS --collect-only"
            shift
            ;;
        --analyze)
            CMD_ARGS="$CMD_ARGS --analyze-only"
            shift
            ;;
        --alerts)
            CMD_ARGS="$CMD_ARGS --alerts-only"
            shift
            ;;
        --list-alerts)
            CMD_ARGS="$CMD_ARGS --list-pending"
            shift
            ;;
        --ack)
            if [ -z "$2" ]; then
                echo "Error: --ack requires an alert ID"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --acknowledge $2"
            shift 2
            ;;
        --source)
            if [ -z "$2" ]; then
                echo "Error: --source requires a source name"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --source $2"
            shift 2
            ;;
        --keywords)
            keywords=""
            shift
            # Collect all remaining arguments as keywords until the next option
            while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                keywords="$keywords \"$1\""
                shift
            done
            CMD_ARGS="$CMD_ARGS --keywords $keywords"
            ;;
        --scheduler)
            echo "Setting up scheduled run..."
            if command -v crontab &> /dev/null; then
                # Add to crontab - runs collection every 6 hours, analysis every 6 hours offset by 30 minutes
                (crontab -l 2>/dev/null || echo "") | grep -v "sentinel" > temp_cron
                echo "0 */6 * * * cd $(pwd) && ./run_sentinel.sh --collect > $(pwd)/logs/collect.log 2>&1" >> temp_cron
                echo "30 */6 * * * cd $(pwd) && ./run_sentinel.sh --analyze > $(pwd)/logs/analyze.log 2>&1" >> temp_cron
                echo "45 */6 * * * cd $(pwd) && ./run_sentinel.sh --alerts > $(pwd)/logs/alerts.log 2>&1" >> temp_cron
                crontab temp_cron
                rm temp_cron
                echo "Scheduled jobs added to crontab"
                echo "To view scheduled jobs: crontab -l"
                echo "To remove scheduled jobs: crontab -l | grep -v 'sentinel' | crontab -"
            else
                echo "Error: crontab command not found"
                echo "Please set up scheduling manually"
            fi
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute the command
if [ "$USE_DOCKER" = true ]; then
    echo "Running Sentinel with Docker: python main.py $CMD_ARGS"
    if command -v docker &> /dev/null && [ -f "docker-compose.yml" ]; then
        docker-compose run --rm sentinel python main.py $CMD_ARGS
    else
        echo "Error: Docker or docker-compose.yml not found"
        exit 1
    fi
else
    echo "Running Sentinel with Python: python main.py $CMD_ARGS"
    if [ -d "venv" ]; then
        source venv/bin/activate
        python main.py $CMD_ARGS
    else
        echo "Error: Python virtual environment not found"
        echo "Run setup.sh first or use --docker option"
        exit 1
    fi
fi
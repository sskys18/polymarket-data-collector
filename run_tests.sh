#!/bin/bash

# Test runner script for Polymarket Data Collector

set -e  # Exit on error

echo "========================================"
echo "Polymarket Data Collector - Test Runner"
echo "========================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Check if .env exists
if [[ ! -f .env ]]; then
    echo "⚠️  .env file not found"
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your database credentials"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    historical|hist|h)
        echo "Running Historical Data Test..."
        python tests/test_historical_single.py
        ;;
    realtime|real|r)
        echo "Running Real-Time Data Test..."
        python tests/test_realtime_single.py
        ;;
    all|both|a)
        echo "Running All Tests..."
        python tests/test_both.py
        ;;
    *)
        echo "Usage: $0 [historical|realtime|all]"
        echo ""
        echo "Options:"
        echo "  historical (h)  - Test historical data collection"
        echo "  realtime (r)    - Test real-time data collection"
        echo "  all (a)         - Run both tests (default)"
        echo ""
        echo "Examples:"
        echo "  $0              # Run all tests"
        echo "  $0 historical   # Test historical only"
        echo "  $0 realtime     # Test realtime only"
        exit 1
        ;;
esac

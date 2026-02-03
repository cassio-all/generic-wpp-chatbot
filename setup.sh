#!/bin/bash

# Setup script for the WhatsApp Chatbot

echo "========================================"
echo "WhatsApp Chatbot - Setup"
echo "========================================"

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit the .env file and add your API keys!"
    echo ""
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/vector_db
mkdir -p credentials
mkdir -p logs

echo ""
echo "========================================"
echo "✅ Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. (Optional) Add SendGrid API key for email functionality"
echo "3. (Optional) Add Google Calendar credentials for scheduling"
echo "4. Run the chatbot: python -m src.main"
echo ""

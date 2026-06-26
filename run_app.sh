#!/bin/bash
# KPI Agent - Setup & Run Script (Linux/Mac)

echo ""
echo "============================================"
echo " KPI Hub"
echo " Setup & Launch Script"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ using your package manager"
    exit 1
fi

echo "[1/3] Python found: "
python3 --version
echo ""

# Install dependencies
echo "[2/3] Installing dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully"
echo ""

# Run Streamlit app in background and open browser
echo "[3/3] Launching KPI Hub Dashboard..."
echo ""
echo "Opening at http://localhost:8501"
echo "Press Ctrl+C in this window to stop the server"
echo ""

# Start Scheduler in background
echo "Starting Background Sync Scheduler..."
python3 integrations/scheduler.py &

# Start Streamlit in background
streamlit run web_app.py &

# Wait for server to start
sleep 3

# Open browser once (Mac/Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8501
else
    # Linux
    xdg-open http://localhost:8501 &>/dev/null || true
fi

# Wait for user input
wait

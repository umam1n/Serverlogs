#!/bin/bash

# ==============================================================================
# Auto-Execution Script for Server Room Access Control System
# ==============================================================================
# This script automates the startup of all necessary services for development.
# It should be placed in the root directory of your project (e.g., ~/Serverlogs/).
#
# To use it:
# 1. Save this code as a file named `start_dev.sh`.
# 2. Make it executable by running: chmod +x start_dev.sh
# 3. Run the script from your toolbox: ./start_dev.sh
# ==============================================================================

echo "--- Starting Development Environment ---"

# --- 1. Start PostgreSQL Database Server ---
# Check if the PostgreSQL server is already running.
sudo -u postgres pg_isready -q
if [ $? -ne 0 ]; then
    echo "PostgreSQL server is not running. Starting it now..."
    sudo -u postgres /usr/bin/pg_ctl -D /var/lib/pgsql/data -l /var/lib/pgsql/data/logfile start
    # Wait a moment for the server to initialize
    sleep 2
else
    echo "PostgreSQL server is already running."
fi

# --- 2. Activate Python Virtual Environment ---
echo "Activating Python virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Could not activate the virtual environment. Make sure you are in the project root."
    exit 1
fi

# --- 3. Start the FastAPI Face Service in the Background ---
echo "Starting Face Recognition Service in the background..."
(cd face_recognition && uvicorn service:app --port 8001 &)
# Save the Process ID (PID) of the background job so we can stop it later
FACE_PID=$!
echo "Face Service started with PID: $FACE_PID"
# Give the service a moment to start up
sleep 3

# --- 4. Start the Django Server in the Foreground ---
echo "Starting Django Development Server... (Press CTRL+C to stop all services)"
python manage.py runserver

# --- 5. Cleanup After Django Server is Stopped ---
# This part of the script will run after you press CTRL+C in the terminal
echo ""
echo "--- Shutting Down Development Environment ---"
echo "Stopping Face Recognition Service (PID: $FACE_PID)..."
kill $FACE_PID
wait $FACE_PID 2>/dev/null

echo "All services have been stopped. Goodbye!"



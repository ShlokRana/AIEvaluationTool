#!/bin/bash

trap "kill 0" EXIT

VENV_PATH="/home/varun/Desktop/Projects/AIEval/AIEvaluationTool/venv/bin/activate"

echo "🚀 Starting all services..."

# ================================
# TestCaseExecutorDashboard
# ================================

echo "Starting TestCaseExecutorDashboard backend..."
cd src/app/TestCaseExecutorDashboard/back-end/ || exit
source "$VENV_PATH"
python main.py &

cd - || exit

echo "Starting TestCaseExecutorDashboard frontend..."
cd src/app/TestCaseExecutorDashboard/front-end/ || exit
npm start &

cd - || exit

# ================================
# TDMS
# ================================

echo "Starting TDMS backend..."
cd src/app/TDMS/back-end/ || exit
source "$VENV_PATH"
python main.py &

cd - || exit

echo "Starting TDMS frontend..."
cd src/app/TDMS/front-end/ || exit
npm run dev &

cd - || exit

# ================================
# Auth Service
# ================================

echo "Starting Auth Service..."
cd src/app/auth_service/ || exit
source "$VENV_PATH"
python main.py &

cd - || exit

# ================================
# Interface Manager
# ================================

echo "Starting Interface Manager..."
cd src/app/interface_manager/ || exit
source "$VENV_PATH"
python main.py &

cd - || exit

echo "✅ All services started!"
wait
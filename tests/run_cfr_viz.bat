@echo off
REM Run CFR Regret Visualization
REM Make sure CSV files exist in parent directory first!

cd /d "%~dp0"

echo Checking for data files...
if not exist "..\cfr_regrets.csv" (
    echo ERROR: cfr_regrets.csv not found!
    echo Run the CFR simulation first to generate data files.
    pause
    exit /b 1
)

if not exist "..\personality_evolution.csv" (
    echo ERROR: personality_evolution.csv not found!
    echo Run the CFR simulation first to generate data files.
    pause
    exit /b 1
)

echo Data files found. Starting Streamlit...
streamlit run analyze_cfr.py --server.port 8501

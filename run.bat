@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting TK Video Analyzer...
streamlit run app.py --server.port 8501
pause
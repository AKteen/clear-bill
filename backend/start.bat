@echo off

REM Install dependencies
pip install -r requirements.txt

REM Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
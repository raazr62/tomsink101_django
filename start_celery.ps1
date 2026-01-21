# Start Celery Worker for Django AI Plan
# Run this in a separate terminal after starting Django server

Write-Host "Starting Celery Worker..." -ForegroundColor Green
Write-Host "Make sure Redis is running first!" -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment
& "C:\Users\sawaf\Projects\tomsink101_django\venv\Scripts\Activate.ps1"

# Start Celery worker
celery -A project worker --loglevel=info --pool=solo

Write-Host ""
Write-Host "Celery worker stopped." -ForegroundColor Red

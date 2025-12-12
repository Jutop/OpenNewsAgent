# Start the AI News Agent web application

Write-Host "🚀 Starting AI News Agent..." -ForegroundColor Green
Write-Host ""
Write-Host "📖 API Documentation: http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "🌐 Web Interface: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& .\.venv\Scripts\python.exe main.py

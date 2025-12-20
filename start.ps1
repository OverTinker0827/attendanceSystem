# Quick Start Script for Windows PowerShell
# Run this script to quickly start the attendance system

Write-Host "Attendance System - Quick Start" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if PostgreSQL is running
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
try {
    $pgStatus = Get-Service postgresql* -ErrorAction Stop
    if ($pgStatus.Status -ne "Running") {
        Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
        Start-Service $pgStatus.Name
    }
    Write-Host "[OK] PostgreSQL is running" -ForegroundColor Green
} catch {
    Write-Host "[!] PostgreSQL service not found. Please install PostgreSQL." -ForegroundColor Red
    exit 1
}

# Check if database exists
Write-Host "Checking database..." -ForegroundColor Yellow
$dbCheck = psql -U postgres -lqt 2>$null | Select-String -Pattern "attendance_system"
if (-not $dbCheck) {
    Write-Host "Creating database..." -ForegroundColor Yellow
    psql -U postgres -c "CREATE DATABASE attendance_system;" 2>$null
    Write-Host "[OK] Database created" -ForegroundColor Green
} else {
    Write-Host "[OK] Database exists" -ForegroundColor Green
}

# Check if .env file exists
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "[!] Please edit backend\.env with your database credentials" -ForegroundColor Yellow
    notepad "backend\.env"
    Write-Host "Press any key after saving the .env file..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
Write-Host "[OK] Configuration ready" -ForegroundColor Green

# SSL certificates not required (using HTTP)

# Check if virtual environment exists
Write-Host "Checking Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "backend\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    Push-Location backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    Pop-Location
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

# Initialize database
Write-Host "Initializing database tables..." -ForegroundColor Yellow
Push-Location backend
.\venv\Scripts\Activate.ps1
python init_db.py
Pop-Location
Write-Host "[OK] Database initialized" -ForegroundColor Green

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "[OK] Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Start services
Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host ""

# Generate SSL certificates if not exists
if (-not (Test-Path "certs\cert.pem")) {
    Write-Host "Generating SSL certificates (required for webcam)..." -ForegroundColor Yellow
    Push-Location certs
    python generate_certs.py
    Pop-Location
    Write-Host "[OK] SSL certificates generated" -ForegroundColor Green
}

# Start backend in new window
Write-Host "[*] Starting Backend (https://localhost:8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; .\venv\Scripts\Activate.ps1; python main.py" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start frontend in new window with SSL
Write-Host "[*] Starting Frontend (https://localhost:8001)..." -ForegroundColor Yellow

# Check if http-server is installed
$httpServerInstalled = Get-Command http-server -ErrorAction SilentlyContinue
if (-not $httpServerInstalled) {
    Write-Host "[!] http-server not found. Installing..." -ForegroundColor Yellow
    npm install -g http-server
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; http-server -p 8001 -S -C ..\certs\cert.pem -K ..\certs\key.pem" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "[OK] Attendance System is Running!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the system:" -ForegroundColor Cyan
Write-Host "  Student Portal: https://localhost:8001" -ForegroundColor Cyan
Write-Host "  Admin Panel:    https://localhost:8001/admin.html" -ForegroundColor Cyan
Write-Host "  Backend API:    https://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Your browser will show a security warning (self-signed certificate)" -ForegroundColor Yellow
Write-Host "   Click 'Advanced' → 'Proceed to localhost (unsafe)' to continue" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in backend/frontend windows to stop" -ForegroundColor Gray
Write-Host ""

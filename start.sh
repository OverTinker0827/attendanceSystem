#!/bin/bash
# Quick Start Script for Mac/Linux
# Run this script to quickly start the attendance system

echo "🎓 Attendance System - Quick Start"
echo "===================================="
echo ""

# Check if PostgreSQL is running
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL not found. Please install PostgreSQL."
    exit 1
fi

# Start PostgreSQL (Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql 2>/dev/null || true
fi

# Start PostgreSQL (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start postgresql 2>/dev/null || true
fi

echo "✅ PostgreSQL is running"

# Check if database exists
echo "Checking database..."
if ! psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw attendance_system; then
    echo "Creating database..."
    createdb -U postgres attendance_system 2>/dev/null || psql -U postgres -c "CREATE DATABASE attendance_system;"
    echo "✅ Database created"
else
    echo "✅ Database exists"
fi

# Check if .env file exists
echo "Checking configuration..."
if [ ! -f "backend/.env" ]; then
    echo "Creating .env file from example..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your database credentials"
    ${EDITOR:-nano} backend/.env
fi
echo "✅ Configuration ready"

# Check if certificates exist
echo "Checking SSL certificates..."
if [ ! -f "certs/localhost.crt" ]; then
    echo "Generating SSL certificates..."
    cd certs
    python3 generate_certs.py
    cd ..
    echo "✅ Certificates generated"
else
    echo "✅ Certificates exist"
fi

# Check if virtual environment exists
echo "Checking Python virtual environment..."
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    cd ..
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Initialize database
echo "Initializing database tables..."
cd backend
source venv/bin/activate
python init_db.py
cd ..
echo "✅ Database initialized"

echo ""
echo "====================================="
echo "✅ Setup Complete!"
echo "====================================="
echo ""

# Start services
echo "Starting services..."
echo ""

# Start backend in background
echo "🔧 Starting Backend (https://localhost:8000)..."
cd backend
source venv/bin/activate
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

sleep 3

# Start frontend in background
echo "🌐 Starting Frontend (https://localhost:8001)..."
cd frontend
http-server -p 8001 -S -C ../certs/localhost.crt -K ../certs/localhost.key > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "====================================="
echo "🎉 Attendance System is Running!"
echo "====================================="
echo ""
echo "Access the system:"
echo "  📱 Student Portal: https://localhost:8001"
echo "  🔐 Admin Panel:    https://localhost:8001/admin.html"
echo "  🔧 Backend API:    https://localhost:8000"
echo ""
echo "Note: Browser will show certificate warning."
echo "      Click 'Advanced' → 'Proceed to localhost'"
echo ""
echo "Logs:"
echo "  Backend:  backend.log"
echo "  Frontend: frontend.log"
echo ""
echo "To stop the system:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or run: pkill -f 'python main.py'; pkill -f 'http-server'"
echo ""

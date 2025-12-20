# Complete Setup Guide

Step-by-step instructions to set up and run the Attendance System.

## Prerequisites

### Required Software

1. **Python 3.9 or higher**
   - Download: https://www.python.org/downloads/
   - Verify: `python --version`

2. **PostgreSQL 13 or higher**
   - Windows: https://www.postgresql.org/download/windows/
   - Mac: `brew install postgresql`
   - Linux: `sudo apt-get install postgresql`
   - Verify: `psql --version`

3. **Node.js 16 or higher** (for frontend server)
   - Download: https://nodejs.org/
   - Verify: `node --version`

4. **Git** (optional, for cloning)
   - Download: https://git-scm.com/

### Hardware Requirements

- **Webcam**: Required for face capture
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: ~500MB for models and dependencies
- **Internet**: Required for initial model download

---

## Installation Steps

### Step 1: Database Setup

#### 1.1. Start PostgreSQL Service

**Windows:**
```powershell
# Start PostgreSQL service
Start-Service postgresql

# Or use pgAdmin GUI
```

**Mac:**
```bash
brew services start postgresql
```

**Linux:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

#### 1.2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE attendance_system;

# Create user (optional)
CREATE USER attendance_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE attendance_system TO attendance_admin;

# Exit
\q
```

#### 1.3. Verify Connection

```bash
psql -U postgres -d attendance_system -c "SELECT version();"
```

---

### Step 2: Backend Setup

#### 2.1. Navigate to Backend Directory

```bash
cd "attendance system/backend"
```

#### 2.2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2.3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed:**
- FastAPI (web framework)
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- psycopg2 (PostgreSQL driver)
- NumPy (numerical computing)
- Pandas (data export)
- python-dotenv (config management)
- Pydantic (data validation)

#### 2.4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env file
notepad .env  # Windows
nano .env     # Mac/Linux
```

**Edit these values in `.env`:**

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/attendance_system

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecurePassword123!

# Face Recognition Configuration
SIMILARITY_THRESHOLD=0.8
MIN_MATCHES_REQUIRED=2

# Server Configuration
HOST=localhost
PORT=8000
SSL_CERT_PATH=../certs/localhost.crt
SSL_KEY_PATH=../certs/localhost.key
```

#### 2.5. Initialize Database

```bash
python init_db.py
```

**Expected output:**
```
Initializing database...
✅ Database tables created successfully
```

#### 2.6. Verify Database Schema

```bash
psql -U postgres -d attendance_system

# List tables
\dt

# Expected output:
# students
# face_embeddings
# attendance

# Describe tables
\d students
\d face_embeddings
\d attendance

# Exit
\q
```

---

### Step 3: SSL Certificate Setup

#### 3.1. Navigate to Certs Directory

```bash
cd ../certs
```

#### 3.2. Install Certificate Generation Tool

```bash
pip install cryptography
```

#### 3.3. Generate Certificates

```bash
python generate_certs.py
```

**Expected output:**
```
🔐 Generating self-signed SSL certificate for localhost...
✅ Private key saved to: localhost.key
✅ Certificate saved to: localhost.crt
🎉 Certificate valid for 365 days
⚠️  Note: Browser will show security warning for self-signed certificates
```

#### 3.4. (Optional) Install Certificate as Trusted

**Windows:**
1. Double-click `localhost.crt`
2. Click "Install Certificate"
3. Select "Local Machine"
4. Place in "Trusted Root Certification Authorities"
5. Restart browser

**Mac:**
1. Open "Keychain Access"
2. File → Import Items → Select `localhost.crt`
3. Double-click the imported certificate
4. Expand "Trust" section
5. Set "When using this certificate" to "Always Trust"
6. Restart browser

**Linux:**
```bash
sudo cp localhost.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

---

### Step 4: Frontend Setup

#### 4.1. Navigate to Frontend Directory

```bash
cd ../frontend
```

#### 4.2. Install HTTP Server

```bash
npm install -g http-server
```

**Alternative:** Use Python's built-in server:
```bash
pip install pyopenssl
```

---

### Step 5: Running the System

#### 5.1. Start Backend (Terminal 1)

```bash
cd backend
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Mac/Linux

# Run backend
python main.py
```

**Expected output:**
```
✅ Database tables created successfully
✅ Backend started successfully
🔧 Configuration: {'similarity_threshold': 0.8, 'min_matches_required': 2, ...}
INFO:     Uvicorn running on https://localhost:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 5.2. Start Frontend (Terminal 2)

**Using http-server:**
```bash
cd frontend
http-server -p 8001 -S -C ../certs/localhost.crt -K ../certs/localhost.key
```

**Using Python (alternative):**
```bash
cd frontend
python -m http.server 8001 --bind localhost
```

**Expected output:**
```
Starting up http-server, serving ./ through https
Available on:
  https://localhost:8001
Hit CTRL-C to stop the server
```

#### 5.3. Verify Services

Open browser and navigate to:

1. **Backend Health Check:**
   - URL: https://localhost:8000
   - Expected: `{"status": "ok", "service": "Attendance System Backend", "version": "1.0.0"}`

2. **Frontend:**
   - URL: https://localhost:8001
   - Expected: Landing page with registration/attendance buttons

3. **Admin Panel:**
   - URL: https://localhost:8001/admin.html
   - Expected: Login page

**Note:** Browser will show security warning for self-signed certificates. Click "Advanced" → "Proceed to localhost".

---

## First-Time Usage

### Register First Student

1. Navigate to https://localhost:8001
2. Click "Register New Student"
3. Enter student ID: `1RV23CS001`
4. Click "Start Registration"
5. Allow webcam access when prompted
6. Position face in frame
7. System captures 5 images automatically
8. Wait for "Registration Successful" message

### Mark Attendance

1. Click "Mark Attendance"
2. System retrieves student ID from cookie
3. Allow webcam access
4. Position face in frame
5. Click "Verify & Mark Attendance"
6. Wait for verification result

### Access Admin Panel

1. Navigate to https://localhost:8001/admin.html
2. Enter admin credentials:
   - Username: `admin`
   - Password: (from `.env` file)
3. View attendance statistics
4. Filter by date or student
5. Export as CSV

---

## Troubleshooting

### Issue: "Database connection failed"

**Solution:**
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Restart PostgreSQL
# Windows:
Restart-Service postgresql

# Mac:
brew services restart postgresql

# Linux:
sudo systemctl restart postgresql

# Verify DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL
```

### Issue: "Failed to load models"

**Solution:**
- Check internet connection (models download from CDN)
- Clear browser cache: Ctrl+Shift+Delete
- Try different browser (Chrome recommended)
- Check browser console for errors: F12 → Console

### Issue: "Webcam not accessible"

**Solution:**
- Grant camera permission in browser settings
- Close other apps using webcam (Zoom, Skype, etc.)
- Check camera in device manager (Windows)
- Try different browser
- Verify HTTPS (camera requires secure context)

### Issue: "Certificate error" / "NET::ERR_CERT_AUTHORITY_INVALID"

**Expected behavior** with self-signed certificates.

**Solution:**
1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)"
3. Or install certificate as trusted (see Step 3.4)

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows:
.\venv\Scripts\Activate.ps1

# Mac/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill -9 <PID>

# Or change port in backend/.env
PORT=8080
```

### Issue: "Face verification always fails"

**Possible causes:**
- Poor lighting
- Face not clearly visible
- Significant change in appearance
- Threshold too strict

**Solution:**
```bash
# Lower threshold in backend/.env
SIMILARITY_THRESHOLD=0.7
MIN_MATCHES_REQUIRED=1

# Restart backend
```

### Issue: "Attendance already marked" but I didn't mark it

**Cause:** Attendance is once-per-day based on calendar date.

**Solution:**
```bash
# Check attendance records
psql -U postgres -d attendance_system
SELECT * FROM attendance WHERE student_id='1RV23CS001' AND date=CURRENT_DATE;

# Delete record (for testing only)
DELETE FROM attendance WHERE student_id='1RV23CS001' AND date=CURRENT_DATE;
```

---

## Development Tips

### Hot Reload

Backend automatically reloads on file changes when run with `python main.py`.

Frontend requires manual refresh in browser.

### Debugging

**Backend logs:**
```bash
# Run with debug logging
python main.py --log-level debug
```

**Frontend logs:**
- Open browser console: F12 → Console
- Check network tab for API calls

### Database Inspection

```bash
# Connect to database
psql -U postgres -d attendance_system

# Useful queries
SELECT COUNT(*) FROM students;
SELECT * FROM face_embeddings WHERE student_id='1RV23CS001';
SELECT * FROM attendance WHERE date=CURRENT_DATE;
SELECT student_id, COUNT(*) as days FROM attendance GROUP BY student_id;

# Reset database (CAUTION: deletes all data)
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS face_embeddings CASCADE;
DROP TABLE IF EXISTS students CASCADE;
```

Then run:
```bash
python init_db.py
```

### Configuration Changes

After changing `backend/.env`, restart backend:
```bash
# Stop: Ctrl+C
# Start: python main.py
```

Frontend config changes require browser refresh.

---

## Production Deployment (Beyond Scope)

For production deployment, consider:

1. **Valid SSL certificates** (Let's Encrypt)
2. **Reverse proxy** (Nginx, Caddy)
3. **Process manager** (systemd, PM2, Docker)
4. **Database backup** (pg_dump cron job)
5. **Rate limiting** (Nginx, FastAPI middleware)
6. **Monitoring** (Prometheus, Grafana)
7. **Liveness detection** (anti-spoofing)
8. **GDPR compliance** (data retention policies)

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor attendance statistics
- Check for errors in logs

**Weekly:**
- Backup database:
```bash
pg_dump -U postgres attendance_system > backup_$(date +%Y%m%d).sql
```

**Monthly:**
- Review and export historical data
- Clean up old logs
- Update dependencies:
```bash
pip install --upgrade -r requirements.txt
```

**Yearly:**
- Regenerate SSL certificates:
```bash
cd certs
python generate_certs.py
```

### Backup and Restore

**Backup:**
```bash
pg_dump -U postgres attendance_system > backup.sql
```

**Restore:**
```bash
psql -U postgres attendance_system < backup.sql
```

---

## Uninstallation

### 1. Stop Services

```bash
# Stop backend: Ctrl+C in terminal
# Stop frontend: Ctrl+C in terminal
```

### 2. Remove Virtual Environment

```bash
cd backend
rm -rf venv  # Mac/Linux
Remove-Item -Recurse -Force venv  # Windows
```

### 3. Drop Database

```bash
psql -U postgres
DROP DATABASE attendance_system;
\q
```

### 4. Remove Files

```bash
cd ..
rm -rf "attendance system"  # Mac/Linux
Remove-Item -Recurse -Force "attendance system"  # Windows
```

---

## Support

For issues or questions:
1. Check this documentation
2. Review [API.md](./API.md) for API details
3. Review [ARCFACE_IMPLEMENTATION.md](./ARCFACE_IMPLEMENTATION.md) for face recognition details
4. Check backend logs for error messages
5. Contact your system administrator

---

**Setup Version:** 1.0.0  
**Last Updated:** December 20, 2025

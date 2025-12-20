# Quick Troubleshooting Guide

Quick fixes for common issues. For detailed troubleshooting, see [docs/SETUP.md](docs/SETUP.md).

## 🔴 Backend Issues

### "Database connection failed"
```bash
# Check PostgreSQL status
psql -U postgres -c "SELECT 1"

# Restart PostgreSQL
# Windows:
Restart-Service postgresql
# Mac:
brew services restart postgresql
# Linux:
sudo systemctl restart postgresql
```

### "ModuleNotFoundError"
```bash
# Activate virtual environment
cd backend
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill -9 <PID>
```

## 🔴 Frontend Issues

### "Failed to load models"
- Check internet connection (models download from CDN)
- Try different browser (Chrome recommended)
- Clear browser cache: Ctrl+Shift+Delete
- Check console for specific error: F12 → Console

### "Webcam not accessible"
- Grant camera permission in browser settings
- Close other apps using webcam
- Verify HTTPS (camera requires secure context)
- Try: chrome://settings/content/camera

### "Certificate error"
**Expected with self-signed certificates**

1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)"
3. Or install certificate as trusted (see docs/SETUP.md)

## 🔴 Face Recognition Issues

### "No face detected"
- Improve lighting (face well-lit)
- Position face in center of frame
- Move closer to camera
- Remove glasses (if causing issues)
- Ensure face is clearly visible

### "Face verification failed"
- Re-register with better lighting
- Ensure consistent appearance
- Lower threshold temporarily:
  ```bash
  # In backend/.env
  SIMILARITY_THRESHOLD=0.7
  MIN_MATCHES_REQUIRED=1
  ```
- Restart backend after config change

### "Attendance already marked"
**Expected: once per day**

To test repeatedly (development only):
```sql
-- Delete today's attendance
psql -U postgres -d attendance_system
DELETE FROM attendance WHERE student_id='1RV23CS001' AND date=CURRENT_DATE;
```

## 🔴 Database Issues

### "Table does not exist"
```bash
cd backend
python init_db.py
```

### "Reset database"
**CAUTION: Deletes all data**
```bash
cd backend
python init_db.py --drop
```

### "Check database contents"
```sql
psql -U postgres -d attendance_system

-- View students
SELECT * FROM students;

-- View embeddings
SELECT student_id, embedding_index FROM face_embeddings;

-- View attendance
SELECT * FROM attendance WHERE date=CURRENT_DATE;
```

## 🔴 Admin Panel Issues

### "Unauthorized / Invalid credentials"
- Check username/password in `backend/.env`
- Default username: `admin`
- Verify no trailing spaces in credentials

### "No data in table"
- Register at least one student
- Mark attendance for today
- Check date filter (defaults to today)

### "CSV export empty"
- Verify date range has attendance records
- Check browser downloads folder
- Try shorter date range

## 🔴 Configuration Issues

### "Where is my .env file?"
```bash
cd backend
cp .env.example .env
notepad .env  # Windows
nano .env     # Mac/Linux
```

### "What are default credentials?"
```bash
# View admin credentials
cat backend/.env | grep ADMIN
```

### "How to change threshold?"
```bash
# Edit backend/.env
SIMILARITY_THRESHOLD=0.8  # Change this (0.0 to 1.0)
MIN_MATCHES_REQUIRED=2    # Change this (1 to 5)

# Restart backend
```

## 🔧 Quick Fixes

### Restart Everything
```bash
# Stop: Ctrl+C in both terminals

# Backend:
cd backend
.\venv\Scripts\Activate.ps1  # Windows
python main.py

# Frontend (new terminal):
cd frontend
http-server -p 8001 -S -C ../certs/localhost.crt -K ../certs/localhost.key
```

### Clear Browser Data
1. Press Ctrl+Shift+Delete
2. Select "Cookies" and "Cached images"
3. Clear data
4. Reload page

### Verify Services
```bash
# Backend health
curl -k https://localhost:8000

# Frontend (in browser)
https://localhost:8001
```

## 📋 Checklist for Fresh Setup

- [ ] PostgreSQL installed and running
- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed (for http-server)
- [ ] Database created: `attendance_system`
- [ ] Backend `.env` file configured
- [ ] Virtual environment created and activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Database initialized: `python init_db.py`
- [ ] SSL certificates generated: `python certs/generate_certs.py`
- [ ] Backend running: https://localhost:8000
- [ ] Frontend running: https://localhost:8001
- [ ] Camera permission granted in browser
- [ ] Certificate warning bypassed

## 🆘 Emergency Reset

If everything is broken:

```bash
# 1. Stop all services (Ctrl+C)

# 2. Reset database
psql -U postgres -c "DROP DATABASE IF EXISTS attendance_system;"
psql -U postgres -c "CREATE DATABASE attendance_system;"

# 3. Reinitialize
cd backend
python init_db.py

# 4. Regenerate certificates
cd ../certs
python generate_certs.py

# 5. Restart services
cd ../backend
python main.py
# In new terminal:
cd ../frontend
http-server -p 8001 -S -C ../certs/localhost.crt -K ../certs/localhost.key
```

## 📞 Get Help

1. Check [docs/SETUP.md](docs/SETUP.md) for detailed instructions
2. Check [docs/API.md](docs/API.md) for API issues
3. Check backend logs for error messages
4. Check browser console (F12) for frontend errors
5. Check PostgreSQL logs for database errors

## 🔍 Debug Mode

### Backend verbose logging
```python
# In backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend console logging
```javascript
// In browser console (F12)
localStorage.debug = '*';
```

### Database query logging
```python
# In backend/database.py
engine = create_engine(config.DATABASE_URL, echo=True)
```

## ✅ Verification Commands

```bash
# Python version
python --version  # Should be 3.9+

# PostgreSQL version
psql --version  # Should be 13+

# Node version
node --version  # Should be 16+

# Check database
psql -U postgres -d attendance_system -c "\dt"

# Check backend
curl -k https://localhost:8000

# Check frontend
curl -k https://localhost:8001
```

---

**Still having issues?**

Review the complete documentation:
- [README.md](README.md) - System overview
- [docs/SETUP.md](docs/SETUP.md) - Detailed setup guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project details

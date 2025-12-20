# Classroom Attendance System with Face Recognition

A secure, browser-based facial recognition attendance system using ArcFace embeddings.

## 🎯 System Overview

- **Backend**: FastAPI @ https://localhost:8000
- **Frontend**: Static HTML/JS @ https://localhost:8001
- **Database**: PostgreSQL
- **Face Recognition**: ArcFace (browser-based using TensorFlow.js)
- **Platform**: Laptop browsers only

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Browser       │ HTTPS   │   Backend        │  SQL    │ PostgreSQL  │
│  (localhost:    │◄───────►│  (localhost:     │◄───────►│             │
│     8001)       │         │     8000)        │         │             │
│                 │         │                  │         │             │
│ • ArcFace.js    │         │ • FastAPI        │         │ • Students  │
│ • Webcam        │         │ • Cosine Sim     │         │ • Embeddings│
│ • Embeddings    │         │ • Auth Logic     │         │ • Attendance│
└─────────────────┘         └──────────────────┘         └─────────────┘
```

## 📋 Features

### Student Features
- **Registration**: Capture 5 facial images → Generate 5 ArcFace embeddings
- **Attendance Marking**: Live face capture → Backend verification
- **Once-per-day**: Students can only mark attendance once per calendar day

### Admin Features
- View attendance by date
- View attendance by student
- Export attendance as CSV
- Secure access (basic authentication)

### Security
- HTTPS-only communication (self-signed certs)
- Configurable similarity thresholds
- Multi-embedding verification (default: 2 out of 5 matches)

## 🚀 Quick Start

### Prerequisites

```bash
# Required software
- Python 3.9+
- PostgreSQL 13+
- Node.js 16+ (for serving frontend)
- Modern browser (Chrome/Edge recommended)
```

### 1. Database Setup

```sql
-- Create database
CREATE DATABASE attendance_system;

-- Run migrations
cd backend
python init_db.py
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run backend
python main.py
# Server starts at https://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend
# Install http-server globally if not already installed
npm install -g http-server

# Run with HTTPS
http-server -p 8001 -S -C ../certs/localhost.crt -K ../certs/localhost.key
# Frontend runs at https://localhost:8001
```

### 4. Generate HTTPS Certificates (First Time Only)

```bash
cd certs
python generate_certs.py
```

## 📖 Usage Guide

### For Students

#### Registration
1. Navigate to https://localhost:8001
2. Click "Register"
3. Enter your student ID (format: 1RV23CSXXX, where XXX is 001-420)
4. Allow webcam access
5. Position your face in the frame
6. System captures 5 images automatically
7. Wait for "Registration Successful" message

#### Mark Attendance
1. Navigate to https://localhost:8001
2. Click "Mark Attendance"
3. System retrieves your ID from cookies
4. Allow webcam access
5. Position your face in the frame
6. Click "Verify" to capture and submit
7. Wait for verification result

### For Admins

1. Navigate to https://localhost:8001/admin.html
2. Enter admin credentials
   - Username: `admin`
   - Password: (see backend/.env file)
3. View attendance statistics
4. Filter by date or student
5. Export as CSV

## ⚙️ Configuration

### Backend Configuration (backend/config.py)

```python
# Face verification parameters
SIMILARITY_THRESHOLD = 0.8      # Cosine similarity threshold (0-1)
MIN_MATCHES_REQUIRED = 2         # Minimum matches out of 5 embeddings

# Database
DATABASE_URL = "postgresql://user:password@localhost/attendance_system"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your_secure_password"

# Student ID validation
STUDENT_ID_PATTERN = r"^1RV23CS(0[0-9]{2}|[1-3][0-9]{2}|4[0-1][0-9]|420)$"
```

### Frontend Configuration (frontend/config.js)

```javascript
const CONFIG = {
    BACKEND_URL: 'https://localhost:8000',
    NUM_REGISTRATION_IMAGES: 5,
    CAPTURE_INTERVAL_MS: 1000,
    VIDEO_WIDTH: 640,
    VIDEO_HEIGHT: 480
};
```

## 🗄️ Database Schema

### students
| Column | Type | Constraints |
|--------|------|-------------|
| student_id | VARCHAR(20) | PRIMARY KEY |
| registered_at | TIMESTAMP | NOT NULL |
| name | VARCHAR(255) | NULLABLE |

### face_embeddings
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| student_id | VARCHAR(20) | FOREIGN KEY → students |
| embedding_index | INTEGER | 1-5 |
| embedding_vector | FLOAT[] | 512 dimensions |
| created_at | TIMESTAMP | NOT NULL |

**Unique constraint**: (student_id, embedding_index)

### attendance
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| student_id | VARCHAR(20) | FOREIGN KEY → students |
| date | DATE | NOT NULL |
| marked_at | TIMESTAMP | NOT NULL |
| present | BOOLEAN | DEFAULT TRUE |

**Unique constraint**: (student_id, date)

## 🔌 API Documentation

### Registration

**Endpoint**: `POST /api/register`

**Request**:
```json
{
    "student_id": "1RV23CS288",
    "embeddings": [
        [0.123, 0.456, ...],  // 512-dim vector
        [0.234, 0.567, ...],
        [0.345, 0.678, ...],
        [0.456, 0.789, ...],
        [0.567, 0.890, ...]
    ]
}
```

**Response (Success)**:
```json
{
    "status": "success",
    "message": "Student registered successfully",
    "student_id": "1RV23CS288"
}
```

**Response (Failure)**:
```json
{
    "status": "error",
    "message": "Student already registered"
}
```

### Attendance Verification

**Endpoint**: `POST /api/verify`

**Request**:
```json
{
    "student_id": "1RV23CS288",
    "live_embedding": [0.123, 0.456, ...]  // 512-dim vector
}
```

**Response (Success)**:
```json
{
    "status": "ok",
    "message": "Attendance marked successfully",
    "similarity_scores": [0.85, 0.92, 0.78, 0.88, 0.81],
    "matches": 4
}
```

**Response (Already Marked)**:
```json
{
    "status": "already_marked",
    "message": "Attendance already marked for today"
}
```

**Response (Verification Failed)**:
```json
{
    "status": "failed",
    "message": "Biometric verification failed",
    "similarity_scores": [0.65, 0.70, 0.72, 0.68, 0.71],
    "matches": 0
}
```

### Admin - Get Attendance

**Endpoint**: `GET /api/admin/attendance?date=2025-12-20`

**Headers**: `Authorization: Basic base64(username:password)`

**Response**:
```json
{
    "date": "2025-12-20",
    "total_students": 420,
    "present": 385,
    "absent": 35,
    "attendance": [
        {"student_id": "1RV23CS001", "present": true, "marked_at": "2025-12-20T09:15:30"},
        {"student_id": "1RV23CS002", "present": true, "marked_at": "2025-12-20T09:16:45"}
    ]
}
```

### Admin - Export CSV

**Endpoint**: `GET /api/admin/export?start_date=2025-12-01&end_date=2025-12-20`

**Headers**: `Authorization: Basic base64(username:password)`

**Response**: CSV file download

## 🧠 ArcFace Browser Pipeline

### Model Selection

We use **FaceNet-based ArcFace** model via TensorFlow.js:
- Model: `facenet` (128 or 512 dimensions)
- Alternative: ONNX Runtime Web with custom ArcFace model

### Pipeline Steps

1. **Face Detection**: 
   - Uses TensorFlow.js face-detection model
   - Detects face bounding box in video frame

2. **Face Alignment**:
   - Extracts face region with padding
   - Resizes to model input size (160×160 for FaceNet)

3. **Embedding Generation**:
   - Passes aligned face through ArcFace model
   - Outputs 512-dimensional embedding vector
   - Normalizes vector (L2 normalization)

4. **Storage/Transmission**:
   - Serializes as Float32Array → JSON
   - Sends via HTTPS POST

### Why Browser-Based?

- **Privacy**: Raw images never leave the browser
- **Efficiency**: Reduces server compute load
- **Bandwidth**: Only embeddings (2KB) transmitted, not images (~100KB)
- **Security**: HTTPS encryption for embedding transport

## 🔒 Security Considerations

### Implemented
- HTTPS-only communication
- Cookie-based session (HttpOnly, Secure flags)
- Basic authentication for admin
- SQL injection protection (parameterized queries)
- Student ID format validation

### Out of Scope (Documented Limitations)
- ❌ Presentation Attack Detection (PAD/anti-spoofing)
- ❌ Network-level security (firewall rules)
- ❌ Mobile browser support
- ❌ Large-scale concurrency (built for classroom use)
- ❌ Deep learning-based liveness detection

## 🎛️ Configurable Parameters

| Parameter | Location | Default | Description |
|-----------|----------|---------|-------------|
| `SIMILARITY_THRESHOLD` | backend/config.py | 0.8 | Minimum cosine similarity (0-1) |
| `MIN_MATCHES_REQUIRED` | backend/config.py | 2 | Required matches out of 5 |
| `NUM_REGISTRATION_IMAGES` | frontend/config.js | 5 | Number of embeddings to capture |
| `CAPTURE_INTERVAL_MS` | frontend/config.js | 1000 | Delay between captures (ms) |
| `ADMIN_USERNAME` | backend/.env | admin | Admin panel username |
| `ADMIN_PASSWORD` | backend/.env | - | Admin panel password |

## 📝 Engineering Decisions & Assumptions

1. **5 Embeddings per Student**: 
   - Captures variation in pose, lighting, expression
   - 2/5 match requirement balances security vs usability

2. **Browser-based ArcFace**:
   - Privacy-preserving (images don't leave device)
   - Reduces backend load
   - TensorFlow.js chosen for ease of deployment

3. **PostgreSQL over NoSQL**:
   - Relational structure fits attendance matrix
   - ACID compliance for attendance records
   - Native array support for embeddings

4. **Cosine Similarity**:
   - Standard metric for normalized embeddings
   - Efficient computation (O(n))
   - Range [0,1] easy to configure

5. **Once-per-day Rule**:
   - Uses (student_id, date) unique constraint
   - No time-window complexity
   - Simple to audit

6. **Self-signed Certs**:
   - Local development acceptable
   - Browser warnings expected
   - Production would use Let's Encrypt

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Test registration
curl -k -X POST https://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"student_id": "1RV23CS001", "embeddings": [[...], [...], [...], [...], [...]]}'

# Test verification
curl -k -X POST https://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"student_id": "1RV23CS001", "live_embedding": [...]}'
```

## 🐛 Troubleshooting

### "Failed to load model"
- Check internet connection (model downloads from CDN)
- Verify TensorFlow.js CDN is accessible
- Try clearing browser cache

### "Database connection failed"
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in backend/.env
- Ensure database exists: `psql -l | grep attendance_system`

### "Webcam not accessible"
- Grant browser camera permissions
- Close other apps using webcam
- Try different browser (Chrome recommended)

### "Certificate error"
- Expected with self-signed certs
- Click "Advanced" → "Proceed to localhost" in browser
- For production, use valid SSL certificate

## 📦 Dependencies

### Backend (Python)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
numpy==1.24.3
pydantic==2.5.0
python-multipart==0.0.6
```

### Frontend (JavaScript)
```
@tensorflow/tfjs@4.13.0
@tensorflow-models/facemesh@0.0.5
(Loaded via CDN)
```

## 📄 License

MIT License - Educational/Internal Use

## 👥 Support

For issues or questions, contact your system administrator.

---

**Last Updated**: December 20, 2025  
**Version**: 1.0.0

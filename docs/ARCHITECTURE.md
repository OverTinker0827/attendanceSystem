# Architecture Documentation

## System Architecture Overview

The Attendance System is designed as a **three-tier architecture** with separation of concerns:

```
┌──────────────────────────────────────────────────────────────┐
│                      Presentation Layer                       │
│                   (Browser-Based Frontend)                    │
├──────────────────────────────────────────────────────────────┤
│  • HTML/CSS/JavaScript                                        │
│  • TensorFlow.js (Face Recognition)                          │
│  • Webcam Integration                                         │
│  • HTTPS Client (Fetch API)                                   │
└──────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌──────────────────────────────────────────────────────────────┐
│                      Application Layer                        │
│                     (FastAPI Backend)                         │
├──────────────────────────────────────────────────────────────┤
│  • REST API Endpoints                                         │
│  • Face Verification Logic                                    │
│  • Authentication & Authorization                             │
│  • Business Rules Enforcement                                 │
└──────────────────────────────────────────────────────────────┘
                            ↓ SQL
┌──────────────────────────────────────────────────────────────┐
│                        Data Layer                             │
│                     (PostgreSQL Database)                     │
├──────────────────────────────────────────────────────────────┤
│  • Students                                                   │
│  • Face Embeddings                                            │
│  • Attendance Records                                         │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (Presentation Layer)

**Technology Stack:**
- HTML5
- CSS3 (Modern responsive design)
- Vanilla JavaScript (ES6+)
- TensorFlow.js 4.13.0
- BlazeFace (Face detection)

**Key Modules:**

#### `index.html`
- Main entry point for students
- Registration and attendance UI
- Video streaming interface

#### `admin.html`
- Admin dashboard
- Attendance viewing and filtering
- CSV export functionality

#### `app.js`
- Registration flow orchestration
- Attendance marking flow
- Webcam management
- Event handling

#### `utils.js`
- Face detection (BlazeFace)
- Embedding generation
- API communication
- Cookie management

#### `config.js`
- Frontend configuration
- Backend URL
- Model settings
- UI messages

#### `styles.css`
- Modern, gradient-based design
- Responsive layout
- Accessibility features

**Data Flow:**

```
User Action → Event Handler → Webcam Capture → Face Detection
    ↓
Embedding Generation → API Call → Backend
    ↓
Response Handling → UI Update → User Feedback
```

### 2. Backend (Application Layer)

**Technology Stack:**
- Python 3.9+
- FastAPI 0.104.1
- Uvicorn (ASGI server)
- SQLAlchemy 2.0 (ORM)
- NumPy (Vector operations)
- Pandas (Data export)

**Key Modules:**

#### `main.py`
- FastAPI application instance
- Route definitions
- Middleware configuration
- CORS setup
- Server startup

**Endpoints:**
- `POST /api/register` - Student registration
- `POST /api/verify` - Attendance verification
- `GET /api/admin/attendance` - View attendance
- `GET /api/admin/export` - Export CSV
- `GET /api/admin/stats` - System statistics

#### `database.py`
- SQLAlchemy models
- Database connection
- Session management
- Schema definitions

**Models:**
- `Student` - Student records
- `FaceEmbedding` - Face embeddings (5 per student)
- `Attendance` - Attendance matrix

#### `config.py`
- Environment variable loading
- Configuration validation
- Student ID pattern
- Thresholds

#### `utils.py`
- Cosine similarity calculation
- Face verification logic
- Basic authentication
- Data validation

**Data Flow:**

```
API Request → Request Validation → Business Logic
    ↓
Database Query → Processing → Response Formatting
    ↓
JSON Response → Client
```

### 3. Database (Data Layer)

**Technology:** PostgreSQL 13+

**Schema Design:**

#### Students Table
```sql
CREATE TABLE students (
    student_id VARCHAR(20) PRIMARY KEY,
    registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    name VARCHAR(255)
);
```

#### Face Embeddings Table
```sql
CREATE TABLE face_embeddings (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES students(student_id) ON DELETE CASCADE,
    embedding_index INTEGER NOT NULL CHECK (embedding_index BETWEEN 1 AND 5),
    embedding_vector FLOAT[] NOT NULL,  -- 512 dimensions
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, embedding_index)
);
```

#### Attendance Table
```sql
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES students(student_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    marked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    present BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(student_id, date)  -- Once per day constraint
);
```

**Relationships:**
- Students 1:N Face Embeddings
- Students 1:N Attendance
- Cascade delete on student removal

**Indexes:**
- Primary keys: Automatic B-tree indexes
- Foreign keys: Automatic indexes
- Unique constraints: Automatic unique indexes
- Additional: `(student_id, date)` on attendance

## Security Architecture

### Transport Security

**HTTPS Everywhere:**
- Backend: `https://localhost:8000`
- Frontend: `https://localhost:8001`
- Self-signed certificates for development
- TLS 1.2+ encryption

### Authentication & Authorization

**Student Authentication:**
- Cookie-based session
- Student ID stored in secure cookie
- HttpOnly flag (prevents XSS)
- Secure flag (HTTPS only)
- SameSite=Strict (CSRF protection)

**Admin Authentication:**
- HTTP Basic Authentication
- Base64 encoded credentials
- Constant-time comparison (`secrets.compare_digest`)
- No token expiry (session-based)

### Data Security

**Embedding Protection:**
- One-way transformation (face → embedding)
- Cannot reconstruct face from embedding
- Normalized vectors (L2 norm = 1)
- Stored as PostgreSQL array type

**Input Validation:**
- Pydantic models for request validation
- Student ID regex pattern
- Embedding dimension check
- NaN/Infinity detection
- SQL injection prevention (parameterized queries)

### CORS Policy

```python
ALLOWED_ORIGINS = [
    "https://localhost:8001",
    "https://127.0.0.1:8001"
]
```

Restricts API access to authorized origins only.

## Scalability Considerations

### Current Limitations

**Designed for classroom scale:**
- 420 students max
- Single server instance
- No load balancing
- No caching layer
- Synchronous processing

**Performance:**
- Registration: ~1-2 seconds
- Verification: ~200-500ms
- Database queries: <50ms
- Concurrent users: ~50

### Scaling Strategies (Future)

**Horizontal Scaling:**
- Deploy multiple backend instances
- Load balancer (Nginx, HAProxy)
- Shared PostgreSQL database
- Session affinity for admin

**Database Optimization:**
- Connection pooling (pgBouncer)
- Read replicas for analytics
- Partitioning attendance by date
- Vector similarity indexes (pgvector)

**Caching:**
- Redis for embeddings cache
- CDN for frontend assets
- API response caching

**Asynchronous Processing:**
- Celery for background tasks
- RabbitMQ/Redis message queue
- Batch verification

## Deployment Architecture

### Development (Current)

```
Developer Laptop
├── Backend (localhost:8000)
│   ├── FastAPI
│   └── SQLAlchemy
├── Frontend (localhost:8001)
│   └── Static files
└── PostgreSQL (localhost:5432)
    └── Database
```

### Production (Recommended)

```
┌─────────────────────────────────────────┐
│             Load Balancer                │
│              (Nginx/Caddy)               │
└────────────────┬────────────────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
┌────▼─────┐         ┌───────▼────┐
│ Frontend │         │  Backend   │
│  (CDN)   │         │ (Gunicorn) │
└──────────┘         └────┬───────┘
                          │
                    ┌─────▼─────┐
                    │PostgreSQL │
                    │ (Primary) │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │PostgreSQL │
                    │ (Replica) │
                    └───────────┘
```

**Components:**
- **Reverse Proxy:** Nginx/Caddy for SSL termination, compression, caching
- **Frontend:** Served from CDN (Cloudflare, AWS CloudFront)
- **Backend:** Gunicorn with multiple workers, systemd service
- **Database:** Primary-replica setup, automated backups
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK stack (Elasticsearch, Logstash, Kibana)

## Monitoring & Observability

### Metrics to Track

**Application Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Verification success rate
- Daily registrations

**System Metrics:**
- CPU usage
- Memory usage
- Disk I/O
- Network bandwidth

**Database Metrics:**
- Query latency
- Connection pool usage
- Lock waits
- Table sizes

### Logging Strategy

**Backend Logging:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

**Log Levels:**
- DEBUG: Development debugging
- INFO: Normal operation (registration, verification)
- WARNING: Recoverable issues (low similarity scores)
- ERROR: Failures (database errors, API errors)
- CRITICAL: System failures

**Log Rotation:**
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## Disaster Recovery

### Backup Strategy

**Database Backups:**
```bash
# Daily automated backup
pg_dump -U postgres attendance_system > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_$(date +%Y%m%d).sql

# Upload to cloud storage (S3, Google Cloud Storage)
aws s3 cp backup_*.sql.gz s3://backups/
```

**Configuration Backups:**
- Git repository for code
- Encrypted `.env` file backup
- SSL certificate backup

**Recovery Time Objective (RTO):** 1 hour  
**Recovery Point Objective (RPO):** 24 hours

### High Availability

**Database:**
- Primary-replica setup
- Automatic failover (Patroni, Repmgr)
- Point-in-time recovery (WAL archiving)

**Application:**
- Multiple backend instances
- Health check endpoints
- Automatic restart (systemd, Docker)

## Future Enhancements

### Phase 2 Features

1. **Multi-Factor Authentication**
   - OTP via email/SMS
   - Liveness detection (blink, head turn)
   - Geolocation verification

2. **Advanced Analytics**
   - Attendance trends
   - Predictive analytics
   - Student engagement scoring

3. **Mobile Support**
   - Progressive Web App (PWA)
   - Native mobile apps (React Native)
   - Push notifications

4. **Integration**
   - University management systems
   - Calendar integration (Google Calendar)
   - Email notifications
   - SMS alerts

5. **AI Enhancements**
   - True ArcFace model (not FaceNet)
   - Anti-spoofing (presentation attack detection)
   - Mask detection
   - Multi-face scenarios

### Technical Debt

- Add comprehensive test suite (pytest, Jest)
- API rate limiting
- Request throttling
- Webhook support
- GraphQL API option
- WebSocket for real-time updates
- Docker containerization
- Kubernetes orchestration

---

**Architecture Version:** 1.0.0  
**Last Updated:** December 20, 2025  
**Author:** Senior Full-Stack Engineer

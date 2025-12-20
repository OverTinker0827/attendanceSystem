# API Documentation

Complete API reference for the Attendance System backend.

## Base URL

```
https://localhost:8000
```

## Authentication

Admin endpoints require HTTP Basic Authentication.

**Header Format:**
```
Authorization: Basic base64(username:password)
```

**Default Credentials:**
- Username: `admin`
- Password: See `backend/.env` file

---

## Student Endpoints

### 1. Register Student

Register a new student with face embeddings.

**Endpoint:** `POST /api/register`

**Request Body:**
```json
{
    "student_id": "1RV23CS288",
    "embeddings": [
        [0.123, 0.456, ...],  // Array of 512 floats
        [0.234, 0.567, ...],
        [0.345, 0.678, ...],
        [0.456, 0.789, ...],
        [0.567, 0.890, ...]
    ]
}
```

**Validation Rules:**
- `student_id`: Must match pattern `1RV23CS001` to `1RV23CS420`
- `embeddings`: Must be exactly 5 arrays
- Each embedding: Must be exactly 512 floats
- No NaN or Infinity values allowed

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Student registered successfully",
    "student_id": "1RV23CS288"
}
```

**Error Responses:**

*400 - Student Already Registered:*
```json
{
    "status": "error",
    "message": "Student already registered. Use overwrite option if you want to re-register."
}
```

*400 - Invalid Student ID:*
```json
{
    "detail": {
        "status": "error",
        "message": "Invalid student ID format. Expected: ^1RV23CS(0[0-9]{2}|[1-3][0-9]{2}|4[0-1][0-9]|420)$"
    }
}
```

*422 - Validation Error:*
```json
{
    "detail": [
        {
            "loc": ["body", "embeddings"],
            "msg": "Must provide exactly 5 embeddings, got 3",
            "type": "value_error"
        }
    ]
}
```

---

### 2. Verify Attendance

Verify student identity and mark attendance.

**Endpoint:** `POST /api/verify`

**Request Body:**
```json
{
    "student_id": "1RV23CS288",
    "live_embedding": [0.123, 0.456, ...]  // Array of 512 floats
}
```

**Validation Rules:**
- `student_id`: Must match pattern
- `live_embedding`: Must be exactly 512 floats
- No NaN or Infinity values allowed

**Success Response (200) - Verified:**
```json
{
    "status": "ok",
    "message": "Attendance marked successfully",
    "similarity_scores": [0.85, 0.92, 0.78, 0.88, 0.81],
    "matches": 4
}
```

**Success Response (200) - Already Marked:**
```json
{
    "status": "already_marked",
    "message": "Attendance already marked for today",
    "similarity_scores": null,
    "matches": null
}
```

**Success Response (200) - Verification Failed:**
```json
{
    "status": "failed",
    "message": "Biometric verification failed",
    "similarity_scores": [0.65, 0.70, 0.72, 0.68, 0.71],
    "matches": 0
}
```

**Error Responses:**

*404 - Student Not Registered:*
```json
{
    "detail": {
        "status": "error",
        "message": "Student not registered. Please register first."
    }
}
```

*500 - Incomplete Registration:*
```json
{
    "detail": {
        "status": "error",
        "message": "Incomplete registration data. Please re-register."
    }
}
```

**Verification Logic:**
1. Retrieve 5 stored embeddings for student
2. Calculate cosine similarity between live embedding and each stored embedding
3. Count how many scores ≥ `SIMILARITY_THRESHOLD` (default: 0.8)
4. Verify if matches ≥ `MIN_MATCHES_REQUIRED` (default: 2)
5. Mark attendance only if verified and not already marked today

---

## Admin Endpoints

All admin endpoints require Basic Authentication.

### 3. Get Attendance

Retrieve attendance records for a specific date or student.

**Endpoint:** `GET /api/admin/attendance`

**Headers:**
```
Authorization: Basic <credentials>
```

**Query Parameters:**
- `date` (optional): Date in `YYYY-MM-DD` format (defaults to today)
- `student_id` (optional): Filter by specific student ID

**Examples:**
```
GET /api/admin/attendance
GET /api/admin/attendance?date=2025-12-20
GET /api/admin/attendance?date=2025-12-20&student_id=1RV23CS288
```

**Success Response (200):**
```json
{
    "date": "2025-12-20",
    "total_students": 420,
    "present": 385,
    "absent": 35,
    "attendance": [
        {
            "student_id": "1RV23CS001",
            "present": true,
            "marked_at": "2025-12-20T09:15:30.123456"
        },
        {
            "student_id": "1RV23CS002",
            "present": true,
            "marked_at": "2025-12-20T09:16:45.789012"
        }
    ]
}
```

**Error Responses:**

*400 - Invalid Date Format:*
```json
{
    "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

*401 - Unauthorized:*
```json
{
    "detail": "Unauthorized"
}
```

---

### 4. Export Attendance CSV

Export attendance data as CSV file.

**Endpoint:** `GET /api/admin/export`

**Headers:**
```
Authorization: Basic <credentials>
```

**Query Parameters:**
- `start_date` (optional): Start date in `YYYY-MM-DD` format (defaults to today)
- `end_date` (optional): End date in `YYYY-MM-DD` format (defaults to today)

**Examples:**
```
GET /api/admin/export
GET /api/admin/export?start_date=2025-12-01&end_date=2025-12-31
```

**Success Response (200):**
```
Content-Type: text/csv
Content-Disposition: attachment; filename=attendance_2025-12-01_2025-12-31.csv

student_id,date,present,marked_at
1RV23CS001,2025-12-01,True,2025-12-01 09:15:30
1RV23CS002,2025-12-01,True,2025-12-01 09:16:45
...
```

**CSV Format:**
| Column | Type | Description |
|--------|------|-------------|
| student_id | string | Student ID |
| date | date | Attendance date (YYYY-MM-DD) |
| present | boolean | True if present |
| marked_at | datetime | Timestamp of attendance mark |

---

### 5. Get Statistics

Get overall system statistics.

**Endpoint:** `GET /api/admin/stats`

**Headers:**
```
Authorization: Basic <credentials>
```

**Success Response (200):**
```json
{
    "total_registered_students": 420,
    "total_attendance_records": 15750,
    "today_attendance": 385,
    "config": {
        "similarity_threshold": 0.8,
        "min_matches_required": 2,
        "num_embeddings": 5,
        "embedding_dimension": 512,
        "student_id_pattern": "^1RV23CS(0[0-9]{2}|[1-3][0-9]{2}|4[0-1][0-9]|420)$"
    }
}
```

---

## Health Check Endpoints

### 6. Root Health Check

Basic service status check.

**Endpoint:** `GET /`

**Success Response (200):**
```json
{
    "status": "ok",
    "service": "Attendance System Backend",
    "version": "1.0.0"
}
```

---

### 7. Detailed Health Check

Detailed health check with configuration.

**Endpoint:** `GET /api/health`

**Success Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2025-12-20T10:30:45.123456",
    "config": {
        "similarity_threshold": 0.8,
        "min_matches_required": 2,
        "num_embeddings": 5,
        "embedding_dimension": 512,
        "student_id_pattern": "^1RV23CS(0[0-9]{2}|[1-3][0-9]{2}|4[0-1][0-9]|420)$"
    }
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
    "detail": {
        "status": "error",
        "message": "Descriptive error message"
    }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |

---

## Configuration Parameters

Backend configuration is managed via environment variables (see `backend/.env`).

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `SIMILARITY_THRESHOLD` | 0.8 | 0.0 - 1.0 | Minimum cosine similarity for face match |
| `MIN_MATCHES_REQUIRED` | 2 | 1 - 5 | Required matches out of 5 embeddings |
| `DATABASE_URL` | - | - | PostgreSQL connection string |
| `ADMIN_USERNAME` | admin | - | Admin panel username |
| `ADMIN_PASSWORD` | - | - | Admin panel password |

---

## Rate Limiting

Currently **not implemented**. Consider adding rate limiting for production:

- Registration: 5 requests per student per hour
- Verification: 10 requests per student per day
- Admin: 100 requests per minute

---

## CORS Configuration

Allowed origins for cross-origin requests:
- `https://localhost:8001`
- `https://127.0.0.1:8001`

To add more origins, update `config.py`:
```python
ALLOWED_ORIGINS = [
    "https://localhost:8001",
    "https://your-domain.com"
]
```

---

## Testing with cURL

### Register Student
```bash
curl -k -X POST https://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "1RV23CS001",
    "embeddings": [[...], [...], [...], [...], [...]]
  }'
```

### Verify Attendance
```bash
curl -k -X POST https://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "1RV23CS001",
    "live_embedding": [...]
  }'
```

### Get Attendance (Admin)
```bash
curl -k -X GET "https://localhost:8000/api/admin/attendance?date=2025-12-20" \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)"
```

### Export CSV (Admin)
```bash
curl -k -X GET "https://localhost:8000/api/admin/export?start_date=2025-12-01&end_date=2025-12-20" \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
  --output attendance.csv
```

**Note:** The `-k` flag bypasses SSL certificate verification for self-signed certificates.

---

## Postman Collection

Import this JSON into Postman for easy testing:

```json
{
    "info": {
        "name": "Attendance System API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Register Student",
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "url": "https://localhost:8000/api/register",
                "body": {
                    "mode": "raw",
                    "raw": "{\n  \"student_id\": \"1RV23CS001\",\n  \"embeddings\": [[...], [...], [...], [...], [...]]\n}"
                }
            }
        }
    ]
}
```

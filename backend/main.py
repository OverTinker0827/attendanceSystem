"""
Main FastAPI application for the attendance system backend.
Implements registration, verification with IP subnet checking, and admin APIs.
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime, time
import uvicorn
import io
import pandas as pd
import ipaddress
from zoneinfo import ZoneInfo
ist = ZoneInfo("Asia/Kolkata")
from database import (
    get_db, Student, FaceEmbedding, Attendance, Classroom, 
    ClassSchedule, init_database
)
from config import config
from utils import (
    verify_face,
    validate_embedding,
    validate_embeddings_list,
    verify_basic_auth,
    format_similarity_scores,
    check_subnet_match,
)

# Initialize FastAPI app
app = FastAPI(
    title="Classroom Attendance System API",
    description="Face recognition-based attendance system with IP verification",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models - Frontend Compatible
# ============================================================================

class RegistrationRequest(BaseModel):
    """Request model for student registration"""
    student_id: str = Field(..., description="Student ID (USN)")
    embeddings: List[List[float]] = Field(..., description="List of 5 face embeddings")

    @validator("student_id")
    def validate_student_id(cls, v):
        if not config.validate_student_id(v):
            raise ValueError(f"Invalid student ID format")
        return v

    @validator("embeddings")
    def validate_embeddings(cls, v):
        is_valid, error_msg = validate_embeddings_list(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class RegistrationResponse(BaseModel):
    """Response model for registration"""
    status: str
    message: str
    student_id: str


class VerificationRequest(BaseModel):
    """Request model for attendance verification"""
    student_id: str = Field(..., description="Student ID")
    live_embedding: List[float] = Field(..., description="Live face embedding")

    @validator("student_id")
    def validate_student_id(cls, v):
        if not config.validate_student_id(v):
            raise ValueError(f"Invalid student ID format")
        return v

    @validator("live_embedding")
    def validate_live_embedding(cls, v):
        is_valid, error_msg = validate_embedding(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class VerificationResponse(BaseModel):
    """Response model for attendance verification"""
    status: str
    message: str
    similarity_scores: Optional[List[float]] = None
    matches: Optional[int] = None
    confidence: Optional[float] = None
    matches_found: Optional[int] = None
    best_match: Optional[float] = None
    marked_at: Optional[str] = None
    subject: Optional[str] = None


class AttendanceRecord(BaseModel):
    """Model for attendance record"""
    student_id: str
    present: bool
    marked_at: Optional[datetime] = None


class AttendanceResponse(BaseModel):
    """Response model for attendance query"""
    date: str
    total_students: int
    present: int
    absent: int
    attendance: List[AttendanceRecord]


# ============================================================================
# Admin API Models
# ============================================================================

class StudentCreate(BaseModel):
    student_id: str
    name: Optional[str] = None
    class_name: Optional[str] = None
    embedding: Optional[List[float]] = None


class ClassroomCreate(BaseModel):
    classroom: str
    ip: str


class ClassScheduleCreate(BaseModel):
    class_name: str
    subject: str
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    classroom: str


class AttendanceCreate(BaseModel):
    student_id: str
    subject: str
    attendance_percentage: Optional[float] = 0.0


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    init_database()
    print("✅ Backend started successfully")
    print(f"🔧 Configuration: {config.get_config_summary()}")


# ============================================================================
# Student APIs - Frontend Compatible
# ============================================================================

@app.post("/api/register", response_model=RegistrationResponse)
async def register_student(
    request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new student or update existing student's face embeddings.
    """
    student_id = request.student_id

    try:
        import numpy as np
        avg_embedding = np.mean(request.embeddings, axis=0).tolist()

        # Check if student already exists
        existing_student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if existing_student:
            # Update existing student's embedding
            existing_student.embedding = avg_embedding
            existing_student.registered_at = datetime.now(ist)
            
            # Delete old face embeddings
            db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student_id).delete()
            db.flush()  # Ensure deletions are persisted
            
            message = "Student embeddings updated successfully"
        else:
            # Create new student record
            new_student = Student(
                student_id=student_id,
                embedding=avg_embedding,
                registered_at=datetime.now(ist)
            )
            db.add(new_student)
            db.flush()  # Persist student to DB
            
            message = "Student registered successfully"

        # Add new face embeddings
        for i, embedding in enumerate(request.embeddings):
            face_embedding = FaceEmbedding(
                student_id=student_id,
                embedding_index=i + 1,
                embedding_vector=embedding,
                created_at=datetime.now(ist)
            )
            db.add(face_embedding)

        db.commit()  # Commit the entire transaction

        return RegistrationResponse(
            status="success",
            message=message,
            student_id=student_id
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Registration failed: {str(e)}"
            }
        )

@app.post("/api/verify", response_model=VerificationResponse)
async def verify_attendance(
    request: VerificationRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    NEW VERIFICATION LOGIC:
    1. Get student's class
    2. Find active class using current time
    3. Get classroom IP
    4. Verify request IP is in same subnet
    5. Only then perform face verification
    6. Update attendance percentage
    """
    student_id = request.student_id
    current_time = datetime.now().time()
    
    print("=" * 80)
    print("🔍 ATTENDANCE VERIFICATION REQUEST")
    print("=" * 80)
    print(f"📋 Student ID: {student_id}")
    print(f"⏰ Current Time: {current_time.strftime('%H:%M:%S')}")
    print(f"🌐 Client IP: {req.client.host}")
    print("-" * 80)

    # Step 1: Check if student is registered
    print("\n[STEP 1] Checking if student is registered...")
    student = db.query(Student).filter(Student.student_id == student_id).first()
    
    if not student:
        print(f"❌ Student {student_id} not found in database")
        return VerificationResponse(
            status="not_registered",
            message="Student not registered. Please register first.",
        )
    
    print(f"✅ Student found: {student.name or 'N/A'}")
    print(f"   Class: {student.class_name or 'Not Set'}")

    # Step 2: Get student's class
    print("\n[STEP 2] Validating student class assignment...")
    if not student.class_name:
        print("❌ Student class not set")
        return VerificationResponse(
            status="error",
            message="Student class not set. Please update via admin panel.",
        )
    
    print(f"✅ Student assigned to class: {student.class_name}")

    # Step 3: Find active class schedule
    print("\n[STEP 3] Finding active class schedule...")
    print(f"   Searching for: class='{student.class_name}', time={current_time.strftime('%H:%M')}")
    
    active_schedule = db.query(ClassSchedule).filter(
        ClassSchedule.class_name == student.class_name,
        ClassSchedule.start_time <= current_time,
        ClassSchedule.end_time >= current_time
    ).first()

    if not active_schedule:
        print("❌ No active class found at this time")
        
        # Debug: Show all schedules for this class
        all_schedules = db.query(ClassSchedule).filter(
            ClassSchedule.class_name == student.class_name
        ).all()
        print(f"   📅 Total schedules for {student.class_name}: {len(all_schedules)}")
        for sched in all_schedules:
            print(f"      - {sched.subject}: {sched.start_time.strftime('%H:%M')} - {sched.end_time.strftime('%H:%M')} @ {sched.classroom}")
        
        return VerificationResponse(
            status="no_active_class",
            message="No active class at this time for your section.",
        )
    
    print(f"✅ Active class found:")
    print(f"   Subject: {active_schedule.subject}")
    print(f"   Time: {active_schedule.start_time.strftime('%H:%M')} - {active_schedule.end_time.strftime('%H:%M')}")
    print(f"   Classroom: {active_schedule.classroom}")

    # Step 4: Get classroom IP
    print("\n[STEP 4] Retrieving classroom IP configuration...")
    classroom_record = db.query(Classroom).filter(
        Classroom.classroom == active_schedule.classroom
    ).first()

    if not classroom_record:
        print(f"❌ Classroom '{active_schedule.classroom}' not found in database")
        return VerificationResponse(
            status="error",
            message="Classroom configuration not found.",
        )
    
    print(f"✅ Classroom IP: {classroom_record.ip}")

    # Step 5: Extract request IP and verify subnet
    print("\n[STEP 5] Verifying IP subnet match...")
    client_ip = req.client.host
    print(f"   Client IP: {client_ip}")
    print(f"   Classroom IP: {classroom_record.ip}")

    # Check subnet match
    subnet_match = check_subnet_match(client_ip, classroom_record.ip)
    print(f"   Subnet Match: {subnet_match}")
    
    if not subnet_match:
        print(f"❌ IP verification failed - client not in classroom subnet")
        return VerificationResponse(
            status="ip_verification_failed",
            message=f"IP verification failed. You must be in {active_schedule.classroom}.",
        )
    
    print("✅ IP verification passed")

    # Step 6: Retrieve stored embeddings for face verification
    print("\n[STEP 6] Retrieving stored face embeddings...")
    stored_embeddings_records = db.query(FaceEmbedding).filter(
        FaceEmbedding.student_id == student_id
    ).order_by(FaceEmbedding.embedding_index).all()
    
    print(f"   Found {len(stored_embeddings_records)} stored embeddings (expected: {config.NUM_EMBEDDINGS})")

    if len(stored_embeddings_records) != config.NUM_EMBEDDINGS:
        print("⚠️  Incomplete embeddings, falling back to single embedding from Student table")
        if student.embedding:
            stored_embeddings = [student.embedding]
            print(f"✅ Using fallback embedding (dimension: {len(student.embedding)})")
        else:
            print("❌ No embeddings available - registration incomplete")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Incomplete registration data. Please re-register."
                }
            )
    else:
        stored_embeddings = [record.embedding_vector for record in stored_embeddings_records]
        print(f"✅ Using {len(stored_embeddings)} embeddings from FaceEmbedding table")
        print(f"   Embedding dimensions: {[len(emb) for emb in stored_embeddings]}")

    # Step 7: Perform face verification
    print("\n[STEP 7] Performing biometric face verification...")
    print(f"   Live embedding dimension: {len(request.live_embedding)}")
    print(f"   Comparing against {len(stored_embeddings)} stored embeddings")
    
    is_verified, similarity_scores, num_matches = verify_face(
        request.live_embedding,
        stored_embeddings
    )
    
    print(f"   Similarity scores: {[f'{score:.4f}' for score in similarity_scores]}")
    print(f"   Matches (>= threshold): {num_matches}/{len(stored_embeddings)}")
    print(f"   Best similarity: {max(similarity_scores) if similarity_scores else 0.0:.4f}")
    print(f"   Verification result: {'✅ PASSED' if is_verified else '❌ FAILED'}")

    if not is_verified:
        best_similarity = max(similarity_scores) if similarity_scores else 0.0
        print(f"\n❌ VERIFICATION FAILED - Insufficient matches")
        return VerificationResponse(
            status="verification_failed",
            message="Biometric verification failed",
            similarity_scores=format_similarity_scores(similarity_scores),
            matches=num_matches,
            matches_found=num_matches,
            best_match=float(best_similarity),
            confidence=float(best_similarity)
        )

    # Step 8: Update attendance percentage
    print("\n[STEP 8] Updating attendance record...")
    try:
        subject = active_schedule.subject
        print(f"   Subject: {subject}")

        # Get or create attendance record
        attendance_record = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.subject == subject
        ).first()

        if not attendance_record:
            print("   ℹ️  No existing record - creating new attendance record")
            attendance_record = Attendance(
                student_id=student_id,
                subject=subject,
                attendance_percentage=0.0,
                total_classes=0,
                attended_classes=0
            )
            db.add(attendance_record)
        else:
            print(f"   📊 Current stats: {attendance_record.attended_classes}/{attendance_record.total_classes} classes")
            print(f"   📈 Current percentage: {attendance_record.attendance_percentage:.2f}%")
            print(f"   🕒 Last marked: {attendance_record.last_marked_at.strftime('%Y-%m-%d %H:%M:%S') if attendance_record.last_marked_at else 'Never'}")

        # Increment attendance (only once per class session)
        # Check if already marked for this session (within last 2 hours)
        # Increment attendance (only once per class session)
        # Check if already marked for THIS SPECIFIC CLASS SESSION (start_time to end_time)
        if attendance_record.last_marked_at:
            # Convert last_marked_at to time only for comparison
            last_marked_time = attendance_record.last_marked_at.time()
            
            # Check if last mark was today and within current class time slot
            last_marked_date = attendance_record.last_marked_at.date()
            today = datetime.now(ist).date()
            
            print(f"   🕒 Last marked: {attendance_record.last_marked_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📅 Last marked date: {last_marked_date}, Today: {today}")
            print(f"   🕐 Last marked time: {last_marked_time.strftime('%H:%M:%S')}")
            print(f"   📚 Current class time slot: {active_schedule.start_time.strftime('%H:%M')} - {active_schedule.end_time.strftime('%H:%M')}")
            
            # Check if already marked for this specific class session
            if (last_marked_date == today and 
                active_schedule.start_time <= last_marked_time <= active_schedule.end_time):
                
                time_diff = datetime.now(ist) - attendance_record.last_marked_at
                time_diff_minutes = time_diff.total_seconds() / 60
                print(f"   ⏱️  Time since last mark: {time_diff_minutes:.1f} minutes")
                print(f"   ⚠️  Already marked for this class session - skipping")
                
                return VerificationResponse(
                    status="already_marked",
                    message=f"Attendance already marked for {subject} (this class session)",
                    marked_at=attendance_record.last_marked_at.isoformat(),
                    subject=subject
                )
            else:
                print(f"   ✅ Last mark was in a different time slot or day - proceeding")

        # Update attendance
        old_attended = attendance_record.attended_classes
        old_total = attendance_record.total_classes
        old_percentage = attendance_record.attendance_percentage
        
        attendance_record.attended_classes += 1
        attendance_record.total_classes += 1
        attendance_record.attendance_percentage = (
            attendance_record.attended_classes / attendance_record.total_classes * 100
        )
        attendance_record.last_marked_at = datetime.now(ist)
        
        print(f"   ✅ Attendance updated:")
        print(f"      Before: {old_attended}/{old_total} ({old_percentage:.2f}%)")
        print(f"      After:  {attendance_record.attended_classes}/{attendance_record.total_classes} ({attendance_record.attendance_percentage:.2f}%)")

        db.commit()
        print("   💾 Changes committed to database")

        best_similarity = max(similarity_scores) if similarity_scores else 0.0
        
        print("\n" + "=" * 80)
        print("✅ ATTENDANCE MARKED SUCCESSFULLY")
        print("=" * 80)
        print(f"Student: {student_id}")
        print(f"Subject: {subject}")
        print(f"Attendance: {attendance_record.attendance_percentage:.2f}%")
        print(f"Confidence: {best_similarity:.4f}")
        print("=" * 80 + "\n")
        
        return VerificationResponse(
            status="ok",
            message=f"Attendance marked for {subject}",
            similarity_scores=format_similarity_scores(similarity_scores),
            matches=num_matches,
            matches_found=num_matches,
            confidence=float(best_similarity),
            marked_at=attendance_record.last_marked_at.isoformat(),
            subject=subject
        )

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR during attendance update: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to mark attendance: {str(e)}"
            }
        )

# ============================================================================
# Admin APIs - CRUD Operations
# ============================================================================

def require_admin_auth(authorization: Optional[str] = Header(None)):
    """Dependency to require admin authentication"""
    if not verify_basic_auth(authorization):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


# Student CRUD
@app.get("/api/admin/students")
async def get_students(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Get all students"""
    students = db.query(Student).all()
    return [
        {
            "student_id": s.student_id,
            "name": s.name,
            "class_name": s.class_name,
            "registered_at": s.registered_at.isoformat() if s.registered_at else None
        }
        for s in students
    ]


@app.post("/api/admin/students")
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Create a new student"""
    existing = db.query(Student).filter(Student.student_id == student.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")

    new_student = Student(
        student_id=student.student_id,
        name=student.name,
        class_name=student.class_name,
        embedding=student.embedding,
        registered_at=datetime.now(ist)
    )
    db.add(new_student)
    db.commit()
    return {"status": "success", "message": "Student created"}


@app.put("/api/admin/students/{student_id}")
async def update_student(
    student_id: str,
    student: StudentCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Update student information"""
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.name is not None:
        db_student.name = student.name
    if student.class_name is not None:
        db_student.class_name = student.class_name
    if student.embedding is not None:
        db_student.embedding = student.embedding

    db.commit()
    return {"status": "success", "message": "Student updated"}


@app.delete("/api/admin/students/{student_id}")
async def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Delete a student"""
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(db_student)
    db.commit()
    return {"status": "success", "message": "Student deleted"}


# Classroom CRUD
@app.get("/api/admin/classrooms")
async def get_classrooms(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Get all classrooms"""
    classrooms = db.query(Classroom).all()
    return [{"classroom": c.classroom, "ip": c.ip} for c in classrooms]


@app.post("/api/admin/classrooms")
async def create_classroom(
    classroom: ClassroomCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Create a new classroom"""
    existing = db.query(Classroom).filter(Classroom.classroom == classroom.classroom).first()
    if existing:
        raise HTTPException(status_code=400, detail="Classroom already exists")

    new_classroom = Classroom(classroom=classroom.classroom, ip=classroom.ip)
    db.add(new_classroom)
    db.commit()
    return {"status": "success", "message": "Classroom created"}


@app.put("/api/admin/classrooms/{classroom_name}")
async def update_classroom(
    classroom_name: str,
    classroom: ClassroomCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Update classroom information"""
    db_classroom = db.query(Classroom).filter(Classroom.classroom == classroom_name).first()
    if not db_classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    db_classroom.ip = classroom.ip
    db.commit()
    return {"status": "success", "message": "Classroom updated"}


@app.delete("/api/admin/classrooms/{classroom_name}")
async def delete_classroom(
    classroom_name: str,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Delete a classroom"""
    db_classroom = db.query(Classroom).filter(Classroom.classroom == classroom_name).first()
    if not db_classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    db.delete(db_classroom)
    db.commit()
    return {"status": "success", "message": "Classroom deleted"}


# ClassSchedule CRUD
@app.get("/api/admin/schedules")
async def get_schedules(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Get all class schedules"""
    schedules = db.query(ClassSchedule).all()
    return [
        {
            "class_name": s.class_name,
            "subject": s.subject,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "classroom": s.classroom
        }
        for s in schedules
    ]


@app.post("/api/admin/schedules")
async def create_schedule(
    schedule: ClassScheduleCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Create a new class schedule"""
    # Parse time strings
    start_time = datetime.strptime(schedule.start_time, "%H:%M").time()
    end_time = datetime.strptime(schedule.end_time, "%H:%M").time()

    # Check if classroom exists
    classroom = db.query(Classroom).filter(Classroom.classroom == schedule.classroom).first()
    if not classroom:
        raise HTTPException(status_code=400, detail="Classroom does not exist")

    new_schedule = ClassSchedule(
        class_name=schedule.class_name,
        subject=schedule.subject,
        start_time=start_time,
        end_time=end_time,
        classroom=schedule.classroom
    )
    db.add(new_schedule)

    try:
        db.commit()
        return {"status": "success", "message": "Schedule created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Schedule creation failed: {str(e)}")


@app.delete("/api/admin/schedules")
async def delete_schedule(
    class_name: str,
    subject: str,
    start_time: str,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Delete a class schedule"""
    start_time_obj = datetime.strptime(start_time, "%H:%M").time()

    db_schedule = db.query(ClassSchedule).filter(
        ClassSchedule.class_name == class_name,
        ClassSchedule.subject == subject,
        ClassSchedule.start_time == start_time_obj
    ).first()

    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(db_schedule)
    db.commit()
    return {"status": "success", "message": "Schedule deleted"}


# Attendance CRUD
@app.get("/api/admin/attendance")
async def get_all_attendance(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Get all attendance records"""
    attendance = db.query(Attendance).all()
    return [
        {
            "student_id": a.student_id,
            "subject": a.subject,
            "attendance_percentage": a.attendance_percentage,
            "total_classes": a.total_classes,
            "attended_classes": a.attended_classes,
            "last_marked_at": a.last_marked_at.isoformat() if a.last_marked_at else None
        }
        for a in attendance
    ]


@app.post("/api/admin/attendance")
async def create_attendance(
    attendance: AttendanceCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Create or update attendance record"""
    existing = db.query(Attendance).filter(
        Attendance.student_id == attendance.student_id,
        Attendance.subject == attendance.subject
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Attendance record already exists. Use PUT to update.")

    new_attendance = Attendance(
        student_id=attendance.student_id,
        subject=attendance.subject,
        attendance_percentage=attendance.attendance_percentage or 0.0,
        total_classes=0,
        attended_classes=0
    )
    db.add(new_attendance)
    db.commit()
    return {"status": "success", "message": "Attendance record created"}


@app.put("/api/admin/attendance/{student_id}/{subject}")
async def update_attendance(
    student_id: str,
    subject: str,
    attendance_percentage: float,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Update attendance percentage"""
    db_attendance = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.subject == subject
    ).first()

    if not db_attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db_attendance.attendance_percentage = attendance_percentage
    db.commit()
    return {"status": "success", "message": "Attendance updated"}


@app.delete("/api/admin/attendance/{student_id}/{subject}")
async def delete_attendance(
    student_id: str,
    subject: str,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Delete an attendance record"""
    db_attendance = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.subject == subject
    ).first()

    if not db_attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(db_attendance)
    db.commit()
    return {"status": "success", "message": "Attendance record deleted"}


# Legacy admin endpoint for backward compatibility
@app.get("/api/admin/stats")
async def get_statistics(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth)
):
    """Get overall system statistics"""
    total_students = db.query(Student).count()
    total_attendance_records = db.query(Attendance).count()

    return {
        "total_registered_students": total_students,
        "total_attendance_records": total_attendance_records,
        "config": config.get_config_summary()
    }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Attendance System Backend",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(ist).isoformat(),
        "config": config.get_config_summary()
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import os

    cert_file = os.path.join(os.path.dirname(__file__), "..", "certs", "cert.pem")
    key_file = os.path.join(os.path.dirname(__file__), "..", "certs", "key.pem")

    if os.path.exists(cert_file) and os.path.exists(key_file):
        uvicorn.run(
            "main:app",
            host=config.HOST,
            port=config.PORT,
            reload=True,
            ssl_certfile=cert_file,
            ssl_keyfile=key_file
        )
    else:
        print("⚠️ WARNING: SSL certificates not found!")
        uvicorn.run(
            "main:app",
            host=config.HOST,
            port=config.PORT,
            reload=True
        )
"""
Desktop GUI Tool for Attendance System Database Management
Allows viewing, adding, editing, and deleting records from all tables.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from sqlalchemy.orm import Session
from datetime import datetime, time
import json

from database import (
    SessionLocal, Student, Classroom, ClassSchedule, 
    Attendance, FaceEmbedding
)


class AttendanceSystemGUI:
    """Main GUI application for database management"""

    def __init__(self, root):
        self.root = root
        self.root.title("Attendance System - Database Manager")
        self.root.geometry("1200x700")
        self.status_bar = tk.Label(
            root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs for each table
        self.create_students_tab()
        self.create_classrooms_tab()
        self.create_schedules_tab()
        self.create_attendance_tab()

        # Status bar


    def get_db(self):
        """Get database session"""
        return SessionLocal()

    def set_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
        self.root.update()

    # ========================================================================
    # Students Tab
    # ========================================================================

    def create_students_tab(self):
        """Create Students table management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Students")

        # Treeview
        columns = ("student_id", "name", "class_name", "registered_at")
        self.students_tree = ttk.Treeview(tab, columns=columns, show="headings", height=20)

        for col in columns:
            self.students_tree.heading(col, text=col.replace("_", " ").title())
            self.students_tree.column(col, width=150)

        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.students_tree.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.students_tree.config(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tk.Frame(tab)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        tk.Button(button_frame, text="Refresh", command=self.load_students, width=15).pack(pady=5)
        tk.Button(button_frame, text="Add Student", command=self.add_student, width=15).pack(pady=5)
        tk.Button(button_frame, text="Edit Student", command=self.edit_student, width=15).pack(pady=5)
        tk.Button(button_frame, text="Delete Student", command=self.delete_student, width=15).pack(pady=5)

        # Load initial data
        self.load_students()

    def load_students(self):
        """Load students from database"""
        self.students_tree.delete(*self.students_tree.get_children())
        db = self.get_db()
        try:
            students = db.query(Student).all()
            for student in students:
                self.students_tree.insert("", tk.END, values=(
                    student.student_id,
                    student.name or "",
                    student.class_name or "",
                    student.registered_at.strftime("%Y-%m-%d %H:%M") if student.registered_at else ""
                ))
            self.set_status(f"Loaded {len(students)} students")
        finally:
            db.close()

    def add_student(self):
        """Open dialog to add new student"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Student")
        dialog.geometry("400x250")

        tk.Label(dialog, text="Student ID (USN):").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        student_id_entry = tk.Entry(dialog, width=30)
        student_id_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Class:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        class_entry = tk.Entry(dialog, width=30)
        class_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Embedding (JSON):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        embedding_text = scrolledtext.ScrolledText(dialog, width=30, height=5)
        embedding_text.grid(row=3, column=1, padx=10, pady=5)
        embedding_text.insert(tk.END, "[]")

        def save():
            student_id = student_id_entry.get().strip()
            name = name_entry.get().strip() or None
            class_name = class_entry.get().strip() or None

            try:
                embedding_str = embedding_text.get("1.0", tk.END).strip()
                embedding = json.loads(embedding_str) if embedding_str != "[]" else None
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON for embedding")
                return

            if not student_id:
                messagebox.showerror("Error", "Student ID is required")
                return

            db = self.get_db()
            try:
                new_student = Student(
                    student_id=student_id,
                    name=name,
                    class_name=class_name,
                    embedding=embedding,
                    registered_at=datetime.utcnow()
                )
                db.add(new_student)
                db.commit()
                messagebox.showinfo("Success", "Student added successfully")
                dialog.destroy()
                self.load_students()
            except Exception as e:
                db.rollback()
                messagebox.showerror("Error", f"Failed to add student: {str(e)}")
            finally:
                db.close()

        tk.Button(dialog, text="Save", command=save, width=15).grid(row=4, column=0, columnspan=2, pady=10)

    def edit_student(self):
        """Edit selected student"""
        selection = self.students_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a student to edit")
            return

        values = self.students_tree.item(selection[0])["values"]
        student_id = values[0]

        db = self.get_db()
        try:
            student = db.query(Student).filter(Student.student_id == student_id).first()
            if not student:
                messagebox.showerror("Error", "Student not found")
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Student")
            dialog.geometry("400x250")

            tk.Label(dialog, text="Student ID:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
            tk.Label(dialog, text=student_id).grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

            tk.Label(dialog, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
            name_entry = tk.Entry(dialog, width=30)
            name_entry.insert(0, student.name or "")
            name_entry.grid(row=1, column=1, padx=10, pady=5)

            tk.Label(dialog, text="Class:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
            class_entry = tk.Entry(dialog, width=30)
            class_entry.insert(0, student.class_name or "")
            class_entry.grid(row=2, column=1, padx=10, pady=5)

            def save():
                student.name = name_entry.get().strip() or None
                student.class_name = class_entry.get().strip() or None

                try:
                    db.commit()
                    messagebox.showinfo("Success", "Student updated successfully")
                    dialog.destroy()
                    self.load_students()
                except Exception as e:
                    db.rollback()
                    messagebox.showerror("Error", f"Failed to update: {str(e)}")

            tk.Button(dialog, text="Save", command=save, width=15).grid(row=3, column=0, columnspan=2, pady=10)

        finally:
            db.close()

    def delete_student(self):
        """Delete selected student"""
        selection = self.students_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a student to delete")
            return

        values = self.students_tree.item(selection[0])["values"]
        student_id = values[0]

        if not messagebox.askyesno("Confirm", f"Delete student {student_id}?"):
            return

        db = self.get_db()
        try:
            student = db.query(Student).filter(Student.student_id == student_id).first()
            if student:
                db.delete(student)
                db.commit()
                messagebox.showinfo("Success", "Student deleted")
                self.load_students()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")
        finally:
            db.close()

    # ========================================================================
    # Classrooms Tab
    # ========================================================================

    def create_classrooms_tab(self):
        """Create Classrooms table management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Classrooms")

        # Treeview
        columns = ("classroom", "ip")
        self.classrooms_tree = ttk.Treeview(tab, columns=columns, show="headings", height=20)

        for col in columns:
            self.classrooms_tree.heading(col, text=col.replace("_", " ").title())
            self.classrooms_tree.column(col, width=200)

        self.classrooms_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons
        button_frame = tk.Frame(tab)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        tk.Button(button_frame, text="Refresh", command=self.load_classrooms, width=15).pack(pady=5)
        tk.Button(button_frame, text="Add Classroom", command=self.add_classroom, width=15).pack(pady=5)
        tk.Button(button_frame, text="Edit Classroom", command=self.edit_classroom, width=15).pack(pady=5)
        tk.Button(button_frame, text="Delete Classroom", command=self.delete_classroom, width=15).pack(pady=5)

        self.load_classrooms()

    def load_classrooms(self):
        """Load classrooms from database"""
        self.classrooms_tree.delete(*self.classrooms_tree.get_children())
        db = self.get_db()
        try:
            classrooms = db.query(Classroom).all()
            for classroom in classrooms:
                self.classrooms_tree.insert("", tk.END, values=(
                    classroom.classroom,
                    classroom.ip
                ))
            self.set_status(f"Loaded {len(classrooms)} classrooms")
        finally:
            db.close()

    def add_classroom(self):
        """Add new classroom"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Classroom")
        dialog.geometry("350x150")

        tk.Label(dialog, text="Classroom:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        classroom_entry = tk.Entry(dialog, width=25)
        classroom_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(dialog, text="IP Address:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        ip_entry = tk.Entry(dialog, width=25)
        ip_entry.grid(row=1, column=1, padx=10, pady=10)

        def save():
            classroom_name = classroom_entry.get().strip()
            ip = ip_entry.get().strip()

            if not classroom_name or not ip:
                messagebox.showerror("Error", "All fields are required")
                return

            db = self.get_db()
            try:
                new_classroom = Classroom(classroom=classroom_name, ip=ip)
                db.add(new_classroom)
                db.commit()
                messagebox.showinfo("Success", "Classroom added")
                dialog.destroy()
                self.load_classrooms()
            except Exception as e:
                db.rollback()
                messagebox.showerror("Error", f"Failed: {str(e)}")
            finally:
                db.close()

        tk.Button(dialog, text="Save", command=save, width=15).grid(row=2, column=0, columnspan=2, pady=10)

    def edit_classroom(self):
        """Edit selected classroom"""
        selection = self.classrooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a classroom")
            return

        values = self.classrooms_tree.item(selection[0])["values"]
        classroom_name = values[0]

        db = self.get_db()
        try:
            classroom = db.query(Classroom).filter(Classroom.classroom == classroom_name).first()

            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Classroom")
            dialog.geometry("350x150")

            tk.Label(dialog, text="Classroom:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Label(dialog, text=classroom_name).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

            tk.Label(dialog, text="IP Address:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            ip_entry = tk.Entry(dialog, width=25)
            ip_entry.insert(0, classroom.ip)
            ip_entry.grid(row=1, column=1, padx=10, pady=10)

            def save():
                classroom.ip = ip_entry.get().strip()
                try:
                    db.commit()
                    messagebox.showinfo("Success", "Classroom updated")
                    dialog.destroy()
                    self.load_classrooms()
                except Exception as e:
                    db.rollback()
                    messagebox.showerror("Error", f"Failed: {str(e)}")

            tk.Button(dialog, text="Save", command=save, width=15).grid(row=2, column=0, columnspan=2, pady=10)
        finally:
            db.close()

    def delete_classroom(self):
        """Delete selected classroom"""
        selection = self.classrooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a classroom")
            return

        values = self.classrooms_tree.item(selection[0])["values"]
        classroom_name = values[0]

        if not messagebox.askyesno("Confirm", f"Delete classroom {classroom_name}?"):
            return

        db = self.get_db()
        try:
            classroom = db.query(Classroom).filter(Classroom.classroom == classroom_name).first()
            if classroom:
                db.delete(classroom)
                db.commit()
                messagebox.showinfo("Success", "Classroom deleted")
                self.load_classrooms()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Error", f"Failed: {str(e)}")
        finally:
            db.close()

    # ========================================================================
    # Class Schedule Tab
    # ========================================================================

    def create_schedules_tab(self):
        """Create ClassSchedule table management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Class Schedule")

        # Treeview
        columns = ("class_name", "subject", "start_time", "end_time", "classroom")
        self.schedules_tree = ttk.Treeview(tab, columns=columns, show="headings", height=20)

        for col in columns:
            self.schedules_tree.heading(col, text=col.replace("_", " ").title())
            self.schedules_tree.column(col, width=150)

        self.schedules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons
        button_frame = tk.Frame(tab)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        tk.Button(button_frame, text="Refresh", command=self.load_schedules, width=15).pack(pady=5)
        tk.Button(button_frame, text="Add Schedule", command=self.add_schedule, width=15).pack(pady=5)
        tk.Button(button_frame, text="Delete Schedule", command=self.delete_schedule, width=15).pack(pady=5)

        self.load_schedules()

    def load_schedules(self):
        """Load schedules from database"""
        self.schedules_tree.delete(*self.schedules_tree.get_children())
        db = self.get_db()
        try:
            schedules = db.query(ClassSchedule).all()
            for schedule in schedules:
                self.schedules_tree.insert("", tk.END, values=(
                    schedule.class_name,
                    schedule.subject,
                    schedule.start_time.strftime("%H:%M"),
                    schedule.end_time.strftime("%H:%M"),
                    schedule.classroom
                ))
            self.set_status(f"Loaded {len(schedules)} schedules")
        finally:
            db.close()

    def add_schedule(self):
        """Add new schedule"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Class Schedule")
        dialog.geometry("350x250")

        tk.Label(dialog, text="Class:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        class_entry = tk.Entry(dialog, width=25)
        class_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Subject:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        subject_entry = tk.Entry(dialog, width=25)
        subject_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Start Time (HH:MM):").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        start_entry = tk.Entry(dialog, width=25)
        start_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(dialog, text="End Time (HH:MM):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        end_entry = tk.Entry(dialog, width=25)
        end_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Classroom:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        classroom_entry = tk.Entry(dialog, width=25)
        classroom_entry.grid(row=4, column=1, padx=10, pady=5)

        def save():
            try:
                class_name = class_entry.get().strip()
                subject = subject_entry.get().strip()
                start_str = start_entry.get().strip()
                end_str = end_entry.get().strip()
                classroom = classroom_entry.get().strip()

                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()

                db = self.get_db()
                new_schedule = ClassSchedule(
                    class_name=class_name,
                    subject=subject,
                    start_time=start_time,
                    end_time=end_time,
                    classroom=classroom
                )
                db.add(new_schedule)
                db.commit()
                db.close()

                messagebox.showinfo("Success", "Schedule added")
                dialog.destroy()
                self.load_schedules()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}")

        tk.Button(dialog, text="Save", command=save, width=15).grid(row=5, column=0, columnspan=2, pady=10)

    def delete_schedule(self):
        """Delete selected schedule"""
        selection = self.schedules_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a schedule")
            return

        values = self.schedules_tree.item(selection[0])["values"]

        if not messagebox.askyesno("Confirm", "Delete this schedule?"):
            return

        db = self.get_db()
        try:
            start_time = datetime.strptime(values[2], "%H:%M").time()
            schedule = db.query(ClassSchedule).filter(
                ClassSchedule.class_name == values[0],
                ClassSchedule.subject == values[1],
                ClassSchedule.start_time == start_time
            ).first()

            if schedule:
                db.delete(schedule)
                db.commit()
                messagebox.showinfo("Success", "Schedule deleted")
                self.load_schedules()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Error", f"Failed: {str(e)}")
        finally:
            db.close()

    # ========================================================================
    # Attendance Tab
    # ========================================================================

    def create_attendance_tab(self):
        """Create Attendance table management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Attendance")

        # Treeview
        columns = ("student_id", "subject", "percentage", "total", "attended", "last_marked")
        self.attendance_tree = ttk.Treeview(tab, columns=columns, show="headings", height=20)

        headers = ["Student ID", "Subject", "Percentage", "Total Classes", "Attended", "Last Marked"]
        for col, header in zip(columns, headers):
            self.attendance_tree.heading(col, text=header)
            self.attendance_tree.column(col, width=130)

        self.attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.attendance_tree.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.attendance_tree.config(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tk.Frame(tab)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        tk.Button(button_frame, text="Refresh", command=self.load_attendance, width=15).pack(pady=5)
        tk.Button(button_frame, text="Add Record", command=self.add_attendance, width=15).pack(pady=5)
        tk.Button(button_frame, text="Edit Record", command=self.edit_attendance, width=15).pack(pady=5)
        tk.Button(button_frame, text="Delete Record", command=self.delete_attendance, width=15).pack(pady=5)

        self.load_attendance()

    def load_attendance(self):
        """Load attendance records from database"""
        self.attendance_tree.delete(*self.attendance_tree.get_children())
        db = self.get_db()
        try:
            records = db.query(Attendance).all()
            for record in records:
                self.attendance_tree.insert("", tk.END, values=(
                    record.student_id,
                    record.subject,
                    f"{record.attendance_percentage:.2f}%",
                    record.total_classes,
                    record.attended_classes,
                    record.last_marked_at.strftime("%Y-%m-%d %H:%M") if record.last_marked_at else ""
                ))
            self.set_status(f"Loaded {len(records)} attendance records")
        finally:
            db.close()

    def add_attendance(self):
        """Add new attendance record"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Attendance Record")
        dialog.geometry("350x200")

        tk.Label(dialog, text="Student ID:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        student_entry = tk.Entry(dialog, width=25)
        student_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(dialog, text="Subject:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        subject_entry = tk.Entry(dialog, width=25)
        subject_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(dialog, text="Percentage:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        percentage_entry = tk.Entry(dialog, width=25)
        percentage_entry.insert(0, "0.0")
        percentage_entry.grid(row=2, column=1, padx=10, pady=10)

        def save():
            student_id = student_entry.get().strip()
            subject = subject_entry.get().strip()
            try:
                percentage = float(percentage_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Invalid percentage")
                return

            if not student_id or not subject:
                messagebox.showerror("Error", "Student ID and Subject are required")
                return

            db = self.get_db()
            try:
                new_record = Attendance(
                    student_id=student_id,
                    subject=subject,
                    attendance_percentage=percentage,
                    total_classes=0,
                    attended_classes=0
                )
                db.add(new_record)
                db.commit()
                messagebox.showinfo("Success", "Attendance record added")
                dialog.destroy()
                self.load_attendance()
            except Exception as e:
                db.rollback()
                messagebox.showerror("Error", f"Failed: {str(e)}")
            finally:
                db.close()

        tk.Button(dialog, text="Save", command=save, width=15).grid(row=3, column=0, columnspan=2, pady=10)

    def edit_attendance(self):
        """Edit selected attendance record"""
        selection = self.attendance_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a record")
            return

        values = self.attendance_tree.item(selection[0])["values"]
        student_id = values[0]
        subject = values[1]

        db = self.get_db()
        try:
            record = db.query(Attendance).filter(
                Attendance.student_id == student_id,
                Attendance.subject == subject
            ).first()

            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Attendance Record")
            dialog.geometry("350x200")

            tk.Label(dialog, text="Student ID:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Label(dialog, text=student_id).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

            tk.Label(dialog, text="Subject:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Label(dialog, text=subject).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

            tk.Label(dialog, text="Percentage:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
            percentage_entry = tk.Entry(dialog, width=25)
            percentage_entry.insert(0, str(record.attendance_percentage))
            percentage_entry.grid(row=2, column=1, padx=10, pady=10)

            def save():
                try:
                    record.attendance_percentage = float(percentage_entry.get().strip())
                    db.commit()
                    messagebox.showinfo("Success", "Record updated")
                    dialog.destroy()
                    self.load_attendance()
                except Exception as e:
                    db.rollback()
                    messagebox.showerror("Error", f"Failed: {str(e)}")

            tk.Button(dialog, text="Save", command=save, width=15).grid(row=3, column=0, columnspan=2, pady=10)
        finally:
            db.close()

    def delete_attendance(self):
        """Delete selected attendance record"""
        selection = self.attendance_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a record")
            return

        values = self.attendance_tree.item(selection[0])["values"]
        student_id = values[0]
        subject = values[1]

        if not messagebox.askyesno("Confirm", f"Delete attendance record for {student_id} - {subject}?"):
            return

        db = self.get_db()
        try:
            record = db.query(Attendance).filter(
                Attendance.student_id == student_id,
                Attendance.subject == subject
            ).first()

            if record:
                db.delete(record)
                db.commit()
                messagebox.showinfo("Success", "Record deleted")
                self.load_attendance()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Error", f"Failed: {str(e)}")
        finally:
            db.close()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AttendanceSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(50), nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default="student")  # student, instructor, admin
    password_hash = db.Column(db.String(256), nullable=False)
    face_image_path = db.Column(db.String(255), nullable=True)  # reference image
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- relationships ---
    enrollments = db.relationship('Enrollment', back_populates='user', cascade="all, delete-orphan")
    attendances = db.relationship('Attendance', back_populates='user', cascade="all, delete-orphan")

    # --- password helpers ---
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(250))

    enrollments = db.relationship('Enrollment', back_populates='unit', cascade="all, delete-orphan")
    attendances = db.relationship('Attendance', back_populates='unit', cascade="all, delete-orphan")


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)

    user = db.relationship('User', back_populates='enrollments')
    unit = db.relationship('Unit', back_populates='enrollments')


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False, index=True)
    date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    status = db.Column(db.String(10), default="present", nullable=False)  # present/absent
    captured_image_path = db.Column(db.String(255), nullable=True)
    marked_by = db.Column(db.String(20), default="student", nullable=False)  # student/instructor/admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- relationships ---
    user = db.relationship('User', back_populates='attendances')
    unit = db.relationship('Unit', back_populates='attendances')

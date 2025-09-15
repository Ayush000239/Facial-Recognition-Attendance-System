
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models import User
import os, base64
from pathlib import Path

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and (not user.student_id or user.student_id == student_id):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('attendance.dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        student_id = request.form.get('student_id', '').strip()
        role = request.form.get('role', 'student')
        password = request.form.get('password', '')
        face_image = request.form.get('face_image')  # dataURL
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('auth.register'))
        user = User(name=name, email=email, student_id=student_id, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        # Save reference face to Known_faces
        if face_image:
            folder = Path(current_app.root_path) / current_app.config['KNOWN_FACES_FOLDER'] / f"user_{user.id}"
            folder.mkdir(parents=True, exist_ok=True)
            ref_path = folder / "reference.png"
            header, b64 = face_image.split(',', 1)
            with open(ref_path, 'wb') as f:
                f.write(base64.b64decode(b64))
            user.face_image_path = str(ref_path)
            db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset without email: verify email + student_id, then set new password."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        student_id = request.form.get('student_id', '').strip()
        new_password = request.form.get('new_password', '')
        user = User.query.filter_by(email=email, student_id=student_id).first()
        if not user:
            flash('No user found with that email and student ID.', 'warning')
            return redirect(url_for('auth.forgot_password'))
        user.set_password(new_password)
        db.session.commit()
        flash('Password reset successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')

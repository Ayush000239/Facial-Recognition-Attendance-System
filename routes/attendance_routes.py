from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Response
from flask_login import login_required, current_user
from extensions import db
from models import User, Attendance, Unit, Enrollment
from utils.face_recognition import verify_face, save_dataurl_to_file
from pathlib import Path
import csv
from io import StringIO

attendance_bp = Blueprint('attendance', __name__)

def role_required(roles):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and current_user.role in roles:
                return f(*args, **kwargs)
            flash('Not authorized.', 'danger')
            return redirect(url_for('attendance.dashboard'))
        return wrapper
    return decorator


# ---------------- DASHBOARD (STUDENT MARK ATTENDANCE) ----------------
@attendance_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST' and current_user.role == 'student':
        unit_id = request.form.get('unit_id', type=int)
        if not unit_id:
            flash('Please select a unit before marking attendance.', 'danger')
            return redirect(url_for('attendance.dashboard'))

        face_image = request.form.get('face_image')
        ok = False
        if face_image and current_user.face_image_path:
            ok = verify_face(face_image, current_user.face_image_path)
        if not ok:
            flash('Face not recognized. Please try again with good lighting and alignment.', 'warning')
            return redirect(url_for('attendance.dashboard'))

        # Save captured image
        folder = Path(current_app.root_path) / current_app.config['KNOWN_FACES_FOLDER'] / f"user_{current_user.id}" / "captures"
        folder.mkdir(parents=True, exist_ok=True)
        img_path = folder / f"capture_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        save_dataurl_to_file(face_image, img_path)

        # Save attendance with unit_id
        att = Attendance(
            user_id=current_user.id,
            unit_id=unit_id,
            status="present",
            captured_image_path=str(img_path),
            marked_by="student",
            date=date.today()
        )
        db.session.add(att)
        db.session.commit()

        flash('Attendance marked!', 'success')
        return redirect(url_for('attendance.dashboard'))

    # Student summary
    total = present = rate = 0
    if current_user.is_authenticated:
        total = Attendance.query.filter_by(user_id=current_user.id).count()
        present = Attendance.query.filter_by(user_id=current_user.id, status='present').count()
        rate = round((present / total) * 100, 1) if total else 0.0

    # Student’s enrolled units
    units = []
    if current_user.role == 'student':
        units = [en.unit for en in current_user.enrollments]

    return render_template('dashboard.html', total_days=total, present_days=present, rate=rate, units=units)


# ---------------- LOGS (VIEW ATTENDANCE) ----------------
@attendance_bp.route('/logs', methods=['GET'])
@login_required
def logs():
    student = request.args.get('student', type=int)
    unit_id = request.args.get('unit_id', type=int)
    status = request.args.get('status', type=str)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    q = Attendance.query
    if current_user.role == 'student':
        q = q.filter(Attendance.user_id == current_user.id)
    else:
        if student:
            q = q.filter(Attendance.user_id == student)
    if unit_id:
        q = q.filter(Attendance.unit_id == unit_id)
    if status in ('present', 'absent'):
        q = q.filter(Attendance.status == status)
    if date_from:
        q = q.filter(Attendance.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        q = q.filter(Attendance.date <= datetime.strptime(date_to, "%Y-%m-%d").date())

    logs = q.order_by(Attendance.date.desc(), Attendance.id.desc()).all()
    students = User.query.order_by(User.name.asc()).all()
    units = Unit.query.order_by(Unit.name.asc()).all()
    return render_template('logs.html', logs=logs, students=students, units=units)


# ---------------- MANUAL MARKING (INSTRUCTOR/ADMIN) ----------------
@attendance_bp.route('/mark', methods=['POST'])
@login_required
@role_required(['instructor', 'admin'])
def mark_manual():
    user_id = request.form.get('user_id', type=int)
    unit_id = request.form.get('unit_id', type=int)
    status = request.form.get('status', 'present')

    if not user_id or not unit_id:
        flash('Select both a student and a unit.', 'warning')
        return redirect(url_for('attendance.logs'))

    att = Attendance(
        user_id=user_id,
        unit_id=unit_id,
        status=status,
        marked_by=current_user.role,
        date=date.today()
    )
    db.session.add(att)
    db.session.commit()
    flash('Attendance marked/updated.', 'success')
    return redirect(url_for('attendance.logs'))


# ---------------- EXPORT CSV ----------------
@attendance_bp.route('/logs/export/csv')
@login_required
@role_required(['instructor', 'admin'])
def export_csv():
    logs = Attendance.query.order_by(Attendance.date.desc(), Attendance.id.desc()).all()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Student", "Unit", "Status", "Marked By"])
    for log in logs:
        writer.writerow([
            log.date.strftime('%Y-%m-%d'),
            log.user.name if log.user else "-",
            log.unit.name if log.unit else "-",
            log.status,
            log.marked_by
        ])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance_logs.csv"}
    )


# ---------------- EXPORT PDF (simple placeholder) ----------------
@attendance_bp.route('/logs/export/pdf')
@login_required
@role_required(['instructor', 'admin'])
def export_pdf():
    # You can replace this with ReportLab/WeasyPrint for a proper PDF later
    return Response(
        "PDF export not implemented yet.",
        mimetype="text/plain"
    )

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Attendance, Unit, Enrollment
import os, shutil

# Use consistent blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ---------------- ADMIN DASHBOARD ----------------
@admin_bp.route("/")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("attendance.dashboard"))

    users = User.query.all()
    units = Unit.query.all()  # needed for unit management/enrollment
    return render_template("admin.html", users=users, units=units)


# ---------------- UNIT MANAGEMENT ----------------
@admin_bp.route("/add_unit", methods=["POST"])
@login_required
def add_unit():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("attendance.dashboard"))

    name = request.form["name"]
    description = request.form.get("description")

    if Unit.query.filter_by(name=name).first():
        flash("Unit already exists.", "danger")
    else:
        unit = Unit(name=name, description=description)
        db.session.add(unit)
        db.session.commit()
        flash("Unit created successfully.", "success")

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/delete_unit/<int:unit_id>", methods=["POST"])
@login_required
def delete_unit(unit_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("attendance.dashboard"))

    unit = Unit.query.get_or_404(unit_id)
    db.session.delete(unit)  # cascade deletes enrollments and attendance
    db.session.commit()

    flash(f"Unit {unit.name} deleted successfully.", "success")
    return redirect(url_for("admin.admin_dashboard"))


# ---------------- ENROLLMENT ----------------
@admin_bp.route("/enroll", methods=["POST"])
@login_required
def enroll_student():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("attendance.dashboard"))

    user_id = request.form["user_id"]
    unit_id = request.form["unit_id"]

    if not Enrollment.query.filter_by(user_id=user_id, unit_id=unit_id).first():
        enrollment = Enrollment(user_id=user_id, unit_id=unit_id)
        db.session.add(enrollment)
        db.session.commit()
        flash("Student enrolled successfully.", "success")
    else:
        flash("This student is already enrolled in the unit.", "warning")

    return redirect(url_for("admin.admin_dashboard"))


# ---------------- USER MANAGEMENT ----------------
@admin_bp.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("attendance.dashboard"))

    user = User.query.get_or_404(user_id)

    # delete user's attendance records first (cascade issue otherwise)
    Attendance.query.filter_by(user_id=user.id).delete()

    # delete user’s face data folder
    folder_path = os.path.join("static", "Known_faces", f"user_{user.id}")
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    db.session.delete(user)
    db.session.commit()

    flash(f"User {user.name} deleted successfully.", "success")
    return redirect(url_for("admin.admin_dashboard"))


# FaceAttend — Flask + DeepFace Attendance

## Quick Start
```bash
cd path\to\where\its\extracted
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

App runs on http://127.0.0.1:5000

## Features
- Roles: student / instructor / admin
- Student ID on login & registration
- Forgot password (verify email + student ID, no email needed)
- Webcam capture using getUserMedia
- DeepFace VGG-Face verification
- Save captures to `static/Known_faces/user_<id>/captures/`
- Logs with filters (student, status, date range)
- Instructors/Admins can manually mark or update attendance
- Student dashboard shows days present, total, and attendance rate
- Modern Bootstrap UI

## Notes
- First registration capture is saved as your reference face in `static/Known_faces/user_<id>/reference.png`.
- If DeepFace struggles, ensure bright, even lighting and your face centered.

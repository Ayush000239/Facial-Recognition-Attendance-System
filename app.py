import os
from flask import Flask, redirect, url_for
from extensions import db, login_manager
from flask_login import current_user
from flask_migrate import Migrate
from routes.auth_routes import auth_bp
from routes.attendance_routes import attendance_bp
from routes.admin_routes import admin_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # --- Config ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_' + os.urandom(16).hex())
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['KNOWN_FACES_FOLDER'] = os.path.join('static', 'Known_faces')
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, app.config['KNOWN_FACES_FOLDER']), exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)  # Flask-Migrate handles schema updates

    # --- Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # --- Routes ---
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('attendance.dashboard'))
        return redirect(url_for('auth.login'))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

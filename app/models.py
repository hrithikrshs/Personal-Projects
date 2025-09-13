from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login_manager

class User(UserMixin, db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(80), unique=True,  nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    first_name  = db.Column(db.String(50),  nullable=False)
    last_name   = db.Column(db.String(50),  nullable=False)
    profession  = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    phone       = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True)

    audio_files = db.relationship('AudioFile', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class AudioFile(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    filename         = db.Column(db.String(255), nullable=False)
    original_filename= db.Column(db.String(255), nullable=False)
    file_path        = db.Column(db.String(500), nullable=False)
    file_size        = db.Column(db.Integer)
    sample_rate      = db.Column(db.Integer)
    duration         = db.Column(db.Float)
    processed        = db.Column(db.Boolean, default=False)
    processing_params= db.Column(db.Text)   # JSON string
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<AudioFile {self.filename}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField, PasswordField, SubmitField, IntegerField,
    SelectField, TextAreaField, BooleanField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

class RegistrationForm(FlaskForm):
    first_name  = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name   = StringField('Last Name',  validators=[DataRequired(), Length(min=2, max=50)])
    username    = StringField('Username',   validators=[DataRequired(), Length(min=4, max=20)])
    email       = StringField('Email',      validators=[DataRequired(), Email()])
    phone       = StringField('Phone',      validators=[Length(min=10, max=20)])
    profession  = SelectField('Profession', choices=[
        ('', 'Select Profession'),
        ('doctor', 'Medical Doctor'),
        ('nurse', 'Nurse'),
        ('researcher', 'Researcher'),
        ('student', 'Student'),
        ('technician', 'Medical Technician'),
        ('engineer', 'Biomedical Engineer'),
        ('other', 'Other')
    ])
    institution = StringField('Institution', validators=[Length(max=200)])
    password    = PasswordField('Password', validators=[
        DataRequired(), Length(min=8, max=128)
    ])
    password2   = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password')
    ])
    terms       = BooleanField(validators=[DataRequired()])
    submit      = SubmitField('Create Account')

class LoginForm(FlaskForm):
    username    = StringField('Username or Email', validators=[DataRequired()])
    password    = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit      = SubmitField('Sign In')

class UploadForm(FlaskForm):
    audio_file    = FileField('Audio', validators=[
        FileRequired(), FileAllowed(['wav', 'mp3', 'flac'], 'Audio only!')
    ])
    description   = TextAreaField('Description', validators=[Length(max=500)])
    n_components  = IntegerField('Components',   default=8,    validators=[NumberRange(2, 20)])
    max_iterations= IntegerField('Iterations',   default=5000, validators=[NumberRange(100, 10000)])
    sample_rate   = IntegerField('Sample Rate',  default=16000,validators=[NumberRange(8000, 48000)])
    submit        = SubmitField('Process Audio')

class ProfileForm(FlaskForm):
    first_name  = StringField(validators=[DataRequired(), Length(min=2, max=50)])
    last_name   = StringField(validators=[DataRequired(), Length(min=2, max=50)])
    email       = StringField(validators=[DataRequired(), Email()])
    phone       = StringField(validators=[Length(min=10, max=20)])
    profession  = SelectField(choices=[
        ('doctor', 'Medical Doctor'), ('nurse', 'Nurse'),
        ('researcher', 'Researcher'), ('student', 'Student'),
        ('technician', 'Medical Technician'), ('engineer', 'Biomedical Engineer'),
        ('other', 'Other')
    ])
    institution = StringField(validators=[Length(max=200)])
    submit      = SubmitField('Update Profile')

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, AudioFile
from app.forms import RegistrationForm, LoginForm, UploadForm, ProfileForm
from app.processor import process_audio, get_audio_info
from app.visualizer import (
    create_spectrogram_plot,
    create_nmf_components_plot,
    create_cluster_plot,
    create_summary_plot,
)
import os
import uuid
import json
import base64
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            profession=form.profession.data,
            institution=form.institution.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            current_app.logger.error(f'Registration error: {e}')
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data.lower())
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username/email or password', 'error')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    recent_files = AudioFile.query.filter_by(user_id=current_user.id).order_by(AudioFile.created_at.desc()).limit(5).all()
    total_files = AudioFile.query.filter_by(user_id=current_user.id).count()
    processed_files = AudioFile.query.filter_by(user_id=current_user.id, processed=True).count()
    stats = {
        'total_files': total_files,
        'processed_files': processed_files,
        'pending_files': total_files - processed_files,
        'success_rate': (processed_files / total_files * 100) if total_files > 0 else 0
    }
    return render_template('dashboard.html', recent_files=recent_files, stats=stats)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.audio_file.data
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                file.save(file_path)
                audio_info = get_audio_info(file_path)
                if not audio_info.get('success', False):
                    flash(f'Error reading audio file: {audio_info.get("error", "Unknown")}', 'error')
                    os.remove(file_path)
                    return render_template('upload.html', form=form)
                audio_file = AudioFile(
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    sample_rate=audio_info['sample_rate'],
                    duration=audio_info['duration'],
                    user_id=current_user.id,
                    processing_params=json.dumps({
                        'n_components': form.n_components.data,
                        'max_iterations': form.max_iterations.data,
                        'sample_rate': form.sample_rate.data,
                        'description': form.description.data
                    })
                )
                db.session.add(audio_file)
                db.session.commit()
                flash('File uploaded successfully! Processing...', 'success')
                return redirect(url_for('main.process', file_id=audio_file.id))
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                flash(f'Upload failed: {str(e)}', 'error')
                current_app.logger.error(f'Upload error: {e}')
    return render_template('upload.html', form=form)

@bp.route('/process/<int:file_id>')
@login_required
def process(file_id):
    audio_file = AudioFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    if audio_file.processed:
        return redirect(url_for('main.results', file_id=file_id))
    params = json.loads(audio_file.processing_params)
    processing_result = process_audio(
        audio_file.file_path,
        n_components=params['n_components'],
        max_iter=params['max_iterations'],
        sr=params['sample_rate']
    )
    if not processing_result.get('success', False):
        print('Processing failed, error:', processing_result.get('error'))
        flash(f'Processing failed: {processing_result.get("error", "Unknown error")}', 'error')
        return redirect(url_for('main.dashboard'))

    # Create the results dir and print debug info
    output_dir = os.path.join(current_app.root_path,'static', 'results', str(file_id))
    try:
        print("Attempting to create directory:", os.path.abspath(output_dir))
        os.makedirs(output_dir, exist_ok=True)
        print("Directory exists after makedirs:", os.path.exists(output_dir))
    except Exception as e:
        print(f"ERROR: Unable to create directory {output_dir}: {e}")
        flash("Server error: can't create output directory for results.", "error")
        return redirect(url_for('main.dashboard'))

    spectrogram = create_spectrogram_plot(processing_result['D'], processing_result['sr'])
    nmf_components = create_nmf_components_plot(processing_result['W'], processing_result['H'])
    cluster_plot = create_cluster_plot(processing_result['labels'])
    summary_plot = create_summary_plot(processing_result['results'])

    print('Spectrogram success:', spectrogram.get('success'), '; Error:', spectrogram.get('error'))
    print('NMF success:', nmf_components.get('success'), '; Error:', nmf_components.get('error'))
    print('Cluster success:', cluster_plot.get('success'), '; Error:', cluster_plot.get('error'))
    print('Summary success:', summary_plot.get('success'), '; Error:', summary_plot.get('error'))
    print('Results data:', processing_result)

    def save_b64_image(img_dict, filename):
        if img_dict.get('success'):
            img_b64 = img_dict['image']
            out_path = os.path.join(output_dir, filename)
            try:
                with open(out_path, 'wb') as f:
                    f.write(base64.b64decode(img_b64))
                print('Saved image:', out_path)
                return f"/static/results/{file_id}/{filename}"
            except Exception as e:
                print(f"ERROR: Saving {filename} failed: {e}")
                return None
        else:
            print(f"Plot image {filename} not created due to failed generation.")
            return None

    spectrogram_path = save_b64_image(spectrogram, 'spectrogram.png')
    nmf_path = save_b64_image(nmf_components, 'nmf_components.png')
    cluster_path = save_b64_image(cluster_plot, 'cluster_plot.png')
    summary_path = save_b64_image(summary_plot, 'summary_plot.png')

    session[f'results_{file_id}'] = {
        'processing_result': {
            'sr': int(processing_result['sr']),
            'results': processing_result['results']
        },
        'spectrogram_path': spectrogram_path,
        'nmf_path': nmf_path,
        'cluster_path': cluster_path,
        'summary_path': summary_path,
    }
    audio_file.processed = True
    db.session.commit()
    flash('Audio processing completed successfully!', 'success')
    return redirect(url_for('main.results', file_id=file_id))

@bp.route('/results/<int:file_id>')
@login_required
def results(file_id):
    audio_file = AudioFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    if not audio_file.processed:
        flash('File has not been processed yet.', 'warning')
        return redirect(url_for('main.process', file_id=file_id))
    results_data = session.get(f'results_{file_id}')
    if not results_data:
        flash('Results not found. Please reprocess the file.', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('results.html', audio_file=audio_file, results=results_data)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data.lower()
        current_user.phone = form.phone.data
        current_user.profession = form.profession.data
        current_user.institution = form.institution.data
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Profile update failed. Please try again.', 'error')
            current_app.logger.error(f'Profile update error: {e}')
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.email.data = current_user.email
    form.phone.data = current_user.phone
    form.profession.data = current_user.profession
    form.institution.data = current_user.institution
    return render_template('profile.html', form=form)

@bp.route('/files')
@login_required
def files():
    page = request.args.get('page', 1, type=int)
    files = AudioFile.query.filter_by(user_id=current_user.id).order_by(AudioFile.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('files.html', files=files)

@bp.route('/delete_file/<int:file_id>')
@login_required
def delete_file(file_id):
    audio_file = AudioFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    try:
        if os.path.exists(audio_file.file_path):
            os.remove(audio_file.file_path)
        db.session.delete(audio_file)
        db.session.commit()
        session.pop(f'results_{file_id}', None)
        flash('File deleted successfully.', 'success')
    except Exception as e:
        flash('Failed to delete file.', 'error')
        current_app.logger.error(f'File deletion error: {e}')
    return redirect(url_for('main.files'))

@bp.route('/api/upload_progress')
@login_required
def upload_progress():
    return jsonify({'progress': 100})

@bp.route('/api/processing_status/<int:file_id>')
@login_required
def processing_status(file_id):
    audio_file = AudioFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'processed': audio_file.processed,
        'created_at': audio_file.created_at.isoformat()
    })

@bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

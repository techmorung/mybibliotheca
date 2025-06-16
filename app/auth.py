from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from .models import User, PasswordResetToken, db
from .forms import (LoginForm, RegistrationForm, RequestPasswordResetForm, 
                   PasswordResetForm, UserProfileForm, ChangePasswordForm,
                   PrivacySettingsForm, AdminPasswordResetForm)
from datetime import datetime, timedelta, timezone
import secrets

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        if user:
            # Check if account is locked
            if user.is_locked():
                flash('Account is temporarily locked due to too many failed login attempts. Please try again later.', 'error')
                return redirect(url_for('auth.login'))
            
            # Check if account is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return redirect(url_for('auth.login'))
            
            # Check password
            if user.check_password(form.password.data):
                # Successful login
                user.reset_failed_login()
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.index')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page)
            else:
                # Failed password
                user.increment_failed_login()
                attempts_left = max(0, 5 - user.failed_login_attempts)
                if attempts_left > 0:
                    flash(f'Invalid password. You have {attempts_left} attempts remaining.', 'error')
                else:
                    flash('Account locked due to too many failed attempts. Please try again in 30 minutes.', 'error')
        else:
            # User not found
            flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Allow admin users to create new users, otherwise redirect authenticated users
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # First user becomes admin
        if User.query.count() == 0:
            user.is_admin = True
            flash('Congratulations! As the first user, you have been granted admin privileges.', 'info')
        
        db.session.add(user)
        db.session.commit()
        
        # If admin is creating a user, redirect back to user management
        if current_user.is_authenticated and current_user.is_admin:
            flash(f'User {user.username} has been created successfully!', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash('Congratulations, you are now registered!', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('auth/profile.html', title='Profile', form=form)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been changed.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password is incorrect.', 'error')
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            db.session.add(reset_token)
            db.session.commit()
            
            # TODO: Send email with reset link
            # For now, just flash the token (in production, this would be emailed)
            flash(f'Password reset requested. Reset token: {token} (expires in 1 hour)', 'info')
            
        flash('Check your email for instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset_token or reset_token.is_expired():
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = reset_token.user
        user.set_password(form.password.data)
        reset_token.used = True
        db.session.commit()
        
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@auth.route('/privacy_settings', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    form = PrivacySettingsForm()
    
    if form.validate_on_submit():
        current_user.share_current_reading = form.share_current_reading.data
        current_user.share_reading_activity = form.share_reading_activity.data
        current_user.share_library = form.share_library.data
        db.session.commit()
        flash('Your privacy settings have been updated.', 'success')
        return redirect(url_for('auth.privacy_settings'))
    elif request.method == 'GET':
        form.share_current_reading.data = current_user.share_current_reading
        form.share_reading_activity.data = current_user.share_reading_activity
        form.share_library.data = current_user.share_library
    
    return render_template('auth/privacy_settings.html', title='Privacy Settings', form=form)

@auth.route('/my_activity')
@login_required
def my_activity():
    from .models import Book, ReadingLog
    from sqlalchemy import func
    
    # Get user's reading statistics
    total_books = Book.query.filter_by(user_id=current_user.id).count()
    
    # Get reading logs count
    reading_logs = ReadingLog.query.filter_by(user_id=current_user.id).count()
    
    # Get books added this year
    current_year = datetime.now(timezone.utc).year
    books_this_year = Book.query.filter_by(user_id=current_user.id).filter(
        func.strftime('%Y', Book.created_at) == str(current_year)
    ).count()
    
    # Get recent books (last 10)
    recent_books = Book.query.filter_by(user_id=current_user.id).order_by(
        Book.created_at.desc()
    ).limit(10).all()
    
    # Get recent reading logs (last 10)
    recent_logs = ReadingLog.query.filter_by(user_id=current_user.id).order_by(
        ReadingLog.date.desc()
    ).limit(10).all()
    
    return render_template('auth/my_activity.html', 
                         title='My Activity',
                         total_books=total_books,
                         reading_logs=reading_logs,
                         books_this_year=books_this_year,
                         recent_books=recent_books,
                         recent_logs=recent_logs)

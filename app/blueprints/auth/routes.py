from flask import render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import random
import string
from ...extensions import db
from ...models import User
from . import auth_bp


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=bool(remember))
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}! 🎉', 'success')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password. Please try again.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        diet_preference = request.form.get('diet_preference', 'veg')

        errors = []
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered. Please login.')
        if phone and User.query.filter_by(phone=phone).first():
            errors.append('Phone number already registered.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/signup.html')

        user = User(
            name=name,
            email=email,
            phone=phone if phone else None,
            diet_preference=diet_preference,
            is_verified=True  # Auto-verify for demo; in prod, send OTP
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to FreshMart, {name}! 🛒', 'success')
        return redirect(url_for('main.index'))
    return render_template('auth/signup.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out. See you soon! 👋', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            # In production, send OTP via email/SMS
            flash(f'OTP sent to {email}. (Demo OTP: {otp})', 'info')
            session['reset_email'] = email
            return redirect(url_for('auth.reset_password'))
        flash('No account found with this email.', 'danger')
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        otp = request.form.get('otp', '')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        user = User.query.filter_by(email=email).first()
        if not user:
            return redirect(url_for('auth.forgot_password'))
        if user.otp != otp:
            flash('Invalid OTP.', 'danger')
            return render_template('auth/reset_password.html')
        if user.otp_expiry < datetime.utcnow():
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html')
        user.set_password(password)
        user.otp = None
        user.otp_expiry = None
        db.session.commit()
        session.pop('reset_email', None)
        flash('Password reset successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            current_user.name = request.form.get('name', current_user.name).strip()
            current_user.phone = request.form.get('phone', current_user.phone).strip() or None
            current_user.diet_preference = request.form.get('diet_preference', current_user.diet_preference)
            current_user.language_preference = request.form.get('language_preference', current_user.language_preference)
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            if not current_user.check_password(current_pw):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'danger')
            elif new_pw != confirm_pw:
                flash('Passwords do not match.', 'danger')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    from ...models import Order, Address
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    addresses = current_user.addresses.all()
    return render_template('profile/profile.html', orders=orders, addresses=addresses)

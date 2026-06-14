from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import secrets
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Production-ready configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:YOUR_PASSWORD@localhost/clinic_db')

# Fix for Heroku PostgreSQL URL (postgres:// -> postgresql://)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app = Flask(__name__, template_folder='../frontend/templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("✓ Gemini AI configured successfully")
    except Exception as e:
        print(f"AI Error: {e}")
        model = None
else:
    model = None
    print("⚠ No API key - AI in demo mode")

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    address = db.Column(db.String(500))
    emergency_contact = db.Column(db.String(20))
    doctor = db.relationship('Doctor', backref='user', lazy=True, uselist=False)
    hospital = db.relationship('Hospital', backref='admin', lazy=True, uselist=False)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    contact = db.Column(db.String(20))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text)
    doctors = db.relationship('Doctor', backref='hospital', lazy=True)
    appointments = db.relationship('Appointment', backref='hospital', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer)
    consultation_fee = db.Column(db.Float, default=50.00)
    about = db.Column(db.Text)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    @property
    def name(self):
        return self.user.name if self.user else "Unknown"

class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    symptoms = db.Column(db.Text)
    notes = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime)
    test_results = db.Column(db.Text)
    doctor_notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='emergency_contacts')

class AmbulanceBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pickup_address = db.Column(db.String(500), nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    destination_hospital = db.Column(db.String(200))
    destination_lat = db.Column(db.Float)
    destination_lng = db.Column(db.Float)
    emergency_type = db.Column(db.String(100))
    patient_condition = db.Column(db.Text)
    status = db.Column(db.String(20), default='requested')
    ambulance_number = db.Column(db.String(50))
    driver_name = db.Column(db.String(100))
    driver_phone = db.Column(db.String(20))
    estimated_arrival = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref='ambulance_bookings')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_type' not in session or session['user_type'] not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    try:
        hospitals = Hospital.query.all()
        
        # Get real counts from database
        total_doctors = Doctor.query.count()
        total_hospitals = Hospital.query.count()
        total_appointments = Appointment.query.count()
        
        # Get monthly appointments (current month)
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_appointments = Appointment.query.filter(
            db.extract('month', Appointment.created_at) == current_month,
            db.extract('year', Appointment.created_at) == current_year
        ).count()
        
        return render_template('index.html', 
                             hospitals=hospitals,
                             total_doctors=total_doctors,
                             total_hospitals=total_hospitals,
                             total_appointments=total_appointments,
                             monthly_appointments=monthly_appointments)
    except Exception as e:
        # Database not initialized - show setup message
        return f"""
        <html>
        <head>
            <title>SmartClinic AI - Setup Required</title>
            <style>
                body {{
                    font-family: 'Poppins', sans-serif;
                    background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    border: 2px solid #00f5ff;
                    box-shadow: 0 0 30px rgba(0, 245, 255, 0.3);
                }}
                h1 {{ color: #00f5ff; margin-bottom: 20px; }}
                .btn {{
                    display: inline-block;
                    padding: 15px 40px;
                    background: linear-gradient(135deg, #00f5ff, #ff006e);
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-size: 18px;
                    margin-top: 20px;
                    transition: transform 0.3s;
                }}
                .btn:hover {{ transform: scale(1.05); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏥 SmartClinic AI</h1>
                <p>Database setup required!</p>
                <p>Click the button below to initialize the database:</p>
                <a href="/setup-database-now" class="btn">Initialize Database</a>
            </div>
        </body>
        </html>
        """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.clear()
    user_type = request.args.get('user_type', 'patient')
    next_url = request.args.get('next')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'patient')
        if not email or not password:
            flash('Please provide both email and password', 'danger')
            return render_template('login.html', user_type=user_type)
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if user.user_type != user_type:
                flash(f'This login is for {user_type}s only. Please use the correct login page.', 'danger')
                return render_template('login.html', user_type=user_type)
            session.clear()
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['user_name'] = user.name
            flash('Logged in successfully!', 'success')
            if next_url:
                return redirect(next_url)
            if user.user_type == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user.user_type == 'hospital_admin':
                return redirect(url_for('hospital_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', user_type=user_type, next=next_url)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        user_type = request.form['user_type']
        phone = request.form['phone']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            user_type=user_type,
            phone=phone,
            age=request.form.get('age') if request.form.get('age') else None,
            gender=request.form.get('gender') if request.form.get('gender') else None,
            blood_group=request.form.get('blood_group') if request.form.get('blood_group') else None,
            height=float(request.form.get('height')) if request.form.get('height') else None,
            weight=float(request.form.get('weight')) if request.form.get('weight') else None,
            address=request.form.get('address') if request.form.get('address') else None,
            emergency_contact=request.form.get('emergency_contact') if request.form.get('emergency_contact') else None
        )
        db.session.add(user)
        db.session.commit()
        if user_type == 'hospital_admin':
            hospital = Hospital(
                name=request.form['hospital_name'],
                address=request.form['hospital_address'],
                contact=phone,
                admin_id=user.id,
                description=request.form.get('hospital_description', '')
            )
            db.session.add(hospital)
            db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/hospitals')
def list_hospitals():
    hospitals = Hospital.query.all()
    return render_template('hospitals.html', hospitals=hospitals)

@app.route('/emergency')
def emergency():
    hospitals = Hospital.query.all()
    return render_template('emergency.html', hospitals=hospitals, google_maps_key=GOOGLE_MAPS_API_KEY)

@app.route('/location-test')
def location_test():
    return render_template('location_test.html')

@app.route('/register_hospital', methods=['GET', 'POST'])
@login_required
@role_required(['hospital_admin'])
def register_hospital():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        contact = request.form.get('contact')
        description = request.form.get('description')
        if not all([name, address, contact]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('register_hospital'))
        try:
            hospital = Hospital(
                name=name,
                address=address,
                contact=contact,
                description=description,
                admin_id=session['user_id']
            )
            db.session.add(hospital)
            db.session.commit()
            flash('Hospital registered successfully!', 'success')
            return redirect(url_for('hospital_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error registering hospital. Please try again.', 'danger')
            return redirect(url_for('register_hospital'))
    return render_template('hospital/register.html')

@app.route('/add_doctor/<int:hospital_id>', methods=['GET', 'POST'])
@login_required
@role_required(['hospital_admin'])
def add_doctor_to_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    if hospital.admin_id != session['user_id']:
        flash('You do not have permission to add doctors to this hospital.', 'danger')
        return redirect(url_for('hospital_dashboard'))
    if request.method == 'POST':
        try:
            email = request.form['email']
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash(f'Email {email} is already registered. Please use a different email.', 'danger')
                return redirect(url_for('add_doctor_to_hospital', hospital_id=hospital_id))
            doctor_user = User(
                name=request.form['name'],
                email=email,
                password_hash=generate_password_hash(request.form['password']),
                user_type='doctor'
            )
            db.session.add(doctor_user)
            db.session.flush()
            doctor = Doctor(
                user_id=doctor_user.id,
                hospital_id=hospital.id,
                specialization=request.form['specialization'],
                experience=int(request.form['experience']),
                consultation_fee=float(request.form['consultation_fee']),
                about=request.form.get('about', '')
            )
            db.session.add(doctor)
            db.session.commit()
            flash(f'Doctor {doctor_user.name} added successfully!', 'success')
            return redirect(url_for('hospital_dashboard'))
        except ValueError as e:
            db.session.rollback()
            flash('Invalid input. Please check experience and consultation fee are valid numbers.', 'danger')
            return redirect(url_for('add_doctor_to_hospital', hospital_id=hospital_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding doctor: {str(e)}', 'danger')
            return redirect(url_for('add_doctor_to_hospital', hospital_id=hospital_id))
    return render_template('hospital/add_doctor.html', hospital=hospital)

@app.route('/add_doctor', methods=['POST'])
@login_required
def add_doctor():
    if session.get('user_type') != 'hospital_admin':
        flash('Only hospitals can add doctors', 'danger')
        return redirect(url_for('index'))
    try:
        hospital = Hospital.query.filter_by(admin_id=session.get('user_id')).first()
        if not hospital:
            flash('Hospital not found', 'danger')
            return redirect(url_for('index'))
        email = request.form['email']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(f'Email {email} is already registered. Please use a different email.', 'danger')
            return redirect(url_for('hospital_dashboard'))
        doctor_user = User(
            name=request.form['name'],
            email=email,
            password_hash=generate_password_hash(request.form['password']),
            user_type='doctor'
        )
        db.session.add(doctor_user)
        db.session.flush()
        doctor = Doctor(
            user_id=doctor_user.id,
            hospital_id=hospital.id,
            specialization=request.form['specialization'],
            experience=int(request.form['experience']),
            consultation_fee=float(request.form['consultation_fee']),
            about=request.form.get('about', '')
        )
        db.session.add(doctor)
        db.session.commit()
        flash(f'Doctor {doctor_user.name} added successfully!', 'success')
        return redirect(url_for('hospital_dashboard'))
    except ValueError as e:
        db.session.rollback()
        flash('Invalid input. Please check experience and consultation fee are valid numbers.', 'danger')
        return redirect(url_for('hospital_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding doctor: {str(e)}', 'danger')
        return redirect(url_for('hospital_dashboard'))

@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@role_required(['patient'])
def book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        symptoms = request.form.get('symptoms')
        if not appointment_date or not appointment_time:
            flash('Please select both date and time for the appointment.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id))
        try:
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
            if appointment_datetime <= datetime.now():
                flash('Please select a future date and time.', 'danger')
                return redirect(url_for('book_appointment', doctor_id=doctor_id))
            appointment = Appointment(
                doctor_id=doctor_id,
                patient_id=session['user_id'],
                hospital_id=doctor.hospital_id,
                appointment_time=appointment_datetime,
                symptoms=symptoms,
                status='pending'
            )
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment booked successfully! Waiting for doctor approval.', 'success')
            return redirect(url_for('patient_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error booking appointment. Please try again.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id))
    return render_template('book_appointment.html', doctor=doctor, today=datetime.now())

@app.route('/patient/dashboard')
@login_required
@role_required(['patient'])
def patient_dashboard():
    user = User.query.get(session['user_id'])
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=session['user_id']
    ).filter(
        Appointment.appointment_time > datetime.now(),
        Appointment.status.in_(['pending', 'approved'])
    ).order_by(Appointment.appointment_time).all()
    past_appointments = Appointment.query.filter_by(
        patient_id=session['user_id']
    ).filter(
        Appointment.status.in_(['completed', 'cancelled'])
    ).order_by(Appointment.appointment_time.desc()).all()
    return render_template('patient/dashboard.html', user=user, upcoming_appointments=upcoming_appointments, past_appointments=past_appointments)

@app.route('/patient/medical-history')
@login_required
@role_required(['patient'])
def patient_medical_history():
    user = User.query.get(session['user_id'])
    medical_history = Appointment.query.filter_by(
        patient_id=session['user_id'],
        status='completed'
    ).order_by(Appointment.completed_at.desc()).all()
    return render_template('patient/medical_history.html', user=user, medical_history=medical_history)

@app.route('/patient/appointment/<int:appointment_id>')
@login_required
@role_required(['patient'])
def view_appointment_details(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('patient_dashboard'))
    return render_template('patient/appointment_details.html', appointment=appointment)

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if session.get('user_type') != 'doctor':
        flash('Access denied. This page is only for doctors.', 'danger')
        return redirect(url_for('index'))
    try:
        doctor = Doctor.query.filter_by(user_id=session.get('user_id')).first()
        if not doctor:
            flash('Doctor profile not found.', 'danger')
            return redirect(url_for('index'))
        today = datetime.now().date()
        pending_appointments = (Appointment.query
            .join(User, User.id == Appointment.patient_id)
            .filter(Appointment.doctor_id == doctor.id, Appointment.status == 'pending')
            .order_by(Appointment.appointment_time).all())
        todays_appointments = (Appointment.query
            .join(User, User.id == Appointment.patient_id)
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_time >= datetime.combine(today, datetime.min.time()),
                Appointment.appointment_time < datetime.combine(today, datetime.max.time()),
                Appointment.status == 'approved'
            ).order_by(Appointment.appointment_time).all())
        upcoming_appointments = (Appointment.query
            .join(User, User.id == Appointment.patient_id)
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_time > datetime.combine(today, datetime.max.time()),
                Appointment.status == 'approved'
            ).order_by(Appointment.appointment_time).all())
        completed_appointments = (Appointment.query
            .join(User, User.id == Appointment.patient_id)
            .filter(Appointment.doctor_id == doctor.id, Appointment.status == 'completed')
            .order_by(Appointment.appointment_time.desc()).all())
        return render_template('doctor/dashboard.html',
            doctor=doctor,
            pending_appointments=pending_appointments,
            todays_appointments=todays_appointments,
            upcoming_appointments=upcoming_appointments,
            completed_appointments=completed_appointments)
    except Exception as e:
        flash('An error occurred while loading the dashboard.', 'danger')
        return redirect(url_for('index'))

@app.route('/hospital/dashboard')
@login_required
def hospital_dashboard():
    if session.get('user_type') != 'hospital_admin':
        flash('Access denied. This page is only for hospitals.', 'danger')
        return redirect(url_for('index'))
    try:
        hospital = Hospital.query.filter_by(admin_id=session.get('user_id')).first()
        if not hospital:
            flash('Hospital profile not found.', 'danger')
            return redirect(url_for('index'))
        doctors = Doctor.query.filter_by(hospital_id=hospital.id).all()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        today_appointments = (Appointment.query
            .join(Doctor)
            .filter(
                Doctor.hospital_id == hospital.id,
                Appointment.appointment_time >= datetime.combine(today, datetime.min.time()),
                Appointment.appointment_time < datetime.combine(tomorrow, datetime.min.time())
            ).order_by(Appointment.appointment_time).all())
        pending_appointments = (Appointment.query
            .join(Doctor)
            .filter(Doctor.hospital_id == hospital.id, Appointment.status == 'pending')
            .order_by(Appointment.appointment_time).all())
        completed_appointments = (Appointment.query
            .join(Doctor)
            .filter(Doctor.hospital_id == hospital.id, Appointment.status == 'completed')
            .order_by(Appointment.appointment_time.desc()).all())
        return render_template('hospital/dashboard.html',
            hospital=hospital,
            doctors=doctors,
            today_appointments=today_appointments,
            pending_appointments=pending_appointments,
            completed_appointments=completed_appointments)
    except Exception as e:
        flash('An error occurred while loading the dashboard.', 'danger')
        return redirect(url_for('index'))

@app.route('/hospital/<int:hospital_id>')
def hospital_details(hospital_id):
    hospital = Hospital.query.options(db.joinedload(Hospital.doctors).joinedload(Doctor.user)).get_or_404(hospital_id)
    today = datetime.now().date()
    return render_template('hospital_details.html', hospital=hospital, today=today)

@app.route('/update_appointment_status', methods=['POST'])
@login_required
def update_appointment_status():
    if session.get('user_type') != 'doctor':
        return jsonify({'success': False, 'message': 'Only doctors can update appointments'}), 403
    try:
        data = request.get_json()
        appointment_id = data.get('appointment_id')
        new_status = data.get('status')
        if not appointment_id or not new_status:
            return jsonify({'success': False, 'message': 'Missing appointment_id or status'}), 400
        doctor = Doctor.query.filter_by(user_id=session.get('user_id')).first()
        if not doctor:
            return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'success': False, 'message': 'Appointment not found'}), 404
        if appointment.doctor_id != doctor.id:
            return jsonify({'success': False, 'message': 'You can only update your own appointments'}), 403
        appointment.status = new_status
        if new_status == 'completed':
            appointment.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': f'Appointment {new_status} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while updating the appointment'}), 500

@app.route('/doctor/appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def doctor_appointment_details(appointment_id):
    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != doctor.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    if request.method == 'POST':
        try:
            appointment.diagnosis = request.form.get('diagnosis')
            appointment.prescription = request.form.get('prescription')
            appointment.treatment_plan = request.form.get('treatment_plan')
            appointment.test_results = request.form.get('test_results')
            appointment.doctor_notes = request.form.get('doctor_notes')
            follow_up = request.form.get('follow_up_date')
            if follow_up:
                appointment.follow_up_date = datetime.strptime(follow_up, "%Y-%m-%d")
            if request.form.get('mark_completed'):
                appointment.status = 'completed'
                appointment.completed_at = datetime.utcnow()
            db.session.commit()
            flash('Medical records updated successfully!', 'success')
            return redirect(url_for('doctor_appointment_details', appointment_id=appointment_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating medical records.', 'danger')
    return render_template('doctor/appointment_details.html', appointment=appointment, doctor=doctor)

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.patient_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        if appointment.status != 'pending':
            return jsonify({'success': False, 'message': 'Can only cancel pending appointments'}), 400
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/emergency/contacts')
@login_required
@role_required(['patient'])
def emergency_contacts():
    contacts = EmergencyContact.query.filter_by(user_id=session['user_id']).order_by(EmergencyContact.is_primary.desc()).all()
    return render_template('patient/emergency_contacts.html', contacts=contacts)

@app.route('/emergency/contacts/add', methods=['POST'])
@login_required
@role_required(['patient'])
def add_emergency_contact():
    try:
        if request.form.get('is_primary') == 'on':
            EmergencyContact.query.filter_by(user_id=session['user_id'], is_primary=True).update({'is_primary': False})
        contact = EmergencyContact(
            user_id=session['user_id'],
            name=request.form['name'],
            relationship=request.form['relationship'],
            phone=request.form['phone'],
            email=request.form.get('email'),
            is_primary=request.form.get('is_primary') == 'on'
        )
        db.session.add(contact)
        db.session.commit()
        flash('Emergency contact added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding emergency contact.', 'danger')
    return redirect(url_for('emergency_contacts'))

@app.route('/emergency/contacts/delete/<int:contact_id>', methods=['POST'])
@login_required
@role_required(['patient'])
def delete_emergency_contact(contact_id):
    try:
        contact = EmergencyContact.query.get_or_404(contact_id)
        if contact.user_id != session['user_id']:
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('emergency_contacts'))
        db.session.delete(contact)
        db.session.commit()
        flash('Emergency contact deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting emergency contact.', 'danger')
    return redirect(url_for('emergency_contacts'))

@app.route('/emergency/ambulance/book', methods=['POST'])
@login_required
def book_ambulance():
    try:
        booking = AmbulanceBooking(
            user_id=session['user_id'],
            patient_name=request.form['patient_name'],
            phone=request.form['phone'],
            pickup_address=request.form['pickup_address'],
            pickup_lat=float(request.form.get('pickup_lat', 0)),
            pickup_lng=float(request.form.get('pickup_lng', 0)),
            destination_hospital=request.form.get('destination_hospital'),
            destination_lat=float(request.form.get('destination_lat', 0)) if request.form.get('destination_lat') else None,
            destination_lng=float(request.form.get('destination_lng', 0)) if request.form.get('destination_lng') else None,
            emergency_type=request.form.get('emergency_type'),
            patient_condition=request.form.get('patient_condition'),
            status='requested'
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Ambulance requested successfully! Emergency services will contact you shortly.',
            'booking_id': booking.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/emergency/ambulance/status/<int:booking_id>')
@login_required
def ambulance_status(booking_id):
    booking = AmbulanceBooking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    return jsonify({
        'success': True,
        'status': booking.status,
        'ambulance_number': booking.ambulance_number,
        'driver_name': booking.driver_name,
        'driver_phone': booking.driver_phone,
        'estimated_arrival': booking.estimated_arrival.isoformat() if booking.estimated_arrival else None
    })

@app.route('/emergency/my-bookings')
@login_required
def my_ambulance_bookings():
    bookings = AmbulanceBooking.query.filter_by(user_id=session['user_id']).order_by(AmbulanceBooking.created_at.desc()).all()
    return render_template('patient/ambulance_bookings.html', bookings=bookings)

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        print(f"Received message: {user_message}")
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
            
        if not model:
            print("Warning: Model not initialized - running in demo mode")
            return jsonify({
                'response': "I'm currently in demo mode. To enable real AI responses, please add your Gemini API key to the .env file."
            })
            
        total_hospitals = Hospital.query.count()
        total_doctors = Doctor.query.count()
        total_patients = User.query.filter_by(user_type='patient').count()
        total_appointments = Appointment.query.count()
        pending_appointments = Appointment.query.filter_by(status='pending').count()
        completed_appointments = Appointment.query.filter_by(status='completed').count()
        
        hospitals_info = []
        hospitals = Hospital.query.all()
        for hospital in hospitals:
            doctors_count = Doctor.query.filter_by(hospital_id=hospital.id).count()
            hospitals_info.append(f"- {hospital.name} ({doctors_count} doctors)")
        
        specializations = db.session.query(Doctor.specialization).distinct().all()
        specializations_list = [s[0] for s in specializations]
        system_prompt = f"""You are SmartClinic AI, an intelligent and comprehensive medical assistant. You MUST provide DETAILED, THOROUGH responses like a knowledgeable doctor would.

SYSTEM DATA:
- Hospitals: {total_hospitals} | Doctors: {total_doctors} | Patients: {total_patients}
- Our Hospitals: {', '.join([h.split(' (')[0].replace('- ', '') for h in hospitals_info]) if hospitals_info else "Multiple partner hospitals"}
- Specializations: {', '.join(specializations_list) if specializations_list else "All major specializations"}

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THIS FORMAT FOR EVERY HEALTH QUERY:

When someone mentions ANY symptom or health issue (like back pain, headache, fever, cold, cough, etc.), you MUST provide a COMPLETE, DETAILED response with ALL of these sections:

## Understanding [Condition]:
- Explain what the condition is
- List ALL possible causes (minimum 5-6 causes)
- Explain the types if applicable

## Home Remedies & Self-Care:
- List 5-6 home remedies with detailed instructions
- Include rest, diet, lifestyle changes
- Be specific with instructions

## Common Medications:
- List 3-4 relevant medications with EXACT names
- Include DOSAGE for adults (e.g., "500mg every 6 hours")
- Include how to take them (before/after food)
- Example format: "**Paracetamol (Dolo 650)**: 500-650mg every 4-6 hours as needed, maximum 4g per day"

## When to See a Doctor:
- List 5-6 warning signs that need immediate medical attention
- Be specific about symptoms

## Recommended Specialist:
- Suggest the appropriate specialist (Orthopedic, General Physician, Neurologist, etc.)
- Explain why this specialist is recommended

## ⚠️ Important Disclaimer:
Always end with: "⚠️ Please consult with a doctor before taking any medication. You can book an appointment through our SmartClinic website to get proper diagnosis and treatment."

EXAMPLE - If someone says "I have back pain", respond like this:

"I understand you're experiencing back pain. Let me provide you with comprehensive information:

## Understanding Back Pain:
Back pain is one of the most common medical problems. It can range from a dull, constant ache to sudden, sharp pain. Common causes include:
- **Muscle strain**: From heavy lifting or sudden movements
- **Poor posture**: Sitting or standing incorrectly for long periods
- **Herniated disc**: When disc material presses on nerves
- **Arthritis**: Osteoarthritis can affect the lower back
- **Skeletal irregularities**: Such as scoliosis
- **Osteoporosis**: Bones becoming brittle and porous

## Home Remedies & Self-Care:
- **Rest**: Avoid strenuous activities for 1-2 days
- **Ice/Heat therapy**: Apply ice for first 48 hours, then switch to heat
- **Gentle stretching**: Light yoga or stretching exercises
- **Maintain good posture**: Use ergonomic chairs
- **Sleep position**: Sleep on your side with a pillow between knees
- **Stay active**: Light walking helps prevent stiffness

## Common Medications:
- **Paracetamol (Dolo 650)**: 500-650mg every 4-6 hours for pain relief
- **Ibuprofen (Brufen)**: 400mg every 6-8 hours with food for pain and inflammation
- **Diclofenac gel**: Apply topically 3-4 times daily on affected area
- **Muscle relaxants (Thiocolchicoside)**: 4mg twice daily for muscle spasms

## When to See a Doctor:
- Pain persists for more than 2 weeks
- Numbness or tingling in legs
- Difficulty urinating or loss of bladder control
- Fever along with back pain
- Pain after an injury or fall
- Unexplained weight loss with back pain

## Recommended Specialist:
An **Orthopedic** specialist is recommended for back pain. They specialize in musculoskeletal conditions and can provide proper diagnosis through physical examination and imaging tests.

⚠️ Please consult with a doctor before taking any medication. You can book an appointment through our SmartClinic website to get proper diagnosis and treatment."

REMEMBER: ALWAYS give this level of detail for ANY health question. Never give short responses. Be comprehensive and helpful like a real doctor consultation.

User message: """
        response = model.generate_content(system_prompt + user_message)
        ai_response = response.text
        
        print(f"AI Response generated successfully")
        
        return jsonify({'response': ai_response})
    except Exception as e:
        error_msg = str(e)
        print(f"AI Chat Error: {error_msg}")
        import traceback
        traceback.print_exc()
        
        if '429' in error_msg or 'quota' in error_msg.lower():
            return jsonify({
                'response': "⚠️ I'm currently experiencing high demand. Please try again in a few seconds, or try again later. Our AI service has a daily limit on the free tier."
            })
        return jsonify({
            'response': f"I'm having trouble processing your request. Error: {error_msg}"
        })

@app.route('/setup-database-now')
def setup_database():
    """One-time database setup endpoint - visit this URL to initialize the database"""
    try:
        # Create all tables
        with app.app_context():
            db.create_all()
        
        # Check if data already exists
        if User.query.first():
            return jsonify({
                'status': 'success',
                'message': 'Database already initialized!',
                'tables': 'All tables exist',
                'data': 'Sample data already present'
            })
        
        # Add sample users
        patient_user = User(
            email='patient@example.com',
            password_hash=generate_password_hash('password123'),
            name='John Patient',
            user_type='patient',
            phone='1234567890',
            age=30,
            gender='Male',
            blood_group='O+',
            address='123 Patient St'
        )
        
        hospital_admin = User(
            email='admin@hospital.com',
            password_hash=generate_password_hash('password123'),
            name='Hospital Admin',
            user_type='hospital_admin',
            phone='9876543210'
        )
        
        doctor_user = User(
            email='doctor@example.com',
            password_hash=generate_password_hash('password123'),
            name='Dr. Smith',
            user_type='doctor',
            phone='5555555555'
        )
        
        db.session.add_all([patient_user, hospital_admin, doctor_user])
        db.session.commit()
        
        # Add hospital
        hospital = Hospital(
            name='City General Hospital',
            address='456 Hospital Ave, Medical District',
            contact='9876543210',
            admin_id=hospital_admin.id,
            description='Leading healthcare provider'
        )
        db.session.add(hospital)
        db.session.commit()
        
        # Add doctor
        doctor = Doctor(
            user_id=doctor_user.id,
            hospital_id=hospital.id,
            specialization='General Medicine',
            experience=10,
            consultation_fee=50.00,
            about='Experienced general physician'
        )
        db.session.add(doctor)
        db.session.commit()
        
        # Add sample appointment
        appointment = Appointment(
            doctor_id=doctor.id,
            patient_id=patient_user.id,
            hospital_id=hospital.id,
            appointment_time=datetime.now() + timedelta(days=1),
            symptoms='Regular checkup',
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '✅ Database initialized successfully!',
            'tables_created': 'All tables created',
            'sample_data': {
                'patients': 1,
                'doctors': 1,
                'hospitals': 1,
                'appointments': 1
            },
            'login_credentials': {
                'patient': 'patient@example.com / password123',
                'doctor': 'doctor@example.com / password123',
                'hospital': 'admin@hospital.com / password123'
            },
            'next_step': 'Visit https://smartcinicai.onrender.com to use the app!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/reset-user-password', methods=['POST'])
def reset_user_password():
    """
    Reset password for a user (for admin use)
    """
    try:
        data = request.get_json()
        secret = data.get('secret', '')
        
        if secret != 'import-data-2026':
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        email = data.get('email', '')
        new_password = data.get('new_password', '')
        
        if not email or not new_password:
            return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Password reset successfully for {email}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/smart-import-data', methods=['POST'])
def smart_import_data():
    """
    Smart import that handles foreign keys properly
    """
    try:
        data = request.get_json()
        secret = data.get('secret', '')
        
        if secret != 'import-data-2026':
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        import_data = data.get('data', {})
        imported = {'users': 0, 'hospitals': 0, 'doctors': 0}
        
        # Import users first
        for user_data in import_data.get('users', []):
            existing = User.query.filter_by(email=user_data['email']).first()
            if not existing:
                user = User(
                    email=user_data['email'],
                    password_hash=generate_password_hash(user_data['password']),
                    name=user_data['name'],
                    user_type=user_data['user_type'],
                    phone=user_data.get('phone')
                )
                db.session.add(user)
                imported['users'] += 1
        
        db.session.commit()
        
        # Import hospitals
        for hosp_data in import_data.get('hospitals', []):
            existing = Hospital.query.filter_by(name=hosp_data['name']).first()
            if not existing:
                admin = User.query.filter_by(email=hosp_data['admin_email']).first()
                if admin:
                    hospital = Hospital(
                        name=hosp_data['name'],
                        address=hosp_data['address'],
                        contact=hosp_data['contact'],
                        admin_id=admin.id,
                        description=hosp_data.get('description', '')
                    )
                    db.session.add(hospital)
                    imported['hospitals'] += 1
        
        db.session.commit()
        
        # Import doctors
        for doc_data in import_data.get('doctors', []):
            existing = User.query.filter_by(email=doc_data['email']).first()
            if not existing:
                user = User(
                    email=doc_data['email'],
                    password_hash=generate_password_hash(doc_data['password']),
                    name=doc_data['name'],
                    user_type='doctor'
                )
                db.session.add(user)
                db.session.flush()
                
                hospital = Hospital.query.filter_by(name=doc_data['hospital_name']).first()
                if hospital:
                    doctor = Doctor(
                        user_id=user.id,
                        hospital_id=hospital.id,
                        specialization=doc_data['specialization'],
                        experience=doc_data['experience'],
                        consultation_fee=doc_data['fee'],
                        about=doc_data.get('about', '')
                    )
                    db.session.add(doctor)
                    imported['doctors'] += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '✅ Data imported successfully!',
            'imported': imported,
            'current_data': {
                'users': User.query.count(),
                'hospitals': Hospital.query.count(),
                'doctors': Doctor.query.count()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/import-production-data', methods=['POST'])
def import_production_data():
    """
    Import data from production_data.sql file
    Security: Requires a secret key to prevent unauthorized access
    """
    try:
        # Get the secret key from request
        data = request.get_json()
        secret = data.get('secret', '')
        
        # Simple security check - you can change this secret
        if secret != 'import-data-2026':
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized: Invalid secret key'
            }), 403
        
        # Read the SQL file
        import os
        sql_file_path = os.path.join(os.path.dirname(__file__), 'production_data.sql')
        
        if not os.path.exists(sql_file_path):
            return jsonify({
                'status': 'error',
                'message': 'production_data.sql file not found. Please upload it first.'
            }), 404
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Parse and execute SQL statements
        statements = sql_content.split(';')
        executed = 0
        errors = []
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--') and 'INSERT INTO' in statement:
                try:
                    db.session.execute(db.text(statement))
                    executed += 1
                except Exception as e:
                    error_msg = str(e)
                    # Skip duplicate entry errors
                    if 'Duplicate entry' not in error_msg and 'UNIQUE constraint' not in error_msg:
                        errors.append(f"Error in statement: {error_msg[:100]}")
        
        db.session.commit()
        
        # Count imported data
        total_users = User.query.count()
        total_hospitals = Hospital.query.count()
        total_doctors = Doctor.query.count()
        
        return jsonify({
            'status': 'success',
            'message': '✅ Data imported successfully!',
            'executed_statements': executed,
            'errors': errors if errors else 'None',
            'current_data': {
                'users': total_users,
                'hospitals': total_hospitals,
                'doctors': total_doctors
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

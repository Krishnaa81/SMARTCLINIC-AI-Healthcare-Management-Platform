from app import app, db
from werkzeug.security import generate_password_hash

print("Creating database tables...")
with app.app_context():
    db.create_all()
    print("✓ All tables created successfully!")
    
    # Add sample users
    from app import User, Hospital, Doctor
    
    # Check if sample data exists
    if User.query.count() == 0:
        print("\nAdding sample data...")
        
        # Create sample patient
        patient = User(
            email='patient@example.com',
            password_hash=generate_password_hash('password123'),
            name='John Doe',
            user_type='patient',
            phone='1234567890',
            age=30,
            gender='Male',
            blood_group='O+',
            address='123 Main St'
        )
        db.session.add(patient)
        
        # Create sample hospital admin
        admin = User(
            email='admin@hospital.com',
            password_hash=generate_password_hash('password123'),
            name='Hospital Admin',
            user_type='hospital_admin',
            phone='0987654321'
        )
        db.session.add(admin)
        db.session.commit()
        
        # Create sample hospital
        hospital = Hospital(
            name='City General Hospital',
            address='456 Hospital Ave',
            contact='0987654321',
            admin_id=admin.id,
            description='Leading healthcare provider'
        )
        db.session.add(hospital)
        db.session.commit()
        
        # Create sample doctor user
        doctor_user = User(
            email='doctor@example.com',
            password_hash=generate_password_hash('password123'),
            name='Dr. Sarah Smith',
            user_type='doctor',
            phone='5555555555'
        )
        db.session.add(doctor_user)
        db.session.commit()
        
        # Create sample doctor
        doctor = Doctor(
            user_id=doctor_user.id,
            hospital_id=hospital.id,
            specialization='Cardiology',
            experience=10,
            consultation_fee=100.00,
            about='Expert cardiologist with 10 years experience'
        )
        db.session.add(doctor)
        db.session.commit()
        
        print("✓ Sample data added successfully!")
        print("\n" + "="*60)
        print("SAMPLE LOGIN CREDENTIALS:")
        print("="*60)
        print("\n👤 Patient Login:")
        print("   Email: patient@example.com")
        print("   Password: password123")
        print("\n👨‍⚕️ Doctor Login:")
        print("   Email: doctor@example.com")
        print("   Password: password123")
        print("\n🏥 Hospital Admin Login:")
        print("   Email: admin@hospital.com")
        print("   Password: password123")
        print("="*60)
    else:
        print("✓ Sample data already exists!")

print("\n✅ Database setup complete!")
print("\nYou can now run: python app.py")

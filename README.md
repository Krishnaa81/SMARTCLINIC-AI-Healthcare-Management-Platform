# 🏥 SmartClinic AI - Doctor Appointment System

AI-powered doctor appointment booking system with modern dark theme and intelligent chatbot.
https://smartcinicai.onrender.com/

## ✨ Features

- 🎨 **Modern Dark Theme** - Beautiful gradient design with cyan, purple, and magenta colors
- 🤖 **AI Chatbot** - Powered by Google Gemini AI for medical assistance
- 📅 **Appointment Booking** - Easy scheduling with doctors
- 🚑 **Emergency Services** - Quick access to nearby hospitals and ambulances
- 👥 **Multi-User System** - Separate dashboards for patients, doctors, and hospitals
- 🗺️ **Location Services** - Find nearby hospitals with interactive maps
- 📱 **Responsive Design** - Works on all devices
- 🔐 **Secure Authentication** - User login and registration system

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MySQL database

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Krishnaa81/SMARTCLINIC-AI-Healthcare-Management-Platform.git
cd SMARTCLINIC-AI-Healthcare-Management-Platform
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r backend/requirements.txt
```

4. **Setup database**
```bash
python backend/setup_db.py
```

5. **Configure environment variables**
```bash
# Copy .env.example to .env
cp backend/.env.example backend/.env

# Edit .env with your settings
```

6. **Run the application**
```bash
# Windows
run.bat

# Mac/Linux
cd backend
python app.py
```

7. **Open in browser**
```
http://localhost:5000
```

## 🗄️ Database Setup

The application uses MySQL. Update your database credentials in `backend/.env`:

```env
DATABASE_URL=mysql+pymysql://username:password@localhost/clinic_db
SECRET_KEY=your-secret-key-here
```

Run the setup script to create tables and sample data:
```bash
python backend/setup_db.py
```

## 🎯 User Roles

### Patient
- Book appointments with doctors
- View medical history
- Manage emergency contacts
- Access emergency services

### Doctor
- View and manage appointments
- Add medical records
- Update patient diagnoses
- Manage prescriptions

### Hospital Admin
- Add doctors to hospital
- Manage appointments
- View hospital statistics
- Monitor daily schedule

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost/clinic_db

# Security
SECRET_KEY=your-secret-key-here

# Optional: AI Features
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_MAPS_API_KEY=your-maps-api-key

# Environment
FLASK_ENV=development
```

## 📁 Project Structure

```
doctor-appointment-system/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── config.py           # Configuration
│   ├── setup_db.py         # Database setup script
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       ├── index.html      # Homepage
│       ├── patient/        # Patient pages
│       ├── doctor/         # Doctor pages
│       └── hospital/       # Hospital pages
└── README.md
```

## 🎨 Design Features

- **Dark Theme**: Modern gradient background with glassmorphism effects
- **Color Scheme**: Cyan (#00f5ff), Purple (#8338ec), Magenta (#ff006e)
- **Animations**: Smooth transitions and hover effects
- **Icons**: Colorful emojis instead of icon fonts
- **Typography**: Poppins font family throughout

## 🚀 Deployment

### Deploy to Render (Free)

1. Push code to GitHub
2. Sign up at https://render.com
3. Create new Web Service
4. Connect your repository
5. Set environment variables
6. Deploy!

See deployment guides in the repository for detailed instructions.

## 🛠️ Technologies Used

- **Backend**: Flask, SQLAlchemy, MySQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI**: Google Gemini AI
- **Maps**: Google Maps API, Leaflet.js
- **Authentication**: Flask sessions, Werkzeug security

## 📝 Sample Credentials

After running `setup_db.py`, you can login with:

**Patient:**
- Email: patient@example.com
- Password: password123

**Doctor:**
- Email: doctor@example.com
- Password: password123

**Hospital Admin:**
- Email: admin@hospital.com
- Password: password123

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Krishna Reddy**
- GitHub: [@Krishnaa81](https://github.com/Krishnaa81)

## 🙏 Acknowledgments

- Google Gemini AI for chatbot functionality
- Bootstrap for responsive design
- Leaflet.js for interactive maps
- Font Awesome for icons (replaced with emojis)

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ by Krishna Reddy**

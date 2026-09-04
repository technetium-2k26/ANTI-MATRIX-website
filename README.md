# Anti-Matrix — Python Flask Web Application

Anti-Matrix is an enterprise digital transformation, engineering, and artificial intelligence consultancy web application.

This project was migrated from **React 19 + JSX + Vite** to a pure **Python 3.11+ / Flask 3.x** server-rendered web application with Jinja2 templates, vanilla CSS3 design system, vanilla JavaScript micro-interactions, SQLite / PostgreSQL SQLAlchemy database models, Flask-Login authentication, and CSRF protection.

---

## 🚀 Key Features & Architecture

- **Backend**: Python 3.11+ / Flask 3.1.x
- **Templating**: Jinja2 with clean template inheritance (`base.html`, components, pages, auth, errors)
- **Styling**: Pure CSS3 (`static/css/main.css`) preserving the complete emerald-neon dark glassmorphism design system
- **Frontend Interactivity**: Vanilla JavaScript (`static/js/main.js`, `navbar.js`, `auth.js`) for scroll-reveals, mobile navigation drawer, FAQ/careers accordions, live password toggles, and async AJAX submissions
- **Authentication**: Flask-Login session management with PBKDF2/SHA256 password hashing
- **Database**: Flask-SQLAlchemy (`User`, `ContactInquiry`) with SQLite for development and seamless PostgreSQL support in production
- **Security**: Flask-WTF CSRF protection, secure HTTP headers, and strict form validation

---

## 🛠️ Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- pip and virtualenv

### 2. Setup Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and adjust settings as needed:
```bash
cp .env.example .env
```

### 5. Run the Application
```bash
python app.py
```
Access the application in your browser at `http://127.0.0.1:5000/`.

---

## 🚢 Production Deployment

For production environments, run via Gunicorn WSGI:
```bash
gunicorn app:app
```
(Defined in `Procfile`: `web: gunicorn app:app`)

---

## 📁 Project Structure

```text
ANTI-MATRIX-website/
├── app.py                  # Application factory and lifecycle hooks
├── config.py               # Config profiles (Development, Production, Testing)
├── requirements.txt        # Production Python dependencies
├── Procfile                # WSGI process definition
├── .env.example            # Environment variable template
├── models/
│   ├── __init__.py         # SQLAlchemy db instance
│   ├── user.py             # User model with Flask-Login & password hashing
│   └── contact.py          # ContactInquiry model
├── routes/
│   ├── __init__.py
│   ├── main.py             # Public & protected page routes
│   ├── auth.py             # Login, signup, and logout flows
│   └── contact.py          # Contact submission endpoint
├── templates/
│   ├── base.html           # Master layout skeleton
│   ├── components/         # navbar.html, footer.html, logo.html, icons.html
│   ├── pages/              # home, about, services, pricing, careers, contact, privacy, terms
│   ├── auth/               # login.html, signup.html
│   └── errors/             # 404.html
├── static/
│   ├── css/main.css        # Full 1,159-line design system
│   ├── js/                 # main.js, navbar.js, auth.js
│   ├── images/             # PNG logos and hero assets
│   └── svg/                # Vector SVG icons & sprite
└── react_backup/           # Complete archive of original React codebase
```

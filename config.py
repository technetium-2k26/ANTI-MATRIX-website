import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Centralized Server-Side Application Fee Mapping (Enforced strictly on server)
INTERNSHIP_FEES = {
    '1_month': 199,
    '3_months': 399
}

INTERNSHIP_PRICING = {
    '1_month': {
        'duration_key': '1_month',
        'label': '1 Month',
        'amount_inr': 199,
        'amount_paise': 19900,
        'formatted': '₹199'
    },
    '3_months': {
        'duration_key': '3_months',
        'label': '3 Months',
        'amount_inr': 399,
        'amount_paise': 39900,
        'formatted': '₹399'
    }
}

# Indian States and Dependent Cities Mapping
INDIA_STATES_AND_CITIES = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Rajahmundry", "Tirupati", "Kakinada", "Kadapa", "Anantapur", "Eluru", "Ongole", "Other"],
    "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Pasighat", "Tawang", "Ziro", "Bomdila", "Other"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Nagaon", "Tinsukia", "Tezpur", "Bongaigaon", "Other"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", "Darbhanga", "Bihar Sharif", "Arrah", "Begusarai", "Katihar", "Other"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Durg", "Rajnandgaon", "Jagdalpur", "Ambikapur", "Other"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda", "Other"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Junagadh", "Gandhinagar", "Anand", "Navsari", "Morbi", "Bharuch", "Other"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala", "Yamunanagar", "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula", "Other"],
    "Himachal Pradesh": ["Shimla", "Dharamshala", "Solan", "Mandi", "Kullu", "Manali", "Baddi", "Bilaspur", "Hamirpur", "Other"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar", "Hazaribagh", "Giridih", "Ramgarh", "Other"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi-Dharwad", "Mangaluru", "Belagavi", "Davanagere", "Ballari", "Kalaburagi", "Shivamogga", "Tumakuru", "Udupi", "Hassan", "Other"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Palakkad", "Alappuzha", "Kannur", "Kottayam", "Malappuram", "Other"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Dewas", "Satna", "Ratlam", "Rewa", "Other"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Kalyan-Dombivli", "Vasai-Virar", "Chhatrapati Sambhaji Nagar (Aurangabad)", "Navi Mumbai", "Solapur", "Kolhapur", "Amravati", "Nanded", "Other"],
    "Manipur": ["Imphal", "Churachandpur", "Thoubal", "Kakching", "Ukhrul", "Other"],
    "Meghalaya": ["Shillong", "Tura", "Jowai", "Nongpoh", "Baghmara", "Other"],
    "Mizoram": ["Aizawl", "Lunglei", "Champhai", "Serchhip", "Kolasib", "Other"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung", "Tuensang", "Wokha", "Other"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur", "Puri", "Balasore", "Bhadrak", "Other"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali", "Hoshiarpur", "Pathankot", "Other"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer", "Udaipur", "Bhilwara", "Alwar", "Sikar", "Sri Ganganagar", "Other"],
    "Sikkim": ["Gangtok", "Namchi", "Geyzing", "Mangan", "Rangpo", "Other"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli", "Tiruppur", "Vellore", "Erode", "Thoothukudi", "Dindigul", "Thanjavur", "Nagercoil", "Kanchipuram", "Hosur", "Other"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Ramagundam", "Khammam", "Mahbubnagar", "Nalgonda", "Adilabad", "Siddipet", "Other"],
    "Tripura": ["Agartala", "Udaipur", "Dharmanagar", "Kailashahar", "Belonia", "Other"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Prayagraj", "Noida", "Greater Noida", "Ghaziabad", "Meerut", "Bareilly", "Aligarh", "Moradabad", "Saharanpur", "Gorakhpur", "Jhansi", "Mathura", "Other"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", "Rishikesh", "Nainital", "Kashipur", "Other"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri", "Bardhaman", "Kharagpur", "Malda", "Haldia", "Other"],
    "Andaman and Nicobar Islands": ["Port Blair", "Other"],
    "Chandigarh": ["Chandigarh", "Other"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Diu", "Silvassa", "Other"],
    "Delhi": ["New Delhi", "Central Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi", "Dwarka", "Rohini", "Other"],
    "Jammu and Kashmir": ["Srinagar", "Jammu", "Anantnag", "Baramulla", "Udhampur", "Kathua", "Sopore", "Other"],
    "Ladakh": ["Leh", "Kargil", "Other"],
    "Lakshadweep": ["Kavaratti", "Agatti", "Amini", "Andrott", "Other"],
    "Puducherry": ["Puducherry", "Karaikal", "Mahe", "Yanam", "Other"]
}

# Education Levels
EDUCATION_LEVELS = [
    "High School / 12th Standard",
    "Diploma",
    "Bachelor's Degree",
    "Master's Degree",
    "Doctorate / Ph.D",
    "Other"
]

# Common Degrees
COMMON_DEGREES = [
    "B.Tech / B.E. (Bachelor of Technology / Engineering)",
    "B.Sc (Bachelor of Science)",
    "BCA (Bachelor of Computer Applications)",
    "B.Com (Bachelor of Commerce)",
    "BBA (Bachelor of Business Administration)",
    "M.Tech / M.E. (Master of Technology / Engineering)",
    "M.Sc (Master of Science)",
    "MCA (Master of Computer Applications)",
    "MBA (Master of Business Administration)",
    "Diploma in Engineering",
    "Other"
]

# Available Graduation Years (Up to 2029 maximum)
GRADUATION_YEARS = [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029]


def get_internship_fee(duration: str) -> int:
    """Retrieve exact server-calculated fee in INR for given duration."""
    return INTERNSHIP_FEES.get(duration, 0)


def get_database_uri(force_production_check=False):
    """
    Retrieves and normalizes the database URI.
    Supports PostgreSQL (Supabase) and SQLite.
    Normalizes 'postgres://' to 'postgresql://' for SQLAlchemy compatibility.
    In production environments, raises RuntimeError if DATABASE_URL is not set.
    """
    raw_url = os.environ.get('DATABASE_URL', '').strip()
    if raw_url:
        if raw_url.startswith('postgres://'):
            raw_url = 'postgresql://' + raw_url[len('postgres://'):]
        return raw_url

    # Check if production is explicitly configured or running on Render
    is_prod = (
        force_production_check
        or os.environ.get('FLASK_CONFIG', '').lower() == 'production'
        or os.environ.get('FLASK_ENV', '').lower() == 'production'
        or os.environ.get('RENDER', '').lower() == 'true'
    )
    if is_prod and not raw_url:
        raise RuntimeError(
            "CRITICAL CONFIGURATION ERROR: DATABASE_URL environment variable is missing in Production. "
            "Production on Render requires a valid Supabase PostgreSQL connection string."
        )

    return f"sqlite:///{os.path.join(BASE_DIR, 'antimatrix.db')}"


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'antimatrix-dev-secret-key-change-in-prod-2026')
    
    # Database configuration with postgres:// to postgresql:// normalization
    SQLALCHEMY_DATABASE_URI = get_database_uri(force_production_check=False)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy Engine & Connection Pool Options (Optimized for Supabase Pooler / Supavisor & Web Services)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Session & Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Application settings
    APP_NAME = 'Anti-Matrix'
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'contact@anti-matrix.com')
    CAREERS_EMAIL = os.environ.get('CAREERS_EMAIL', 'careers@anti-matrix.com')

    # File Uploads (Resumes and Sensitive Identity Documents)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'resumes')
    UPLOAD_FOLDER_RESUMES = os.path.join(BASE_DIR, 'uploads', 'resumes')
    UPLOAD_FOLDER_DOCUMENTS = os.path.join(BASE_DIR, 'uploads', 'documents')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

    # Cashfree Payment Gateway Settings (Render & Environment Compatible)
    CASHFREE_APP_ID = (os.environ.get('CASHFREE_APP_ID', '').strip() or os.environ.get('CASHFREE_CLIENT_ID', '').strip())
    CASHFREE_SECRET_KEY = (os.environ.get('CASHFREE_SECRET_KEY', '').strip() or os.environ.get('CASHFREE_CLIENT_SECRET', '').strip())
    CASHFREE_CLIENT_ID = CASHFREE_APP_ID
    CASHFREE_CLIENT_SECRET = CASHFREE_SECRET_KEY
    CASHFREE_ENV = (os.environ.get('CASHFREE_ENV', '').strip() or os.environ.get('CASHFREE_ENVIRONMENT', '').strip() or 'sandbox').lower()
    CASHFREE_ENVIRONMENT = CASHFREE_ENV
    CASHFREE_API_VERSION = os.environ.get('CASHFREE_API_VERSION', '2023-08-01').strip()
    CASHFREE_RETURN_URL = os.environ.get('CASHFREE_RETURN_URL', '').strip()
    CASHFREE_WEBHOOK_URL = os.environ.get('CASHFREE_WEBHOOK_URL', '').strip()

    # Brevo (Sendinblue) Email Service Settings
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()
    BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', os.environ.get('SENDER_EMAIL', 'info@antimatrix.co.in')).strip()
    BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'Anti Matrix').strip()

    # SMTP Relay Settings (Brevo SMTP or custom relay)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '').strip()
    _smtp_port_raw = os.environ.get('SMTP_PORT', '587').strip()
    SMTP_PORT = int(_smtp_port_raw) if _smtp_port_raw.isdigit() else 587
    SMTP_USER = os.environ.get('SMTP_USER', '').strip()
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '').strip()
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'info@antimatrix.co.in').strip()

    # Payment Test Mode Switch (Defaults to false so real Cashfree Sandbox is used)
    PAYMENT_TEST_MODE = os.environ.get('PAYMENT_TEST_MODE', 'false').lower() in ('true', '1', 'yes')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    PAYMENT_TEST_MODE = os.environ.get('PAYMENT_TEST_MODE', 'false').lower() in ('true', '1', 'yes')


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    PAYMENT_TEST_MODE = os.environ.get('PAYMENT_TEST_MODE', 'false').lower() in ('true', '1', 'yes')
    
    # In production, pool sizing is added for PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DEBUG = True
    PAYMENT_TEST_MODE = os.environ.get('PAYMENT_TEST_MODE', 'false').lower() in ('true', '1', 'yes')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig if os.environ.get('FLASK_ENV') != 'production' else ProductionConfig
}



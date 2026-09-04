from datetime import datetime, timezone
import string
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    application_id = db.Column(
        db.Integer,
        db.ForeignKey('job_applications.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash = db.Column(db.String(256), nullable=False)
    account_status = db.Column(db.String(30), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship to JobApplication (1-to-1)
    application = db.relationship(
        'JobApplication',
        backref=db.backref('employee', uselist=False, cascade='all, delete-orphan')
    )

    def set_password(self, password: str):
        """Hashes plaintext password with Werkzeug secure password hashing."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies candidate password against stored secure hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def job(self):
        return self.application.job if self.application else None

    @property
    def candidate_name(self):
        return self.application.full_name if self.application else ''

    @property
    def candidate_email(self):
        return self.application.email if self.application else ''

    @property
    def candidate_phone(self):
        return self.application.phone if self.application else ''

    @property
    def offer_letter_doc(self):
        """Returns the latest generated Offer Letter document for this employee if any."""
        for doc in self.documents:
            if doc.document_type == 'offer_letter':
                return doc
        return None

    @classmethod
    def generate_unique_employee_id(cls, max_attempts: int = 2000) -> str:
        """
        Generates a non-sequential, cryptographically random Employee ID in the format AM + 4 random digits (e.g. AM4827).
        Enforces uniqueness by checking the database and retrying on collision.
        """
        for _ in range(max_attempts):
            # Generate 4 random digits from 0000 to 9999
            random_digits = f"{secrets.randbelow(10000):04d}"
            emp_id = f"AM{random_digits}"
            if not cls.query.filter_by(employee_id=emp_id).first():
                return emp_id

        raise ValueError("Unable to generate a new Employee ID. Please contact the administrator.")

    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """
        Generates a cryptographically strong random password containing uppercase, lowercase,
        digits, and symbols. Prefixed with 'AM' to align with Anti-Matrix credential standards.
        Example output format: AMx7K9@pQ4#
        """
        if length < 8:
            length = 8

        # Guarantee at least 1 uppercase, 1 lowercase, 1 digit, 1 special character
        upper = string.ascii_uppercase
        lower = string.ascii_lowercase
        digits = string.digits
        symbols = "@#$%&*!"

        prefix = "AM"
        remaining_len = length - len(prefix)

        # Ensure mandatory character types
        mandatory = [
            secrets.choice(lower),
            secrets.choice(digits),
            secrets.choice(upper),
            secrets.choice(symbols)
        ]

        all_chars = upper + lower + digits + symbols
        fillers = [secrets.choice(all_chars) for _ in range(remaining_len - len(mandatory))]

        tail = mandatory + fillers
        # Cryptographic shuffle
        shuffled = []
        while tail:
            idx = secrets.randbelow(len(tail))
            shuffled.append(tail.pop(idx))

        return prefix + "".join(shuffled)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'application_id': self.application_id,
            'application_code': self.application.formatted_code if self.application else None,
            'candidate_name': self.candidate_name,
            'candidate_email': self.candidate_email,
            'job_title': self.job.title if self.job else None,
            'duration': self.application.duration_display if self.application else None,
            'account_status': self.account_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Employee id={self.id} employee_id='{self.employee_id}' app_id={self.application_id} status='{self.account_status}'>"

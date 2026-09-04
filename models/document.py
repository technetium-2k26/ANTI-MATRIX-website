from datetime import datetime, timezone
from . import db


class DocumentTemplate(db.Model):
    __tablename__ = 'document_templates'

    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 'offer_letter', 'experience_letter', 'certificate'
    name = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<DocumentTemplate id={self.id} type='{self.template_type}' filename='{self.filename}'>"


class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'

    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 'application_successful', 'offer_letter'
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<EmailTemplate id={self.id} type='{self.template_type}' subject='{self.subject[:30]}'>"


class EmployeeDocument(db.Model):
    __tablename__ = 'employee_documents'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    document_type = db.Column(db.String(50), default='offer_letter', nullable=False)  # 'offer_letter', 'experience_letter', 'certificate'
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    
    # Status progression: NOT_GENERATED -> GENERATED -> VERIFIED -> SENT
    status = db.Column(db.String(30), default='GENERATED', nullable=False)
    
    # Email tracking: not_sent, sent, failed
    email_status = db.Column(db.String(30), default='not_sent', nullable=False)
    email_error = db.Column(db.Text, nullable=True)
    
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship to Employee (Many Documents to One Employee)
    employee = db.relationship(
        'Employee',
        backref=db.backref('documents', cascade='all, delete-orphan', lazy=True)
    )

    def __repr__(self):
        return f"<EmployeeDocument id={self.id} emp_id={self.employee_id} type='{self.document_type}' status='{self.status}' email='{self.email_status}'>"

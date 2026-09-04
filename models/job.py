from datetime import datetime, timezone
from . import db


class JobPosting(db.Model):
    __tablename__ = 'job_postings'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    employment_type = db.Column(db.String(50), nullable=False, default='Full-time')
    short_description = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    qualifications = db.Column(db.Text, nullable=True)
    experience = db.Column(db.String(100), nullable=True)
    responsibilities = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    salary = db.Column(db.String(100), nullable=True)
    application_deadline = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def get_requirements_list(self):
        if not self.requirements:
            return []
        lines = [line.strip().lstrip('•-*').strip() for line in self.requirements.splitlines() if line.strip()]
        return lines if lines else [self.requirements.strip()]

    def get_responsibilities_list(self):
        if not self.responsibilities:
            return []
        lines = [line.strip().lstrip('•-*').strip() for line in self.responsibilities.splitlines() if line.strip()]
        return lines if lines else [self.responsibilities.strip()]

    @property
    def application_count(self):
        return len(self.applications)

    @property
    def new_application_count(self):
        return sum(1 for app in self.applications if app.status == 'New')

    def __repr__(self):
        return f"<JobPosting id={self.id} title='{self.title}' dept='{self.department}' active={self.is_active}>"


class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=False)
    college = db.Column(db.String(150), nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    graduation_year = db.Column(db.String(20), nullable=False)
    experience = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.Text, nullable=False)
    portfolio_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    cover_letter = db.Column(db.Text, nullable=False)
    why_join = db.Column(db.Text, nullable=True)
    resume_filename = db.Column(db.String(255), nullable=False)
    resume_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default='New', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def application_code(self):
        return f"#AM-{self.id:06d}"

    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def __repr__(self):
        return f"<JobApplication id={self.id} code='{self.application_code}' name='{self.full_name}' status='{self.status}'>"

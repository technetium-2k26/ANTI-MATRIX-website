from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .contact import ContactInquiry
from .job import JobPosting, JobApplication

__all__ = ['db', 'User', 'ContactInquiry', 'JobPosting', 'JobApplication']

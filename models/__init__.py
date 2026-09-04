from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .contact import ContactInquiry

__all__ = ['db', 'User', 'ContactInquiry']

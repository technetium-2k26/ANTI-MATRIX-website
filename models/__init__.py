from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .contact import ContactInquiry
from .job import JobPosting, JobApplication, Payment
from .employee import Employee
from .document import DocumentTemplate, EmailTemplate, EmployeeDocument, EmailLog
from .money_transaction import MoneyTransaction

__all__ = [
    'db', 'User', 'ContactInquiry', 'JobPosting', 'JobApplication',
    'Payment', 'Employee', 'DocumentTemplate', 'EmailTemplate', 'EmployeeDocument', 'EmailLog',
    'MoneyTransaction'
]



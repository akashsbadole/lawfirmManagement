from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for many-to-many relationship between users and cases
case_assignments = db.Table('case_assignments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('case_id', db.Integer, db.ForeignKey('case.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20))  # 'admin' (full access to system; manage users, roles, permissions, clients, cases, billing, payments; approve/reject invoices/time entries; access analytics, financial reports, firm-wide dashboards; configure system settings (billing rates, document categories, practice areas); assign lawyers/staff to cases), 'lawyer' (manage own cases & clients; add/edit case details, appointments, documents, time entries; track billable hours; generate invoices (pending admin approval); search legal database, access case law, add citations to cases; communicate with clients via notes/messages; cannot create/remove other users), 'staff' (support role, limited permissions; schedule appointments; upload and manage documents (evidence, contracts); draft invoices (cannot approve/send); record time entries on behalf of lawyers (if permitted); cannot delete cases or clients; cannot assign users)
    hourly_rate = db.Column(db.Float)
    cases = db.relationship('Case', secondary=case_assignments, backref=db.backref('assigned_users', lazy='dynamic'))
    time_entries = db.relationship('TimeEntry', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(256))
    company = db.Column(db.String(128))
    category = db.Column(db.String(64))
    notes = db.Column(db.Text)
    cases = db.relationship('Case', backref='client', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='client', lazy='dynamic')
    documents = db.relationship('Document', backref='client', lazy='dynamic')

    def __repr__(self):
        return f'<Client {self.first_name} {self.last_name}>'

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    status = db.Column(db.String(20))  # Open, In Progress, On Hold, Closed, Archived
    priority = db.Column(db.String(20))  # Low, Medium, High, Urgent
    practice_area = db.Column(db.String(64))
    case_type = db.Column(db.String(64))
    budget = db.Column(db.Float)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    appointments = db.relationship('Appointment', backref='case', lazy='dynamic')
    documents = db.relationship('Document', backref='case', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='case', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='case', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Case {self.case_number}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    location = db.Column(db.String(256))
    type = db.Column(db.String(64))  # Consultation, Meeting, Court Appearance, etc.
    status = db.Column(db.String(20))  # Scheduled, Completed, Canceled
    notes = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.title}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256))
    original_filename = db.Column(db.String(256))
    category = db.Column(db.String(64))  # Contracts, Evidence, Court Filings, etc.
    description = db.Column(db.Text)
    confidential = db.Column(db.Boolean, default=False)
    version = db.Column(db.Integer, default=1)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Document {self.filename}>'

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    hours = db.Column(db.Float)
    description = db.Column(db.Text)
    billable = db.Column(db.Boolean, default=True)
    rate = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    status = db.Column(db.String(20))  # Draft, Submitted, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TimeEntry {self.id}>'

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True)
    issue_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20))  # Draft, Sent, Paid, Overdue
    notes = db.Column(db.Text)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    client = db.relationship('Client', backref=db.backref('invoices', lazy=True))
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='invoice', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=datetime.utcnow)


    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    payment_date = db.Column(db.Date)
    method = db.Column(db.String(64))  # Credit Card, Check, Cash, Bank Transfer
    reference = db.Column(db.String(128))
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}>'

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(512))
    results = db.Column(db.JSON)   # store search results (title, link, snippet, citation)
    search_engine = db.Column(db.String(50))  # Google, Bing, DuckDuckGo
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchHistory {self.query}>'
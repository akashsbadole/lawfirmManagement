from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import re
import uuid

# Tenant model for multi-tenancy
class Tenant(db.Model):
    """Multi-tenant support - each law firm is a tenant"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    subdomain = db.Column(db.String(64), unique=True, nullable=False)
    domain = db.Column(db.String(128))  # Custom domain if any
    database_name = db.Column(db.String(64))  # For database per tenant approach
    is_active = db.Column(db.Boolean, default=True)
    
    # Subscription details
    plan_type = db.Column(db.String(32), default='basic')  # basic, premium, enterprise
    max_users = db.Column(db.Integer, default=5)
    max_cases = db.Column(db.Integer, default=100)
    max_storage_gb = db.Column(db.Integer, default=1)
    
    # Contact information
    contact_name = db.Column(db.String(128))
    contact_email = db.Column(db.String(128))
    contact_phone = db.Column(db.String(32))
    address = db.Column(db.Text)
    
    # Billing information
    billing_email = db.Column(db.String(128))
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    last_payment = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    
    @staticmethod
    def get_by_subdomain(subdomain):
        """Get tenant by subdomain"""
        return Tenant.query.filter_by(subdomain=subdomain, is_active=True).first()
    
    @staticmethod
    def get_by_domain(domain):
        """Get tenant by custom domain"""
        return Tenant.query.filter_by(domain=domain, is_active=True).first()
    
    def get_current_usage(self):
        """Get current usage statistics"""
        return {
            'users': self.users.filter_by(is_active=True).count(),
            'cases': Case.query.filter_by(tenant_id=self.id).count(),
            'storage_mb': self.get_storage_usage()
        }
    
    def get_storage_usage(self):
        """Calculate storage usage in MB"""
        # This would calculate actual file storage usage
        # For now, return a placeholder
        return 0
    
    def is_within_limits(self):
        """Check if tenant is within subscription limits"""
        usage = self.get_current_usage()
        return (
            usage['users'] <= self.max_users and
            usage['cases'] <= self.max_cases and
            usage['storage_mb'] <= (self.max_storage_gb * 1024)
        )
    
    def __repr__(self):
        return f'<Tenant {self.name}>'

# Role definitions with proper permissions
class UserRole(Enum):
    ADMIN = 'admin'
    LAWYER = 'lawyer' 
    STAFF = 'staff'

class Permission(Enum):
    # User management
    MANAGE_USERS = 'manage_users'
    VIEW_ALL_USERS = 'view_all_users'
    
    # Client management
    CREATE_CLIENTS = 'create_clients'
    EDIT_CLIENTS = 'edit_clients'
    DELETE_CLIENTS = 'delete_clients'
    VIEW_CLIENTS = 'view_clients'
    
    # Case management
    CREATE_CASES = 'create_cases'
    EDIT_CASES = 'edit_cases'
    DELETE_CASES = 'delete_cases'
    VIEW_CASES = 'view_cases'
    ASSIGN_CASES = 'assign_cases'
    
    # Document management
    UPLOAD_DOCUMENTS = 'upload_documents'
    EDIT_DOCUMENTS = 'edit_documents'
    DELETE_DOCUMENTS = 'delete_documents'
    VIEW_DOCUMENTS = 'view_documents'
    VIEW_CONFIDENTIAL = 'view_confidential'
    
    # Time tracking
    CREATE_TIME_ENTRIES = 'create_time_entries'
    EDIT_TIME_ENTRIES = 'edit_time_entries'
    DELETE_TIME_ENTRIES = 'delete_time_entries'
    VIEW_TIME_ENTRIES = 'view_time_entries'
    APPROVE_TIME_ENTRIES = 'approve_time_entries'
    
    # Billing
    CREATE_INVOICES = 'create_invoices'
    EDIT_INVOICES = 'edit_invoices'
    DELETE_INVOICES = 'delete_invoices'
    APPROVE_INVOICES = 'approve_invoices'
    VIEW_BILLING = 'view_billing'
    PROCESS_PAYMENTS = 'process_payments'
    
    # Appointments
    CREATE_APPOINTMENTS = 'create_appointments'
    EDIT_APPOINTMENTS = 'edit_appointments'
    DELETE_APPOINTMENTS = 'delete_appointments'
    VIEW_APPOINTMENTS = 'view_appointments'
    
    # Search and legal tools
    SEARCH_INTERNAL = 'search_internal'
    SEARCH_EXTERNAL = 'search_external'
    ACCESS_LEGAL_TOOLS = 'access_legal_tools'
    
    # System configuration
    CONFIGURE_SYSTEM = 'configure_system'
    VIEW_ANALYTICS = 'view_analytics'
    VIEW_REPORTS = 'view_reports'

# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Full system access
        Permission.MANAGE_USERS, Permission.VIEW_ALL_USERS,
        Permission.CREATE_CLIENTS, Permission.EDIT_CLIENTS, Permission.DELETE_CLIENTS, Permission.VIEW_CLIENTS,
        Permission.CREATE_CASES, Permission.EDIT_CASES, Permission.DELETE_CASES, Permission.VIEW_CASES, Permission.ASSIGN_CASES,
        Permission.UPLOAD_DOCUMENTS, Permission.EDIT_DOCUMENTS, Permission.DELETE_DOCUMENTS, Permission.VIEW_DOCUMENTS, Permission.VIEW_CONFIDENTIAL,
        Permission.CREATE_TIME_ENTRIES, Permission.EDIT_TIME_ENTRIES, Permission.DELETE_TIME_ENTRIES, Permission.VIEW_TIME_ENTRIES, Permission.APPROVE_TIME_ENTRIES,
        Permission.CREATE_INVOICES, Permission.EDIT_INVOICES, Permission.DELETE_INVOICES, Permission.APPROVE_INVOICES, Permission.VIEW_BILLING, Permission.PROCESS_PAYMENTS,
        Permission.CREATE_APPOINTMENTS, Permission.EDIT_APPOINTMENTS, Permission.DELETE_APPOINTMENTS, Permission.VIEW_APPOINTMENTS,
        Permission.SEARCH_INTERNAL, Permission.SEARCH_EXTERNAL, Permission.ACCESS_LEGAL_TOOLS,
        Permission.CONFIGURE_SYSTEM, Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS
    ],
    UserRole.LAWYER: [
        # Lawyer permissions - manage own cases and clients
        Permission.VIEW_ALL_USERS,  # Can see other users for assignments
        Permission.CREATE_CLIENTS, Permission.EDIT_CLIENTS, Permission.VIEW_CLIENTS,
        Permission.CREATE_CASES, Permission.EDIT_CASES, Permission.VIEW_CASES,
        Permission.UPLOAD_DOCUMENTS, Permission.EDIT_DOCUMENTS, Permission.VIEW_DOCUMENTS, Permission.VIEW_CONFIDENTIAL,
        Permission.CREATE_TIME_ENTRIES, Permission.EDIT_TIME_ENTRIES, Permission.VIEW_TIME_ENTRIES,
        Permission.CREATE_INVOICES, Permission.EDIT_INVOICES, Permission.VIEW_BILLING,
        Permission.CREATE_APPOINTMENTS, Permission.EDIT_APPOINTMENTS, Permission.VIEW_APPOINTMENTS,
        Permission.SEARCH_INTERNAL, Permission.SEARCH_EXTERNAL, Permission.ACCESS_LEGAL_TOOLS
    ],
    UserRole.STAFF: [
        # Staff permissions - support role with limited access
        Permission.VIEW_CLIENTS,
        Permission.VIEW_CASES,
        Permission.UPLOAD_DOCUMENTS, Permission.EDIT_DOCUMENTS, Permission.VIEW_DOCUMENTS,
        Permission.CREATE_TIME_ENTRIES, Permission.VIEW_TIME_ENTRIES,
        Permission.CREATE_INVOICES, Permission.VIEW_BILLING,  # Can draft but not approve
        Permission.CREATE_APPOINTMENTS, Permission.EDIT_APPOINTMENTS, Permission.VIEW_APPOINTMENTS,
        Permission.SEARCH_INTERNAL, Permission.ACCESS_LEGAL_TOOLS
    ]
}

# Association table for many-to-many relationship between users and cases
case_assignments = db.Table('case_assignments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('case_id', db.Integer, db.ForeignKey('case.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    username = db.Column(db.String(64), index=True, nullable=False)
    email = db.Column(db.String(120), index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')
    hourly_rate = db.Column(db.Float, default=0.0)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add unique constraint for username within tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'username', name='unique_tenant_username'),
        db.UniqueConstraint('tenant_id', 'email', name='unique_tenant_email'),
    )
    
    # Relationships
    cases = db.relationship('Case', secondary=case_assignments, backref=db.backref('assigned_users', lazy='dynamic'))
    time_entries = db.relationship('TimeEntry', backref='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Set password with validation"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        try:
            user_role = UserRole(self.role)
            return permission in ROLE_PERMISSIONS.get(user_role, [])
        except ValueError:
            return False
    
    def get_role_display(self):
        """Get human-readable role name"""
        role_names = {
            'admin': 'Administrator',
            'lawyer': 'Lawyer',
            'staff': 'Staff'
        }
        return role_names.get(self.role, self.role.title())
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def validate_email(self):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, self.email) is not None
    
    def can_access_case(self, case):
        """Check if user can access specific case"""
        if self.role == 'admin':
            return True
        return case in self.cases
    
    def can_access_client(self, client):
        """Check if user can access specific client"""
        if self.role == 'admin':
            return True
        # Check if user has any cases for this client
        return any(case.client_id == client.id for case in self.cases)

    def __repr__(self):
        return f'<User {self.username}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    company = db.Column(db.String(128))
    category = db.Column(db.String(64))  # Individual, Corporate, Government, etc.
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    cases = db.relationship('Case', backref='client', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='client', lazy='dynamic')
    documents = db.relationship('Document', backref='client', lazy='dynamic')
    
    def get_full_name(self):
        """Get client's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def validate_email(self):
        """Validate email format if provided"""
        if not self.email:
            return True  # Email is optional
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, self.email) is not None
    
    def validate_phone(self):
        """Validate phone format if provided"""
        if not self.phone:
            return True  # Phone is optional
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', self.phone)
        return len(digits_only) >= 10  # At least 10 digits
    
    def get_active_cases_count(self):
        """Get count of active cases for this client"""
        return self.cases.filter(Case.status.in_(['Open', 'In Progress'])).count()
    
    def get_total_billed(self):
        """Get total amount billed to this client"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Invoice.amount)).filter(
            Invoice.client_id == self.id,
            Invoice.status != 'Draft'
        ).scalar()
        return result or 0.0

    def __repr__(self):
        return f'<Client {self.first_name} {self.last_name}>'

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    case_number = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='Open')  # Open, In Progress, On Hold, Closed, Archived
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Urgent
    practice_area = db.Column(db.String(64))  # Family Law, Criminal Law, Corporate Law, etc.
    case_type = db.Column(db.String(64))  # Litigation, Consultation, Contract Review, etc.
    budget = db.Column(db.Float, default=0.0)
    estimated_hours = db.Column(db.Float)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    lead_attorney_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # Case number should be unique within tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'case_number', name='unique_tenant_case_number'),
    )
    
    # Relationships
    appointments = db.relationship('Appointment', backref='case', lazy='dynamic')
    documents = db.relationship('Document', backref='case', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='case', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='case', lazy='dynamic')
    lead_attorney = db.relationship('User', foreign_keys=[lead_attorney_id])
    
    @staticmethod
    def generate_case_number():
        """Generate unique case number"""
        from datetime import datetime
        year = datetime.now().year
        # Get the last case number for this year
        last_case = Case.query.filter(
            Case.case_number.like(f'{year}-%')
        ).order_by(Case.case_number.desc()).first()
        
        if last_case:
            last_num = int(last_case.case_number.split('-')[1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{year}-{new_num:04d}"
    
    def get_total_hours(self):
        """Get total hours logged for this case"""
        from sqlalchemy import func
        result = db.session.query(func.sum(TimeEntry.hours)).filter(
            TimeEntry.case_id == self.id
        ).scalar()
        return result or 0.0
    
    def get_billable_hours(self):
        """Get total billable hours for this case"""
        from sqlalchemy import func
        result = db.session.query(func.sum(TimeEntry.hours)).filter(
            TimeEntry.case_id == self.id,
            TimeEntry.billable == True
        ).scalar()
        return result or 0.0
    
    def get_total_billed(self):
        """Get total amount billed for this case"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Invoice.amount)).filter(
            Invoice.case_id == self.id,
            Invoice.status != 'Draft'
        ).scalar()
        return result or 0.0
    
    def get_status_color(self):
        """Get color class for case status"""
        colors = {
            'Open': 'success',
            'In Progress': 'primary',
            'On Hold': 'warning',
            'Closed': 'secondary',
            'Archived': 'dark'
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Get color class for case priority"""
        colors = {
            'Low': 'success',
            'Medium': 'info',
            'High': 'warning',
            'Urgent': 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    def is_overbudget(self):
        """Check if case is over budget"""
        if not self.budget or self.budget <= 0:
            return False
        return self.get_total_billed() > self.budget

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
    search_type = db.Column(db.String(50), nullable=False, default='internal') # 'internal' or 'external'
    jurisdiction = db.Column(db.String(100))
    case_type = db.Column(db.String(100))
    date_from = db.Column(db.Date)
    date_to = db.Column(db.Date)
    search_engine = db.Column(db.String(50))  # e.g., 'google', 'bing' for external searches
    results = db.Column(db.JSON)   # stores results from either internal docs or external APIs
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchHistory {self.query} ({self.search_type})>'

class CaseLaw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), nullable=False)
    citation = db.Column(db.String(256), unique=True, nullable=False)
    year = db.Column(db.Integer)
    court = db.Column(db.String(128))
    jurisdiction = db.Column(db.String(128)) # e.g., "Federal", "State Supreme Court", "Appellate Court"
    summary = db.Column(db.Text)
    full_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CaseLaw {self.citation}>'

class AuditLog(db.Model):
    """Track user actions for security and compliance"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(128), nullable=False)  # e.g., 'CREATE_CLIENT', 'DELETE_CASE'
    resource_type = db.Column(db.String(64), nullable=False)  # e.g., 'Client', 'Case', 'Document'
    resource_id = db.Column(db.Integer)  # ID of the affected resource
    details = db.Column(db.JSON)  # Additional details about the action
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(512))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class SystemSettings(db.Model):
    """Store system-wide configuration settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    category = db.Column(db.String(64))  # e.g., 'billing', 'security', 'general'
    data_type = db.Column(db.String(32), default='string')  # 'string', 'integer', 'float', 'boolean', 'json'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_typed_value(self):
        """Return value converted to appropriate type"""
        if self.data_type == 'integer':
            return int(self.value) if self.value else 0
        elif self.data_type == 'float':
            return float(self.value) if self.value else 0.0
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes') if self.value else False
        elif self.data_type == 'json':
            import json
            return json.loads(self.value) if self.value else {}
        return self.value or ''
    
    def __repr__(self):
        return f'<SystemSettings {self.key}>'

class Task(db.Model):
    """Task management for team collaboration"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(32), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_tasks')
    case = db.relationship('Case', backref='tasks')
    client = db.relationship('Client', backref='tasks')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.title}>'

class Reminder(db.Model):
    """Reminders and notifications system"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    message = db.Column(db.Text)
    reminder_type = db.Column(db.String(64))  # deadline, appointment, payment, custom
    reminder_date = db.Column(db.DateTime, nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'))
    
    user = db.relationship('User', backref='reminders')
    case = db.relationship('Case', backref='reminders')
    appointment = db.relationship('Appointment', backref='reminders')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Reminder {self.title}>'

class SupportTicket(db.Model):
    """Support system for users"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    subject = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(32), default='medium')  # low, medium, high, urgent
    category = db.Column(db.String(64))  # technical, billing, feature_request, bug_report
    
    # Relationships
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='support_tickets')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tickets')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    @staticmethod
    def generate_ticket_number():
        """Generate unique ticket number"""
        import random
        import string
        while True:
            number = 'TKT-' + ''.join(random.choices(string.digits, k=6))
            if not SupportTicket.query.filter_by(ticket_number=number).first():
                return number
    
    def __repr__(self):
        return f'<SupportTicket {self.ticket_number}>'

class SupportMessage(db.Model):
    """Messages/replies in support tickets"""
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal notes vs customer-visible
    
    # Relationships
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    ticket = db.relationship('SupportTicket', backref='messages')
    user = db.relationship('User', backref='support_messages')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SupportMessage {self.id}>'

class EmailTemplate(db.Model):
    """Email templates for automation"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    subject = db.Column(db.String(256), nullable=False)
    body = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.String(64))  # appointment_reminder, invoice_due, welcome, etc.
    is_active = db.Column(db.Boolean, default=True)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', backref='email_templates')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class EmailLog(db.Model):
    """Log of sent emails"""
    id = db.Column(db.Integer, primary_key=True)
    to_email = db.Column(db.String(256), nullable=False)
    subject = db.Column(db.String(256), nullable=False)
    body = db.Column(db.Text)
    status = db.Column(db.String(32), default='pending')  # pending, sent, failed
    error_message = db.Column(db.Text)
    
    # Relationships
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    
    template = db.relationship('EmailTemplate')
    user = db.relationship('User')
    client = db.relationship('Client')
    
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailLog {self.to_email}>'

class ClientPortalAccess(db.Model):
    """Client portal access management"""
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(128), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime)
    
    # Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref='portal_access')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_access_token():
        """Generate secure access token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        """Check if access token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<ClientPortalAccess {self.client.get_full_name()}>'

class TrustAccount(db.Model):
    """Trust account management for client funds"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(128), nullable=False)
    account_number = db.Column(db.String(64), unique=True)
    bank_name = db.Column(db.String(128))
    current_balance = db.Column(db.Float, default=0.0)
    
    # Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref='trust_accounts')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrustAccount {self.account_name}>'

class TrustTransaction(db.Model):
    """Trust account transactions"""
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(32), nullable=False)  # deposit, withdrawal, transfer
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(256))
    reference_number = db.Column(db.String(64))
    
    # Relationships
    trust_account_id = db.Column(db.Integer, db.ForeignKey('trust_account.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    trust_account = db.relationship('TrustAccount', backref='transactions')
    created_by = db.relationship('User')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrustTransaction {self.transaction_type}: {self.amount}>'

class Backup(db.Model):
    """Database backup tracking"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512))
    file_size = db.Column(db.Integer)  # Size in bytes
    backup_type = db.Column(db.String(32), default='manual')  # manual, automatic
    status = db.Column(db.String(32), default='completed')  # in_progress, completed, failed
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Backup {self.filename}>'
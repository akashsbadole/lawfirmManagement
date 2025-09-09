"""
Multi-tenant utilities for the legal management system
"""
from flask import request, g, session, redirect, url_for, abort
from app.models import Tenant
from functools import wraps
import re

def get_tenant_from_request():
    """
    Extract tenant from request (subdomain or custom domain)
    """
    host = request.host.lower()
    
    # Check for custom domain first
    tenant = Tenant.get_by_domain(host)
    if tenant:
        return tenant
    
    # Check for subdomain pattern (subdomain.yourdomain.com)
    subdomain_match = re.match(r'^([a-zA-Z0-9-]+)\.', host)
    if subdomain_match:
        subdomain = subdomain_match.group(1)
        
        # Skip common subdomains
        if subdomain not in ['www', 'api', 'admin', 'mail', 'ftp']:
            tenant = Tenant.get_by_subdomain(subdomain)
            if tenant:
                return tenant
    
    # Default tenant for main domain or localhost
    if host in ['localhost', '127.0.0.1'] or host.startswith('localhost:') or host.startswith('127.0.0.1:'):
        # For development, use a default tenant or create one
        tenant = Tenant.query.filter_by(subdomain='default').first()
        if not tenant:
            # Create default tenant for development
            tenant = Tenant(
                name='Default Law Firm',
                subdomain='default',
                contact_name='Admin',
                contact_email='admin@lawfirm.com',
                plan_type='enterprise',
                max_users=100,
                max_cases=1000,
                max_storage_gb=10
            )
            from app import db
            db.session.add(tenant)
            db.session.commit()
        return tenant
    
    return None

def tenant_required(f):
    """
    Decorator to ensure a valid tenant is identified
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = get_tenant_from_request()
        if not tenant:
            # Redirect to tenant selection or show error
            return redirect(url_for('select_tenant'))
        
        g.current_tenant = tenant
        return f(*args, **kwargs)
    return decorated_function

def check_tenant_limits(action_type):
    """
    Check if tenant is within subscription limits for specific actions
    """
    if not hasattr(g, 'current_tenant'):
        return False
    
    tenant = g.current_tenant
    usage = tenant.get_current_usage()
    
    if action_type == 'create_user':
        return usage['users'] < tenant.max_users
    elif action_type == 'create_case':
        return usage['cases'] < tenant.max_cases
    elif action_type == 'upload_file':
        # Check storage limit (simplified)
        return usage['storage_mb'] < (tenant.max_storage_gb * 1024)
    
    return True

def get_tenant_database_uri(tenant):
    """
    Get database URI for tenant (for database-per-tenant approach)
    """
    if tenant.database_name:
        # Use separate database for tenant
        return f"sqlite:///{tenant.database_name}.db"
    else:
        # Use shared database with tenant_id filtering
        return None

class TenantContext:
    """
    Context manager for tenant-specific operations
    """
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.old_tenant = None
    
    def __enter__(self):
        self.old_tenant = getattr(g, 'current_tenant', None)
        g.current_tenant = Tenant.query.get(self.tenant_id)
        return g.current_tenant
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        g.current_tenant = self.old_tenant

def filter_by_tenant(query, model_class):
    """
    Add tenant filter to query
    """
    if hasattr(g, 'current_tenant') and hasattr(model_class, 'tenant_id'):
        return query.filter(model_class.tenant_id == g.current_tenant.id)
    return query

def create_tenant_admin(tenant, admin_data):
    """
    Create admin user for new tenant
    """
    from app.models import User
    from app import db
    
    admin = User(
        tenant_id=tenant.id,
        username=admin_data.get('username', 'admin'),
        email=admin_data.get('email'),
        first_name=admin_data.get('first_name', 'Admin'),
        last_name=admin_data.get('last_name', 'User'),
        role='admin',
        is_active=True
    )
    admin.set_password(admin_data.get('password', 'admin123'))
    
    db.session.add(admin)
    db.session.commit()
    
    return admin

def setup_tenant_data(tenant):
    """
    Set up initial data for new tenant
    """
    from app.models import SystemSettings
    from app import db
    
    # Create default system settings for tenant
    default_settings = [
        {
            'key': f'tenant_{tenant.id}_firm_name',
            'value': tenant.name,
            'description': 'Name of the law firm',
            'category': 'general'
        },
        {
            'key': f'tenant_{tenant.id}_default_hourly_rate',
            'value': '250.00',
            'description': 'Default hourly rate for new lawyers',
            'category': 'billing'
        },
        {
            'key': f'tenant_{tenant.id}_invoice_due_days',
            'value': '30',
            'description': 'Default number of days for invoice due date',
            'category': 'billing'
        }
    ]
    
    for setting_data in default_settings:
        setting = SystemSettings(**setting_data)
        db.session.add(setting)
    
    db.session.commit()

def get_tenant_setting(key, default=None):
    """
    Get tenant-specific setting
    """
    if not hasattr(g, 'current_tenant'):
        return default
    
    from app.models import SystemSettings
    tenant_key = f'tenant_{g.current_tenant.id}_{key}'
    setting = SystemSettings.query.filter_by(key=tenant_key).first()
    
    if setting:
        return setting.get_typed_value()
    
    return default

def set_tenant_setting(key, value, description=None, category='general'):
    """
    Set tenant-specific setting
    """
    if not hasattr(g, 'current_tenant'):
        return False
    
    from app.models import SystemSettings
    from app import db
    
    tenant_key = f'tenant_{g.current_tenant.id}_{key}'
    setting = SystemSettings.query.filter_by(key=tenant_key).first()
    
    if setting:
        setting.value = str(value)
    else:
        setting = SystemSettings(
            key=tenant_key,
            value=str(value),
            description=description,
            category=category
        )
        db.session.add(setting)
    
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
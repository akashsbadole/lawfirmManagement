"""
Utility functions and decorators for the legal management system
"""
from functools import wraps
from flask import flash, redirect, url_for, request, abort
from flask_login import current_user
from app.models import Permission, AuditLog
from app import db
import re
from datetime import datetime

def permission_required(permission):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_anonymous:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            if not current_user.has_permission(permission):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(allowed_roles):
    """Decorator to check if user has one of the allowed roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_anonymous:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_user_action(action, resource_type, resource_id=None, details=None):
    """Log user action for audit trail"""
    if current_user.is_authenticated:
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:512]
        )
        db.session.add(audit_log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error logging user action: {e}")

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional in most cases
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) >= 10

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    return filename

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"

def format_hours(hours):
    """Format hours with proper decimal places"""
    if hours is None:
        return "0.00"
    return f"{hours:.2f}"

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
            'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'csv'
        }
    
    return '.' in filename and get_file_extension(filename) in allowed_extensions

def get_system_setting(key, default=None):
    """Get system setting value"""
    from app.models import SystemSettings
    setting = SystemSettings.query.filter_by(key=key).first()
    if setting:
        return setting.get_typed_value()
    return default

def set_system_setting(key, value, description=None, category='general', data_type='string'):
    """Set system setting value"""
    from app.models import SystemSettings
    setting = SystemSettings.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value)
        setting.updated_at = datetime.utcnow()
    else:
        setting = SystemSettings(
            key=key,
            value=str(value),
            description=description,
            category=category,
            data_type=data_type
        )
        db.session.add(setting)
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error setting system setting: {e}")
        return False

def paginate_query(query, page, per_page=20):
    """Paginate a SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def search_filter(query, search_term, *fields):
    """Add search filter to query across multiple fields"""
    if not search_term:
        return query
    
    search_conditions = []
    for field in fields:
        search_conditions.append(field.ilike(f'%{search_term}%'))
    
    if search_conditions:
        query = query.filter(db.or_(*search_conditions))
    
    return query

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_required_fields(data, required_fields):
    """Validate that required fields are present and not empty"""
    errors = []
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == '':
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    if errors:
        raise ValidationError("; ".join(errors))

def validate_numeric_field(value, field_name, min_value=None, max_value=None):
    """Validate numeric field"""
    if value is None or value == '':
        return None
    
    try:
        num_value = float(value)
        if min_value is not None and num_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        if max_value is not None and num_value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")
        return num_value
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number")

def validate_date_field(value, field_name):
    """Validate date field"""
    if not value:
        return None
    
    try:
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        return value
    except ValueError:
        raise ValidationError(f"{field_name} must be a valid date (YYYY-MM-DD)")

def validate_datetime_field(value, field_name):
    """Validate datetime field"""
    if not value:
        return None
    
    try:
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%dT%H:%M')
        return value
    except ValueError:
        raise ValidationError(f"{field_name} must be a valid datetime")
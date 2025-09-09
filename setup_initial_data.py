#!/usr/bin/env python3
"""
Setup script to initialize the legal management system with default data
"""
from app import app, db
from app.models import User, Client, Case, SystemSettings, UserRole, Task, SupportTicket, EmailTemplate
from datetime import datetime, date, timedelta
import os

def create_default_users():
    """Create default admin and sample users"""
    print("Creating default users...")
    
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@lawfirm.com',
            first_name='System',
            last_name='Administrator',
            role='admin',
            department='Administration',
            hourly_rate=0.0,
            is_active=True,
            created_at=datetime.utcnow()
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        print("✓ Created admin user (username: admin, password: admin123)")
    else:
        print("✓ Admin user already exists")
    
    # Create sample lawyer
    lawyer = User.query.filter_by(username='jdoe').first()
    if not lawyer:
        lawyer = User(
            username='jdoe',
            email='john.doe@lawfirm.com',
            first_name='John',
            last_name='Doe',
            role='lawyer',
            department='Family Law',
            hourly_rate=350.00,
            phone='(555) 123-4567',
            is_active=True,
            created_at=datetime.utcnow()
        )
        lawyer.set_password('lawyer123')
        db.session.add(lawyer)
        print("✓ Created sample lawyer (username: jdoe, password: lawyer123)")
    else:
        print("✓ Sample lawyer already exists")
    
    # Create sample staff
    staff = User.query.filter_by(username='msmith').first()
    if not staff:
        staff = User(
            username='msmith',
            email='mary.smith@lawfirm.com',
            first_name='Mary',
            last_name='Smith',
            role='staff',
            department='Administration',
            hourly_rate=75.00,
            phone='(555) 123-4568',
            is_active=True,
            created_at=datetime.utcnow()
        )
        staff.set_password('staff123')
        db.session.add(staff)
        print("✓ Created sample staff (username: msmith, password: staff123)")
    else:
        print("✓ Sample staff already exists")

def create_system_settings():
    """Create default system settings"""
    print("Creating system settings...")
    
    default_settings = [
        {
            'key': 'firm_name',
            'value': 'Legal Management System',
            'description': 'Name of the law firm',
            'category': 'general',
            'data_type': 'string'
        },
        {
            'key': 'default_hourly_rate',
            'value': '250.00',
            'description': 'Default hourly rate for new lawyers',
            'category': 'billing',
            'data_type': 'float'
        },
        {
            'key': 'invoice_due_days',
            'value': '30',
            'description': 'Default number of days for invoice due date',
            'category': 'billing',
            'data_type': 'integer'
        },
        {
            'key': 'max_file_size_mb',
            'value': '16',
            'description': 'Maximum file upload size in MB',
            'category': 'system',
            'data_type': 'integer'
        },
        {
            'key': 'enable_audit_logging',
            'value': 'true',
            'description': 'Enable audit logging for user actions',
            'category': 'security',
            'data_type': 'boolean'
        },
        {
            'key': 'session_timeout_minutes',
            'value': '480',
            'description': 'User session timeout in minutes (8 hours)',
            'category': 'security',
            'data_type': 'integer'
        },
        {
            'key': 'backup_retention_days',
            'value': '90',
            'description': 'Number of days to retain database backups',
            'category': 'system',
            'data_type': 'integer'
        }
    ]
    
    for setting_data in default_settings:
        existing = SystemSettings.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = SystemSettings(**setting_data, created_at=datetime.utcnow())
            db.session.add(setting)
            print(f"✓ Created setting: {setting_data['key']}")
        else:
            print(f"✓ Setting already exists: {setting_data['key']}")

def create_sample_clients():
    """Create sample clients for demonstration"""
    print("Creating sample clients...")
    
    sample_clients = [
        {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.johnson@email.com',
            'phone': '(555) 234-5678',
            'address': '123 Main St, Anytown, ST 12345',
            'company': 'Johnson Enterprises',
            'category': 'Corporate',
            'notes': 'Corporate client for business law matters'
        },
        {
            'first_name': 'Robert',
            'last_name': 'Williams',
            'email': 'robert.williams@email.com',
            'phone': '(555) 345-6789',
            'address': '456 Oak Ave, Somewhere, ST 67890',
            'company': '',
            'category': 'Individual',
            'notes': 'Family law client - divorce proceedings'
        },
        {
            'first_name': 'Sarah',
            'last_name': 'Davis',
            'email': 'sarah.davis@email.com',
            'phone': '(555) 456-7890',
            'address': '789 Pine Rd, Elsewhere, ST 13579',
            'company': 'Davis & Associates',
            'category': 'Corporate',
            'notes': 'Contract review and business formation'
        }
    ]
    
    admin_user = User.query.filter_by(role='admin').first()
    
    for client_data in sample_clients:
        existing = Client.query.filter_by(
            first_name=client_data['first_name'],
            last_name=client_data['last_name']
        ).first()
        
        if not existing:
            client = Client(
                **client_data,
                is_active=True,
                created_at=datetime.utcnow(),
                created_by=admin_user.id if admin_user else None
            )
            db.session.add(client)
            print(f"✓ Created client: {client_data['first_name']} {client_data['last_name']}")
        else:
            print(f"✓ Client already exists: {client_data['first_name']} {client_data['last_name']}")

def create_sample_cases():
    """Create sample cases"""
    print("Creating sample cases...")
    
    # Get clients and lawyer
    alice = Client.query.filter_by(first_name='Alice', last_name='Johnson').first()
    robert = Client.query.filter_by(first_name='Robert', last_name='Williams').first()
    lawyer = User.query.filter_by(role='lawyer').first()
    
    if not alice or not robert or not lawyer:
        print("⚠ Skipping sample cases - required clients or lawyer not found")
        return
    
    sample_cases = [
        {
            'case_number': Case.generate_case_number(),
            'title': 'Business Formation and Contract Review',
            'description': 'Assistance with LLC formation and review of vendor contracts',
            'status': 'In Progress',
            'priority': 'Medium',
            'practice_area': 'Corporate Law',
            'case_type': 'Business Formation',
            'budget': 15000.00,
            'estimated_hours': 40.0,
            'client_id': alice.id,
            'lead_attorney_id': lawyer.id
        },
        {
            'case_number': Case.generate_case_number(),
            'title': 'Divorce and Child Custody',
            'description': 'Divorce proceedings with child custody arrangements',
            'status': 'Open',
            'priority': 'High',
            'practice_area': 'Family Law',
            'case_type': 'Divorce',
            'budget': 8000.00,
            'estimated_hours': 25.0,
            'client_id': robert.id,
            'lead_attorney_id': lawyer.id
        }
    ]
    
    for case_data in sample_cases:
        existing = Case.query.filter_by(case_number=case_data['case_number']).first()
        if not existing:
            case = Case(**case_data, created_at=datetime.utcnow())
            db.session.add(case)
            
            # Assign lawyer to case
            case.assigned_users.append(lawyer)
            
            print(f"✓ Created case: {case_data['case_number']} - {case_data['title']}")
        else:
            print(f"✓ Case already exists: {case_data['case_number']}")

def create_sample_tasks():
    """Create sample tasks"""
    print("Creating sample tasks...")
    
    lawyer = User.query.filter_by(role='lawyer').first()
    staff = User.query.filter_by(role='staff').first()
    case = Case.query.first()
    
    if not lawyer or not staff or not case:
        print("⚠ Skipping sample tasks - required users or case not found")
        return
    
    sample_tasks = [
        {
            'title': 'Review contract documents',
            'description': 'Review and analyze the vendor contracts for Johnson Enterprises',
            'priority': 'high',
            'assigned_to_id': lawyer.id,
            'created_by_id': lawyer.id,
            'case_id': case.id,
            'due_date': datetime.utcnow() + timedelta(days=3)
        },
        {
            'title': 'Schedule client meeting',
            'description': 'Schedule follow-up meeting with client to discuss case progress',
            'priority': 'medium',
            'assigned_to_id': staff.id,
            'created_by_id': lawyer.id,
            'case_id': case.id,
            'due_date': datetime.utcnow() + timedelta(days=1)
        },
        {
            'title': 'Prepare court filing',
            'description': 'Prepare and file necessary court documents for the case',
            'priority': 'urgent',
            'assigned_to_id': lawyer.id,
            'created_by_id': lawyer.id,
            'case_id': case.id,
            'due_date': datetime.utcnow() + timedelta(days=7)
        }
    ]
    
    for task_data in sample_tasks:
        existing = Task.query.filter_by(title=task_data['title']).first()
        if not existing:
            task = Task(**task_data)
            db.session.add(task)
            print(f"✓ Created task: {task_data['title']}")
        else:
            print(f"✓ Task already exists: {task_data['title']}")

def create_email_templates():
    """Create sample email templates"""
    print("Creating email templates...")
    
    admin_user = User.query.filter_by(role='admin').first()
    
    templates = [
        {
            'name': 'Appointment Reminder',
            'subject': 'Appointment Reminder - {appointment_title}',
            'body': '''Dear {client_name},

This is a reminder that you have an appointment scheduled:

Date: {appointment_date}
Time: {appointment_time}
Location: {appointment_location}
Type: {appointment_type}

Please let us know if you need to reschedule.

Best regards,
{firm_name}''',
            'template_type': 'appointment_reminder',
            'created_by_id': admin_user.id if admin_user else None
        },
        {
            'name': 'Invoice Due Notice',
            'subject': 'Invoice Due - {invoice_number}',
            'body': '''Dear {client_name},

This is a notice that your invoice {invoice_number} is due.

Amount Due: ${invoice_amount}
Due Date: {due_date}

Please remit payment at your earliest convenience.

Thank you,
{firm_name}''',
            'template_type': 'invoice_due',
            'created_by_id': admin_user.id if admin_user else None
        },
        {
            'name': 'Welcome New Client',
            'subject': 'Welcome to {firm_name}',
            'body': '''Dear {client_name},

Welcome to {firm_name}! We are pleased to represent you in your legal matter.

Your case number is: {case_number}
Assigned attorney: {attorney_name}

We will keep you informed of all developments in your case.

Best regards,
{firm_name}''',
            'template_type': 'welcome',
            'created_by_id': admin_user.id if admin_user else None
        }
    ]
    
    for template_data in templates:
        existing = EmailTemplate.query.filter_by(name=template_data['name']).first()
        if not existing:
            template = EmailTemplate(**template_data)
            db.session.add(template)
            print(f"✓ Created email template: {template_data['name']}")
        else:
            print(f"✓ Email template already exists: {template_data['name']}")

def update_existing_users():
    """Update existing users with new fields"""
    print("Updating existing users with new fields...")
    
    users = User.query.all()
    for user in users:
        if user.is_active is None:
            user.is_active = True
        if user.created_at is None:
            user.created_at = datetime.utcnow()
        if user.updated_at is None:
            user.updated_at = datetime.utcnow()
        if user.hourly_rate is None:
            user.hourly_rate = 0.0
    
    print(f"✓ Updated {len(users)} existing users")

def update_existing_clients():
    """Update existing clients with new fields"""
    print("Updating existing clients with new fields...")
    
    clients = Client.query.all()
    for client in clients:
        if client.is_active is None:
            client.is_active = True
        if client.created_at is None:
            client.created_at = datetime.utcnow()
        if client.updated_at is None:
            client.updated_at = datetime.utcnow()
    
    print(f"✓ Updated {len(clients)} existing clients")

def main():
    """Main setup function"""
    print("🚀 Setting up Legal Management System...")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Update existing data first
            update_existing_users()
            update_existing_clients()
            
            # Create new data
            create_default_users()
            create_system_settings()
            create_sample_clients()
            create_sample_cases()
            create_sample_tasks()
            create_email_templates()
            
            # Commit all changes
            db.session.commit()
            
            print("=" * 50)
            print("✅ Setup completed successfully!")
            print("\nDefault Login Credentials:")
            print("Admin: username=admin, password=admin123")
            print("Lawyer: username=jdoe, password=lawyer123")
            print("Staff: username=msmith, password=staff123")
            print("\n⚠ IMPORTANT: Change default passwords in production!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during setup: {str(e)}")
            raise

if __name__ == '__main__':
    main()
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, SearchHistory, CaseLaw, AuditLog, SystemSettings, Permission, UserRole, Task, SupportTicket, SupportMessage
from app.utils import permission_required, role_required, log_user_action, validate_email, validate_phone, sanitize_filename, allowed_file, ValidationError, validate_required_fields, validate_numeric_field, validate_date_field, validate_datetime_field
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime
import os, json
from werkzeug.utils import secure_filename
from flask import abort
from functools import wraps

# This can be set in config.py or an environment variable for deployment.
LEGAL_DICTIONARY_PATH = os.path.join(app.root_path, '..', 'legal_dictionary.json')
with open(LEGAL_DICTIONARY_PATH, 'r') as f:
    legal_dictionary = json.load(f)

# User Management Routes
@app.route('/users')
@login_required
@permission_required(Permission.VIEW_ALL_USERS)
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(db.or_(
            User.username.ilike(f'%{search}%'),
            User.first_name.ilike(f'%{search}%'),
            User.last_name.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%')
        ))
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    users = query.order_by(User.last_name, User.first_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users.html', users=users, search=search, role_filter=role_filter)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def new_user():
    if request.method == 'POST':
        try:
            # Validate required fields
            validate_required_fields(request.form, ['username', 'email', 'first_name', 'last_name', 'password', 'role'])
            
            # Check if username or email already exists
            if User.query.filter_by(username=request.form['username']).first():
                flash('Username already exists', 'danger')
                return render_template('user_form.html')
            
            if User.query.filter_by(email=request.form['email']).first():
                flash('Email already exists', 'danger')
                return render_template('user_form.html')
            
            # Validate email format
            if not validate_email(request.form['email']):
                flash('Invalid email format', 'danger')
                return render_template('user_form.html')
            
            # Validate role
            if request.form['role'] not in [role.value for role in UserRole]:
                flash('Invalid role selected', 'danger')
                return render_template('user_form.html')
            
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                role=request.form['role'],
                phone=request.form.get('phone', ''),
                department=request.form.get('department', ''),
                hourly_rate=validate_numeric_field(request.form.get('hourly_rate'), 'Hourly Rate', min_value=0) or 0.0
            )
            
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
            
            log_user_action('CREATE_USER', 'User', user.id, {'username': user.username, 'role': user.role})
            flash('User created successfully!', 'success')
            return redirect(url_for('users'))
            
        except ValidationError as e:
            flash(str(e), 'danger')
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the user', 'danger')
    
    return render_template('user_form.html')

@app.route('/users/<int:id>')
@login_required
@permission_required(Permission.VIEW_ALL_USERS)
def user_detail(id):
    user = User.query.get_or_404(id)
    recent_activities = AuditLog.query.filter_by(user_id=id).order_by(AuditLog.timestamp.desc()).limit(10).all()
    return render_template('user_detail.html', user=user, recent_activities=recent_activities)

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def edit_user(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validate required fields
            validate_required_fields(request.form, ['username', 'email', 'first_name', 'last_name', 'role'])
            
            # Check if username or email already exists (excluding current user)
            existing_user = User.query.filter(User.username == request.form['username'], User.id != id).first()
            if existing_user:
                flash('Username already exists', 'danger')
                return render_template('user_form.html', user=user)
            
            existing_user = User.query.filter(User.email == request.form['email'], User.id != id).first()
            if existing_user:
                flash('Email already exists', 'danger')
                return render_template('user_form.html', user=user)
            
            # Validate email format
            if not validate_email(request.form['email']):
                flash('Invalid email format', 'danger')
                return render_template('user_form.html', user=user)
            
            # Validate role
            if request.form['role'] not in [role.value for role in UserRole]:
                flash('Invalid role selected', 'danger')
                return render_template('user_form.html', user=user)
            
            old_data = {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
            
            user.username = request.form['username']
            user.email = request.form['email']
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.role = request.form['role']
            user.phone = request.form.get('phone', '')
            user.department = request.form.get('department', '')
            user.hourly_rate = validate_numeric_field(request.form.get('hourly_rate'), 'Hourly Rate', min_value=0) or 0.0
            user.is_active = bool(request.form.get('is_active'))
            
            # Update password if provided
            if request.form.get('password'):
                user.set_password(request.form['password'])
            
            db.session.commit()
            
            new_data = {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
            
            log_user_action('UPDATE_USER', 'User', user.id, {'old': old_data, 'new': new_data})
            flash('User updated successfully!', 'success')
            return redirect(url_for('users'))
            
        except ValidationError as e:
            flash(str(e), 'danger')
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the user', 'danger')
    
    return render_template('user_form.html', user=user)

@app.route('/users/<int:id>/toggle_status', methods=['POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def toggle_user_status(id):
    user = User.query.get_or_404(id)
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'warning')
        return redirect(url_for('users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = 'ACTIVATE_USER' if user.is_active else 'DEACTIVATE_USER'
    log_user_action(action, 'User', user.id, {'username': user.username})
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'warning')
        return redirect(url_for('users'))
    
    # Check if user has associated data
    if user.time_entries.count() > 0 or user.cases.count() > 0:
        flash('Cannot delete user with associated time entries or cases. Deactivate instead.', 'warning')
        return redirect(url_for('users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    log_user_action('DELETE_USER', 'User', id, {'username': username})
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users'))


# Enhanced Dashboard with Analytics
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    # Basic counts
    client_count = Client.query.filter_by(is_active=True).count()
    case_count = Case.query.count()
    active_cases = Case.query.filter(Case.status.in_(['Open', 'In Progress'])).count()
    appointment_count = Appointment.query.count()
    document_count = Document.query.count()
    time_entry_count = TimeEntry.query.count()
    invoice_count = Invoice.query.count()
    
    # Financial analytics
    total_revenue = db.session.query(func.sum(Invoice.amount)).filter(
        Invoice.status == 'Paid'
    ).scalar() or 0
    
    pending_revenue = db.session.query(func.sum(Invoice.amount)).filter(
        Invoice.status.in_(['Sent', 'Overdue'])
    ).scalar() or 0
    
    # Time analytics
    total_billable_hours = db.session.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.billable == True
    ).scalar() or 0
    
    # Recent activity
    recent_cases = Case.query.order_by(Case.updated_at.desc()).limit(5).all()
    recent_appointments = Appointment.query.filter(
        Appointment.start_time >= datetime.now()
    ).order_by(Appointment.start_time.asc()).limit(5).all()
    
    # Tasks analytics
    my_pending_tasks = Task.query.filter(
        Task.assigned_to_id == current_user.id,
        Task.status.in_(['pending', 'in_progress'])
    ).count()
    
    overdue_tasks = Task.query.filter(
        Task.assigned_to_id == current_user.id,
        Task.due_date < datetime.now(),
        Task.status != 'completed'
    ).count()
    
    # Support tickets
    open_tickets = SupportTicket.query.filter_by(status='open').count()
    my_tickets = SupportTicket.query.filter_by(created_by_id=current_user.id).count()
    
    # Monthly case creation data for chart (last 6 months)
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_cases = db.session.query(
        extract('month', Case.created_at).label('month'),
        extract('year', Case.created_at).label('year'),
        func.count(Case.id).label('count')
    ).filter(
        Case.created_at >= six_months_ago
    ).group_by(
        extract('year', Case.created_at),
        extract('month', Case.created_at)
    ).order_by('year', 'month').all()
    
    # Case status distribution
    case_status_data = db.session.query(
        Case.status,
        func.count(Case.id).label('count')
    ).group_by(Case.status).all()
    
    # Revenue by month (last 6 months)
    monthly_revenue = db.session.query(
        extract('month', Invoice.created_at).label('month'),
        extract('year', Invoice.created_at).label('year'),
        func.sum(Invoice.amount).label('total')
    ).filter(
        Invoice.created_at >= six_months_ago,
        Invoice.status == 'Paid'
    ).group_by(
        extract('year', Invoice.created_at),
        extract('month', Invoice.created_at)
    ).order_by('year', 'month').all()
    
    # Practice area distribution
    practice_area_data = db.session.query(
        Case.practice_area,
        func.count(Case.id).label('count')
    ).filter(
        Case.practice_area.isnot(None)
    ).group_by(Case.practice_area).all()
    
    return render_template('dashboard.html', 
                           # Basic counts
                           client_count=client_count, 
                           case_count=case_count,
                           active_cases=active_cases,
                           appointment_count=appointment_count,
                           document_count=document_count,
                           time_entry_count=time_entry_count,
                           invoice_count=invoice_count,
                           
                           # Financial data
                           total_revenue=total_revenue,
                           pending_revenue=pending_revenue,
                           total_billable_hours=total_billable_hours,
                           
                           # Task data
                           my_pending_tasks=my_pending_tasks,
                           overdue_tasks=overdue_tasks,
                           
                           # Support data
                           open_tickets=open_tickets,
                           my_tickets=my_tickets,
                           
                           # Recent activity
                           recent_cases=recent_cases,
                           recent_appointments=recent_appointments,
                           
                           # Chart data
                           monthly_cases=monthly_cases,
                           case_status_data=case_status_data,
                           monthly_revenue=monthly_revenue,
                           practice_area_data=practice_area_data)

# Client Management
@app.route('/clients')
@login_required
@permission_required(Permission.VIEW_CLIENTS)
def clients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Client.query.filter_by(is_active=True)
    
    # Apply search filter
    if search:
        query = query.filter(db.or_(
            Client.first_name.ilike(f'%{search}%'),
            Client.last_name.ilike(f'%{search}%'),
            Client.email.ilike(f'%{search}%'),
            Client.company.ilike(f'%{search}%')
        ))
    
    # Apply category filter
    if category:
        query = query.filter(Client.category == category)
    
    # For non-admin users, only show clients they have access to
    if current_user.role != 'admin':
        client_ids = [case.client_id for case in current_user.cases]
        if client_ids:
            query = query.filter(Client.id.in_(client_ids))
        else:
            query = query.filter(Client.id == -1)  # No results
    
    clients = query.order_by(Client.last_name, Client.first_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = db.session.query(Client.category).distinct().filter(Client.category.isnot(None)).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('clients.html', clients=clients, search=search, category=category, categories=categories)

@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.CREATE_CLIENTS)
def new_client():
    if request.method == 'POST':
        try:
            # Validate required fields
            validate_required_fields(request.form, ['first_name', 'last_name'])
            
            # Validate email if provided
            if request.form.get('email') and not validate_email(request.form['email']):
                flash('Invalid email format', 'danger')
                return render_template('client_form.html')
            
            # Validate phone if provided
            if request.form.get('phone') and not validate_phone(request.form['phone']):
                flash('Invalid phone number format', 'danger')
                return render_template('client_form.html')
            
            client = Client(
                first_name=request.form['first_name'].strip(),
                last_name=request.form['last_name'].strip(),
                email=request.form.get('email', '').strip() or None,
                phone=request.form.get('phone', '').strip() or None,
                address=request.form.get('address', '').strip(),
                company=request.form.get('company', '').strip(),
                category=request.form.get('category', '').strip(),
                notes=request.form.get('notes', '').strip(),
                created_by=current_user.id
            )
            
            db.session.add(client)
            db.session.commit()
            
            log_user_action('CREATE_CLIENT', 'Client', client.id, {
                'name': client.get_full_name(),
                'email': client.email,
                'company': client.company
            })
            
            flash('Client created successfully!', 'success')
            return redirect(url_for('clients'))
            
        except ValidationError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the client', 'danger')
    
    return render_template('client_form.html')

@app.route('/clients/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def client_detail(id):
    client = Client.query.get_or_404(id)
    return render_template('client_detail.html', client=client)

@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer'])
def edit_client(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        client.first_name = request.form['first_name']
        client.last_name = request.form['last_name']
        client.email = request.form['email']
        client.phone = request.form['phone']
        client.address = request.form['address']
        client.company = request.form['company']
        client.category = request.form['category']
        client.notes = request.form['notes']
        db.session.commit()
        flash('Client updated successfully!')
        return redirect(url_for('clients'))
    return render_template('client_form.html', client=client)

@app.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!')
    return redirect(url_for('clients'))

# Case Management
@app.route('/cases')
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def cases():
    cases = Case.query.all()
    return render_template('cases.html', cases=cases)

@app.route('/cases/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer'])
def new_case():
    if request.method == 'POST':
        case = Case(
            case_number=request.form['case_number'],
            title=request.form['title'],
            description=request.form['description'],
            status=request.form['status'],
            priority=request.form['priority'],
            practice_area=request.form['practice_area'],
            case_type=request.form['case_type'],
            budget=request.form['budget'],
            client_id=request.form['client_id']
        )
        db.session.add(case)
        db.session.commit()
        flash('Case created successfully!')
        return redirect(url_for('cases'))
    clients = Client.query.all()
    return render_template('case_form.html', clients=clients)

@app.route('/cases/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def case_detail(id):
    case = Case.query.get_or_404(id)
    return render_template('case_detail.html', case=case)

@app.route('/cases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer'])
def edit_case(id):
    case = Case.query.get_or_404(id)
    if request.method == 'POST':
        case.case_number = request.form['case_number']
        case.title = request.form['title']
        case.description = request.form['description']
        case.status = request.form['status']
        case.priority = request.form['priority']
        case.practice_area = request.form['practice_area']
        case.case_type = request.form['case_type']
        case.budget = request.form['budget']
        case.client_id = request.form['client_id']
        db.session.commit()
        flash('Case updated successfully!')
        return redirect(url_for('cases'))
    clients = Client.query.all()
    return render_template('case_form.html', case=case, clients=clients)

@app.route('/cases/<int:id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_case(id):
    case = Case.query.get_or_404(id)
    db.session.delete(case)
    db.session.commit()
    flash('Case deleted successfully!')
    return redirect(url_for('cases'))

# Appointment Management
@app.route('/appointments')
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def appointments():
    appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=appointments)

@app.route('/appointments/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def new_appointment():
    if request.method == 'POST':
        appointment = Appointment(
            title=request.form['title'],
            start_time=datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M'),
            end_time=datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M'),
            location=request.form['location'],
            type=request.form['type'],
            status=request.form['status'],
            notes=request.form['notes'],
            client_id=request.form['client_id'],
            case_id=request.form['case_id'] if request.form['case_id'] else None,
            user_id=current_user.id
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment created successfully!')
        return redirect(url_for('appointments'))
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('appointment_form.html', clients=clients, cases=cases)

@app.route('/appointments/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def appointment_detail(id):
    appointment = Appointment.query.get_or_404(id)
    return render_template('appointment_detail.html', appointment=appointment)

@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def edit_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    if request.method == 'POST':
        appointment.title = request.form['title']
        appointment.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        appointment.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        appointment.location = request.form['location']
        appointment.type = request.form['type']
        appointment.status = request.form['status']
        appointment.notes = request.form['notes']
        appointment.client_id = request.form['client_id']
        appointment.case_id = request.form['case_id'] if request.form['case_id'] else None
        db.session.commit()
        flash('Appointment updated successfully!')
        return redirect(url_for('appointments'))
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('appointment_form.html', appointment=appointment, clients=clients, cases=cases)

@app.route('/appointments/<int:id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment deleted successfully!')
    return redirect(url_for('appointments'))

# Document Management
@app.route('/documents')
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def documents():
    documents = Document.query.all()
    return render_template('documents.html', documents=documents)

@app.route('/documents/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def new_document():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            original_filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            document = Document(
                filename=filename,
                original_filename=original_filename,
                category=request.form['category'],
                description=request.form['description'],
                confidential=True if request.form.get('confidential') else False,
                client_id=request.form['client_id'],
                case_id=request.form['case_id'] if request.form['case_id'] else None,
                uploaded_by=current_user.id
            )
            db.session.add(document)
            db.session.commit()
            flash('Document uploaded successfully!')
            return redirect(url_for('documents'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('document_form.html', clients=clients, cases=cases)

@app.route('/documents/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def document_detail(id):
    document = Document.query.get_or_404(id)
    return render_template('document_detail.html', document=document)

@app.route('/documents/<int:id>/download', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def download_document(id):
    document = Document.query.get_or_404(id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], document.filename, as_attachment=True)

@app.route('/documents/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def edit_document(id):
    document = Document.query.get_or_404(id)
    if request.method == 'POST':
        document.category = request.form['category']
        document.description = request.form['description']
        document.confidential = True if request.form.get('confidential') else False
        document.client_id = request.form['client_id']
        document.case_id = request.form['case_id'] if request.form['case_id'] else None
        db.session.commit()
        flash('Document updated successfully!')
        return redirect(url_for('documents'))
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('document_form.html', document=document, clients=clients, cases=cases)

@app.route('/documents/<int:id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_document(id):
    document = Document.query.get_or_404(id)
    # Delete file from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(document)
    db.session.commit()
    flash('Document deleted successfully!')
    return redirect(url_for('documents'))

# Time Tracking
@app.route('/time_tracking')
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def time_tracking():
    time_entries = TimeEntry.query.all()
    return render_template('time_tracking.html', time_entries=time_entries)

@app.route('/time_entries/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def new_time_entry():
    if request.method == 'POST':
        if not request.form['client_id']:
            flash('Client is required!')
            return redirect(url_for('new_time_entry'))

        time_entry = TimeEntry(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            hours=float(request.form['hours']),
            description=request.form['description'],
            billable=True if request.form.get('billable') else False,
            rate=float(request.form['rate']),
            user_id=current_user.id,
            case_id=request.form['case_id'] if request.form['case_id'] else None,
            client_id=request.form['client_id'],
            status='Draft'
        )
        db.session.add(time_entry)
        db.session.commit()
        flash('Time entry created successfully!')
        return redirect(url_for('time_tracking'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('time_entry_form.html', clients=clients, cases=cases)

@app.route('/time_entries/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def time_entry_detail(id):
    time_entry = TimeEntry.query.get_or_404(id)
    return render_template('time_entry_detail.html', time_entry=time_entry)

@app.route('/time_entries/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def edit_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    if request.method == 'POST':
        time_entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        time_entry.hours = float(request.form['hours'])
        time_entry.description = request.form['description']
        time_entry.billable = True if request.form.get('billable') else False
        time_entry.rate = float(request.form['rate'])
        time_entry.case_id = request.form['case_id'] if request.form['case_id'] else None
        time_entry.client_id = request.form['client_id']
        time_entry.status = request.form['status']
        db.session.commit()
        flash('Time entry updated successfully!')
        return redirect(url_for('time_tracking'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('time_entry_form.html', time_entry=time_entry, clients=clients, cases=cases)

@app.route('/time_entries/<int:id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    db.session.delete(time_entry)
    db.session.commit()
    flash('Time entry deleted successfully!')
    return redirect(url_for('time_tracking'))

# Billing & Invoicing
@app.route('/billing')
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def billing():
    invoices = Invoice.query.all()
    return render_template('billing.html', invoices=invoices)

@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def new_invoice():
    if request.method == 'POST':
        # Generate unique invoice number
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_num = int(last_invoice.invoice_number[3:])
            new_num = last_num + 1
        else:
            new_num = 1000
        invoice_number = f"INV{new_num}"
        
        invoice = Invoice(
            invoice_number=invoice_number,
            issue_date=datetime.strptime(request.form['issue_date'], '%Y-%m-%d'),
            due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d'),
            amount=float(request.form['amount']),
            status=request.form['status'],
            notes=request.form['notes'],
            case_id=request.form['case_id'] if request.form['case_id'] else None,
            client_id=request.form['client_id']
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Invoice created successfully!')
        return redirect(url_for('billing'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('invoice_form.html', clients=clients, cases=cases)

@app.route('/invoices/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def invoice_detail(id):
    invoice = Invoice.query.get_or_404(id)
    payments = Payment.query.filter_by(invoice_id=id).all()
    time_entries = TimeEntry.query.filter_by(invoice_id=id).all()
    return render_template('invoice_detail.html', invoice=invoice, payments=payments, time_entries=time_entries)

@app.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer'])
def edit_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    if request.method == 'POST':
        invoice.issue_date = datetime.strptime(request.form['issue_date'], '%Y-%m-%d')
        invoice.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        invoice.amount = float(request.form['amount'])
        invoice.status = request.form['status']
        invoice.notes = request.form['notes']
        invoice.case_id = request.form['case_id'] if request.form['case_id'] else None
        invoice.client_id = request.form['client_id']
        db.session.commit()
        flash('Invoice updated successfully!')
        return redirect(url_for('billing'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('invoice_form.html', invoice=invoice, clients=clients, cases=cases)

@app.route('/invoices/<int:id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted successfully!')
    return redirect(url_for('billing'))

@app.route('/invoices/<int:id>/add_payment', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def add_payment(id):
    invoice = Invoice.query.get_or_404(id)
    payment = Payment(
        amount=float(request.form['amount']),
        payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d'),
        method=request.form['method'],
        reference=request.form['reference'],
        invoice_id=id
    )
    db.session.add(payment)
    
    # Update invoice status if fully paid
    total_paid = sum(p.amount for p in invoice.payments) + float(request.form['amount'])
    if total_paid >= invoice.amount:
        invoice.status = 'Paid'
    
    db.session.commit()
    flash('Payment added successfully!')
    return redirect(url_for('invoice_detail', id=id))

# Search related routes
@app.route('/search')
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def search():
    return render_template('search.html')

@app.route('/api/dictionary', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def api_dictionary():
    term = request.args.get('term', '').lower()

    results = [item for item in legal_dictionary['legal_terms'] if term in item['term'].lower()]

    return jsonify(results)

@app.route('/api/citation', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def api_citation():
    citation = request.args.get('citation', '')

    # Mock citation checker for now - always returns valid
    return jsonify({'valid': True, 'citation': citation})

@app.route('/api/internal-search', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def api_internal_search():
    query = request.args.get('q', '').lower()
    jurisdiction = request.args.get('jurisdiction', '').lower()
    case_type = request.args.get('case_type', '').lower()
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    
    date_from = datetime.strptime(date_from_str, '%Y-%m-%d') if date_from_str else None
    date_to = datetime.strptime(date_to_str, '%Y-%m-%d') if date_to_str else None

    results = Document.query

    if query:
        results = results.filter(db.or_(
            Document.filename.ilike(f'%{query}%'),
            Document.original_filename.ilike(f'%{query}%'),
            Document.category.ilike(f'%{query}%'),
            Document.description.ilike(f'%{query}%')
        ))

    if jurisdiction:
        results = results.filter(Document.category.ilike(f'%{jurisdiction}%'))

    if case_type:
        results = results.filter(Document.category.ilike(f'%{case_type}%'))

    if date_from:
        results = results.filter(Document.uploaded_at >= date_from)
    if date_to:
        results = results.filter(Document.uploaded_at <= date_to)
    
    results = results.all()

    results_list = [{
        'id': doc.id,
        'filename': doc.filename,
        'original_filename': doc.original_filename,
        'category': doc.category,
        'description': doc.description,
        'confidential': doc.confidential,
        'client_id': doc.client_id,
        'case_id': doc.case_id,
        'uploaded_at': doc.uploaded_at.isoformat()
    } for doc in results]

    search_history_entry = SearchHistory(
        query=query,
        search_type='internal',
        jurisdiction=jurisdiction,
        case_type=case_type,
        date_from=date_from,
        date_to=date_to,
        results={'documents': results_list},
        user_id=current_user.id
    )
    db.session.add(search_history_entry)
    db.session.commit()

    return jsonify({"results": results_list})
    
@app.route('/api/case-law-search', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
def api_case_law_search():
    query = request.args.get('q', '').lower()
    year = request.args.get('year', type=int)
    court = request.args.get('court', '').lower()
    jurisdiction = request.args.get('jurisdiction', '').lower()

    results = CaseLaw.query

    if query:
        results = results.filter(db.or_(
            CaseLaw.title.ilike(f'%{query}%'),
            CaseLaw.citation.ilike(f'%{query}%'),
            CaseLaw.summary.ilike(f'%{query}%'),
            CaseLaw.full_text.ilike(f'%{query}%')
        ))
    if year:
        results = results.filter(CaseLaw.year == year)
    if court:
        results = results.filter(CaseLaw.court.ilike(f'%{court}%'))
    if jurisdiction:
        results = results.filter(CaseLaw.jurisdiction.ilike(f'%{jurisdiction}%'))

    results = results.all()

    results_list = [{
        'id': cl.id,
        'title': cl.title,
        'citation': cl.citation,
        'year': cl.year,
        'court': cl.court,
        'jurisdiction': cl.jurisdiction,
        'summary': cl.summary,
        'full_text': cl.full_text,
        'created_at': cl.created_at.isoformat()
    } for cl in results]

    # Create search history entry for case law search
    search_history_entry = SearchHistory(
        query=query,
        search_type='case_law',
        year=year,
        court=court,
        jurisdiction=jurisdiction,
        results={'case_law': results_list},
        user_id=current_user.id
    )
    db.session.add(search_history_entry)
    db.session.commit()

    return jsonify({"results": results_list})

@app.route('/api/external-search', methods=['GET'])
@login_required
@permission_required(Permission.SEARCH_EXTERNAL)
def api_external_search():
    from app.search_engines import LegalSearchAggregator, SearchEngineError, extract_citations, categorize_legal_content
    
    query = request.args.get('q', '')
    search_engine = request.args.get('search_engine', 'google')
    search_type = request.args.get('search_type', 'general')  # 'general' or 'legal_sites'
    num_results = min(int(request.args.get('num_results', 10)), 20)  # Max 20 results
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    try:
        aggregator = LegalSearchAggregator()
        
        # Check if the requested engine is available
        available_engines = aggregator.get_available_engines()
        if search_engine not in available_engines:
            # Fallback to first available engine
            search_engine = available_engines[0] if available_engines else 'duckduckgo'
        
        # Perform search based on type
        if search_type == 'legal_sites':
            search_results = aggregator.search_legal_sites(query, search_engine, num_results)
        else:
            search_results = aggregator.search_general(query, search_engine, num_results)
        
        # Enhance results with legal analysis
        enhanced_results = []
        for result in search_results.get('results', []):
            # Extract citations from snippet
            citations = extract_citations(result.get('snippet', ''))
            
            # Categorize content
            categories = categorize_legal_content(
                result.get('title', ''), 
                result.get('snippet', '')
            )
            
            enhanced_result = {
                **result,
                'citations': citations,
                'categories': categories,
                'relevance_score': len(citations) * 2 + len(categories)  # Simple relevance scoring
            }
            enhanced_results.append(enhanced_result)
        
        # Sort by relevance score (highest first)
        enhanced_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Log search history
        search_history_entry = SearchHistory(
            query=query,
            search_type='external',
            search_engine=search_engine,
            results={
                'external_results': enhanced_results,
                'total_results': search_results.get('total_results', 0),
                'search_metadata': {
                    'search_type': search_type,
                    'engine_used': search_engine,
                    'available_engines': available_engines,
                    'errors': search_results.get('errors', [])
                }
            },
            user_id=current_user.id
        )
        db.session.add(search_history_entry)
        db.session.commit()
        
        log_user_action('EXTERNAL_SEARCH', 'Search', None, {
            'query': query,
            'engine': search_engine,
            'results_count': len(enhanced_results)
        })
        
        return jsonify({
            'results': enhanced_results,
            'total_results': search_results.get('total_results', 0),
            'search_engine': search_engine,
            'available_engines': available_engines,
            'query': query,
            'search_type': search_type,
            'errors': search_results.get('errors', [])
        })
        
    except SearchEngineError as e:
        error_msg = f"Search engine error: {str(e)}"
        
        # Log the error
        search_history_entry = SearchHistory(
            query=query,
            search_type='external',
            search_engine=search_engine,
            results={'error': error_msg},
            user_id=current_user.id
        )
        db.session.add(search_history_entry)
        db.session.commit()
        
        return jsonify({'error': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        return jsonify({'error': error_msg}), 500

@app.route('/api/search/engines', methods=['GET'])
@login_required
@permission_required(Permission.SEARCH_EXTERNAL)
def api_search_engines():
    """Get available search engines"""
    from app.search_engines import LegalSearchAggregator
    
    try:
        aggregator = LegalSearchAggregator()
        available_engines = aggregator.get_available_engines()
        
        engine_info = {
            'google': {
                'name': 'Google',
                'description': 'Google Custom Search with legal focus',
                'requires_api_key': True
            },
            'bing': {
                'name': 'Bing',
                'description': 'Microsoft Bing Web Search',
                'requires_api_key': True
            },
            'duckduckgo': {
                'name': 'DuckDuckGo',
                'description': 'Privacy-focused search (limited results)',
                'requires_api_key': False
            }
        }
        
        engines = []
        for engine in available_engines:
            if engine in engine_info:
                engines.append({
                    'id': engine,
                    **engine_info[engine],
                    'available': True
                })
        
        return jsonify({
            'engines': engines,
            'default': available_engines[0] if available_engines else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/history', methods=['GET'])
@login_required
@permission_required(Permission.SEARCH_INTERNAL)
def api_search_history():
    history = SearchHistory.query.filter_by(user_id=current_user.id)\
                               .order_by(SearchHistory.created_at.desc())\
                               .limit(10).all()
    
    history_data = []
    for item in history:
        results = item.results if item.results is not None else {}
        
        if item.search_type == 'internal':
            displayed_results = results.get('documents', [])
            result_count = len(displayed_results)
            search_source = 'Internal'
        elif item.search_type == 'external':
            displayed_results = results.get('external_results', [])
            result_count = len(displayed_results)
            search_source = item.search_engine
        else:
            displayed_results = []
            result_count = 0
            search_source = 'Unknown'

        history_data.append({
            "id": item.id,
            "query": item.query,
            "search_type": item.search_type,
            "search_source": search_source,
            "results_count": result_count,
            "created_at": item.created_at.isoformat()
        })
    
    return jsonify(history_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Username and password are required', 'danger')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user is None or not user.check_password(password):
                # Log failed login attempt
                log_user_action('FAILED_LOGIN', 'User', None, {
                    'username': username,
                    'ip_address': request.remote_addr
                })
                flash('Invalid username or password', 'danger')
                return render_template('login.html')
            
            # Check if user is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'warning')
                return render_template('login.html')
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=bool(request.form.get('remember-me')))
            
            # Log successful login
            log_user_action('SUCCESSFUL_LOGIN', 'User', user.id, {
                'username': user.username,
                'ip_address': request.remote_addr
            })
            
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
            
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')

# Support System Routes
@app.route('/support')
@login_required
def support_tickets():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    query = SupportTicket.query
    
    # Filter by user role
    if current_user.role != 'admin':
        query = query.filter_by(created_by_id=current_user.id)
    
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    
    if priority_filter:
        query = query.filter(SupportTicket.priority == priority_filter)
    
    tickets = query.order_by(SupportTicket.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('support/tickets.html', tickets=tickets, 
                         status_filter=status_filter, priority_filter=priority_filter)

@app.route('/support/new', methods=['GET', 'POST'])
@login_required
def new_support_ticket():
    if request.method == 'POST':
        try:
            validate_required_fields(request.form, ['subject', 'description', 'category'])
            
            ticket = SupportTicket(
                ticket_number=SupportTicket.generate_ticket_number(),
                subject=request.form['subject'].strip(),
                description=request.form['description'].strip(),
                priority=request.form.get('priority', 'medium'),
                category=request.form.get('category', 'general'),
                created_by_id=current_user.id
            )
            
            db.session.add(ticket)
            db.session.commit()
            
            log_user_action('CREATE_SUPPORT_TICKET', 'SupportTicket', ticket.id, {
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject
            })
            
            flash('Support ticket created successfully!', 'success')
            return redirect(url_for('support_tickets'))
            
        except ValidationError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the ticket', 'danger')
    
    return render_template('support/ticket_form.html')

@app.route('/support/<int:id>')
@login_required
def support_ticket_detail(id):
    ticket = SupportTicket.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and ticket.created_by_id != current_user.id:
        flash('You do not have permission to view this ticket', 'danger')
        return redirect(url_for('support_tickets'))
    
    return render_template('support/ticket_detail.html', ticket=ticket)

@app.route('/support/<int:id>/reply', methods=['POST'])
@login_required
def reply_support_ticket(id):
    ticket = SupportTicket.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and ticket.created_by_id != current_user.id:
        flash('You do not have permission to reply to this ticket', 'danger')
        return redirect(url_for('support_tickets'))
    
    try:
        message_text = request.form.get('message', '').strip()
        if not message_text:
            flash('Message cannot be empty', 'danger')
            return redirect(url_for('support_ticket_detail', id=id))
        
        message = SupportMessage(
            message=message_text,
            ticket_id=ticket.id,
            user_id=current_user.id,
            is_internal=bool(request.form.get('is_internal')) and current_user.role == 'admin'
        )
        
        db.session.add(message)
        
        # Update ticket status if admin is replying
        if current_user.role == 'admin' and ticket.status == 'open':
            ticket.status = 'in_progress'
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_user_action('REPLY_SUPPORT_TICKET', 'SupportTicket', ticket.id, {
            'ticket_number': ticket.ticket_number
        })
        
        flash('Reply added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding the reply', 'danger')
    
    return redirect(url_for('support_ticket_detail', id=id))

@app.route('/support/<int:id>/close', methods=['POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)  # Only admins can close tickets
def close_support_ticket(id):
    ticket = SupportTicket.query.get_or_404(id)
    
    ticket.status = 'closed'
    ticket.resolved_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_user_action('CLOSE_SUPPORT_TICKET', 'SupportTicket', ticket.id, {
        'ticket_number': ticket.ticket_number
    })
    
    flash('Ticket closed successfully!', 'success')
    return redirect(url_for('support_ticket_detail', id=id))

# Task Management Routes
@app.route('/tasks')
@login_required
def tasks():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    assigned_filter = request.args.get('assigned', '')
    
    query = Task.query
    
    # Filter by user role
    if current_user.role != 'admin':
        query = query.filter(db.or_(
            Task.assigned_to_id == current_user.id,
            Task.created_by_id == current_user.id
        ))
    
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    if assigned_filter == 'me':
        query = query.filter(Task.assigned_to_id == current_user.id)
    elif assigned_filter == 'unassigned':
        query = query.filter(Task.assigned_to_id.is_(None))
    
    tasks = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('tasks/tasks.html', tasks=tasks, 
                         status_filter=status_filter, assigned_filter=assigned_filter)

@app.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        try:
            validate_required_fields(request.form, ['title'])
            
            task = Task(
                title=request.form['title'].strip(),
                description=request.form.get('description', '').strip(),
                priority=request.form.get('priority', 'medium'),
                assigned_to_id=request.form.get('assigned_to_id') or None,
                case_id=request.form.get('case_id') or None,
                client_id=request.form.get('client_id') or None,
                created_by_id=current_user.id
            )
            
            if request.form.get('due_date'):
                task.due_date = validate_datetime_field(request.form['due_date'], 'Due Date')
            
            db.session.add(task)
            db.session.commit()
            
            log_user_action('CREATE_TASK', 'Task', task.id, {
                'title': task.title,
                'assigned_to': task.assigned_to.get_full_name() if task.assigned_to else None
            })
            
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks'))
            
        except ValidationError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the task', 'danger')
    
    users = User.query.filter_by(is_active=True).all()
    cases = Case.query.filter(Case.status.in_(['Open', 'In Progress'])).all()
    clients = Client.query.filter_by(is_active=True).all()
    
    return render_template('tasks/task_form.html', users=users, cases=cases, clients=clients)

@app.route('/tasks/<int:id>/complete', methods=['POST'])
@login_required
def complete_task(id):
    task = Task.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and task.assigned_to_id != current_user.id and task.created_by_id != current_user.id:
        flash('You do not have permission to complete this task', 'danger')
        return redirect(url_for('tasks'))
    
    task.status = 'completed'
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_user_action('COMPLETE_TASK', 'Task', task.id, {'title': task.title})
    
    flash('Task marked as completed!', 'success')
    return redirect(url_for('tasks'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Helper function to check file extension
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dashboard
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Get some statistics for the dashboard
    client_count = Client.query.count()
    case_count = Case.query.count()
    appointment_count = Appointment.query.count()
    document_count = Document.query.count()
    time_entry_count = TimeEntry.query.count()
    invoice_count = Invoice.query.count()
    
    # Get recent cases, appointments, etc.
    recent_cases = Case.query.order_by(Case.updated_at.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.start_time.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           client_count=client_count, 
                           case_count=case_count,
                           appointment_count=appointment_count,
                           document_count=document_count,
                           time_entry_count=time_entry_count,
                           invoice_count=invoice_count,
                           recent_cases=recent_cases,
                           recent_appointments=recent_appointments)

# Client Management
@app.route('/clients')
@login_required
def clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    if request.method == 'POST':
        client = Client(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone=request.form['phone'],
            address=request.form['address'],
            company=request.form['company'],
            category=request.form['category'],
            notes=request.form['notes']
        )
        db.session.add(client)
        db.session.commit()
        flash('Client created successfully!')
        return redirect(url_for('clients'))
    return render_template('client_form.html')

@app.route('/clients/<int:id>', methods=['GET'])
@login_required
def client_detail(id):
    client = Client.query.get_or_404(id)
    return render_template('client_detail.html', client=client)

@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!')
    return redirect(url_for('clients'))

# Case Management
@app.route('/cases')
@login_required
def cases():
    cases = Case.query.all()
    return render_template('cases.html', cases=cases)

@app.route('/cases/new', methods=['GET', 'POST'])
@login_required
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
def case_detail(id):
    case = Case.query.get_or_404(id)
    return render_template('case_detail.html', case=case)

@app.route('/cases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
def delete_case(id):
    case = Case.query.get_or_404(id)
    db.session.delete(case)
    db.session.commit()
    flash('Case deleted successfully!')
    return redirect(url_for('cases'))

# Appointment Management
@app.route('/appointments')
@login_required
def appointments():
    appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=appointments)

@app.route('/appointments/new', methods=['GET', 'POST'])
@login_required
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
def appointment_detail(id):
    appointment = Appointment.query.get_or_404(id)
    return render_template('appointment_detail.html', appointment=appointment)

@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
def delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment deleted successfully!')
    return redirect(url_for('appointments'))

# Document Management
@app.route('/documents')
@login_required
def documents():
    documents = Document.query.all()
    return render_template('documents.html', documents=documents)

@app.route('/documents/new', methods=['GET', 'POST'])
@login_required
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
def document_detail(id):
    document = Document.query.get_or_404(id)
    return render_template('document_detail.html', document=document)

@app.route('/documents/<int:id>/download', methods=['GET'])
@login_required
def download_document(id):
    document = Document.query.get_or_404(id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], document.filename, as_attachment=True)

@app.route('/documents/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
def time_tracking():
    time_entries = TimeEntry.query.all()
    return render_template('time_tracking.html', time_entries=time_entries)

@app.route('/time_entries/new', methods=['GET', 'POST'])
@login_required
def new_time_entry():
    if request.method == 'POST':
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
def time_entry_detail(id):
    time_entry = TimeEntry.query.get_or_404(id)
    return render_template('time_entry_detail.html', time_entry=time_entry)

@app.route('/time_entries/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
def delete_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    db.session.delete(time_entry)
    db.session.commit()
    flash('Time entry deleted successfully!')
    return redirect(url_for('time_tracking'))

# Billing & Invoicing
@app.route('/billing')
@login_required
def billing():
    invoices = Invoice.query.all()
    return render_template('billing.html', invoices=invoices)

@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
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
def invoice_detail(id):
    invoice = Invoice.query.get_or_404(id)
    payments = Payment.query.filter_by(invoice_id=id).all()
    time_entries = TimeEntry.query.filter_by(invoice_id=id).all()
    return render_template('invoice_detail.html', invoice=invoice, payments=payments, time_entries=time_entries)

@app.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted successfully!')
    return redirect(url_for('billing'))

@app.route('/invoices/<int:id>/add_payment', methods=['POST'])
@login_required
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

# Search
@app.route('/search')
@login_required
def search():
    return render_template('search.html')

# API Routes
@app.route('/api/clients', methods=['GET'])
@login_required
def api_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': client.id,
        'first_name': client.first_name,
        'last_name': client.last_name,
        'email': client.email,
        'phone': client.phone,
        'address': client.address,
        'company': client.company,
        'category': client.category,
        'notes': client.notes
    } for client in clients])

@app.route('/api/clients', methods=['POST'])
@login_required
def api_create_client():
    data = request.get_json()
    client = Client(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        address=data['address'],
        company=data['company'],
        category=data['category'],
        notes=data['notes']
    )
    db.session.add(client)
    db.session.commit()
    return jsonify({'id': client.id}), 201

@app.route('/api/clients/<int:id>', methods=['GET'])
@login_required
def api_client(id):
    client = Client.query.get_or_404(id)
    return jsonify({
        'id': client.id,
        'first_name': client.first_name,
        'last_name': client.last_name,
        'email': client.email,
        'phone': client.phone,
        'address': client.address,
        'company': client.company,
        'category': client.category,
        'notes': client.notes
    })

@app.route('/api/clients/<int:id>', methods=['PUT'])
@login_required
def api_update_client(id):
    client = Client.query.get_or_404(id)
    data = request.get_json()
    client.first_name = data['first_name']
    client.last_name = data['last_name']
    client.email = data['email']
    client.phone = data['phone']
    client.address = data['address']
    client.company = data['company']
    client.category = data['category']
    client.notes = data['notes']
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/clients/<int:id>', methods=['DELETE'])
@login_required
def api_delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({'status': 'success'})

# Case API
@app.route('/api/cases', methods=['GET'])
@login_required
def api_cases():
    cases = Case.query.all()
    return jsonify([{
        'id': case.id,
        'case_number': case.case_number,
        'title': case.title,
        'description': case.description,
        'status': case.status,
        'priority': case.priority,
        'practice_area': case.practice_area,
        'case_type': case.case_type,
        'budget': case.budget,
        'client_id': case.client_id,
        'client_name': f"{case.client.first_name} {case.client.last_name}" if case.client else None
    } for case in cases])

@app.route('/api/cases', methods=['POST'])
@login_required
def api_create_case():
    data = request.get_json()
    case = Case(
        case_number=data['case_number'],
        title=data['title'],
        description=data['description'],
        status=data['status'],
        priority=data['priority'],
        practice_area=data['practice_area'],
        case_type=data['case_type'],
        budget=data['budget'],
        client_id=data['client_id']
    )
    db.session.add(case)
    db.session.commit()
    return jsonify({'id': case.id}), 201

@app.route('/api/cases/<int:id>', methods=['GET'])
@login_required
def api_case(id):
    case = Case.query.get_or_404(id)
    return jsonify({
        'id': case.id,
        'case_number': case.case_number,
        'title': case.title,
        'description': case.description,
        'status': case.status,
        'priority': case.priority,
        'practice_area': case.practice_area,
        'case_type': case.case_type,
        'budget': case.budget,
        'client_id': case.client_id,
        'client_name': f"{case.client.first_name} {case.client.last_name}" if case.client else None
    })

@app.route('/api/cases/<int:id>', methods=['PUT'])
@login_required
def api_update_case(id):
    case = Case.query.get_or_404(id)
    data = request.get_json()
    case.case_number = data['case_number']
    case.title = data['title']
    case.description = data['description']
    case.status = data['status']
    case.priority = data['priority']
    case.practice_area = data['practice_area']
    case.case_type = data['case_type']
    case.budget = data['budget']
    case.client_id = data['client_id']
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/cases/<int:id>', methods=['DELETE'])
@login_required
def api_delete_case(id):
    case = Case.query.get_or_404(id)
    db.session.delete(case)
    db.session.commit()
    return jsonify({'status': 'success'})

# Appointment API
@app.route('/api/appointments', methods=['GET'])
@login_required
def api_appointments():
    appointments = Appointment.query.all()
    return jsonify([{
        'id': appointment.id,
        'title': appointment.title,
        'start_time': appointment.start_time.isoformat(),
        'end_time': appointment.end_time.isoformat(),
        'location': appointment.location,
        'type': appointment.type,
        'status': appointment.status,
        'notes': appointment.notes,
        'client_id': appointment.client_id,
        'client_name': f"{appointment.client.first_name} {appointment.client.last_name}" if appointment.client else None,
        'case_id': appointment.case_id,
        'case_title': appointment.case.title if appointment.case else None,
        'user_id': appointment.user_id,
        'user_name': f"{appointment.user.first_name} {appointment.user.last_name}"
    } for appointment in appointments])

@app.route('/api/appointments', methods=['POST'])
@login_required
def api_create_appointment():
    data = request.get_json()
    appointment = Appointment(
        title=data['title'],
        start_time=datetime.fromisoformat(data['start_time']),
        end_time=datetime.fromisoformat(data['end_time']),
        location=data['location'],
        type=data['type'],
        status=data['status'],
        notes=data['notes'],
        client_id=data['client_id'],
        case_id=data.get('case_id'),
        user_id=current_user.id
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify({'id': appointment.id}), 201

@app.route('/api/appointments/<int:id>', methods=['GET'])
@login_required
def api_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    return jsonify({
        'id': appointment.id,
        'title': appointment.title,
        'start_time': appointment.start_time.isoformat(),
        'end_time': appointment.end_time.isoformat(),
        'location': appointment.location,
        'type': appointment.type,
        'status': appointment.status,
        'notes': appointment.notes,
        'client_id': appointment.client_id,
        'client_name': f"{appointment.client.first_name} {appointment.client.last_name}" if appointment.client else None,
        'case_id': appointment.case_id,
        'case_title': appointment.case.title if appointment.case else None,
        'user_id': appointment.user_id,
        'user_name': f"{appointment.user.first_name} {appointment.user.last_name}"
    })

@app.route('/api/appointments/<int:id>', methods=['PUT'])
@login_required
def api_update_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    data = request.get_json()
    appointment.title = data['title']
    appointment.start_time = datetime.fromisoformat(data['start_time'])
    appointment.end_time = datetime.fromisoformat(data['end_time'])
    appointment.location = data['location']
    appointment.type = data['type']
    appointment.status = data['status']
    appointment.notes = data['notes']
    appointment.client_id = data['client_id']
    appointment.case_id = data.get('case_id')
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/appointments/<int:id>', methods=['DELETE'])
@login_required
def api_delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    return jsonify({'status': 'success'})

# Document API
@app.route('/api/documents', methods=['GET'])
@login_required
def api_documents():
    documents = Document.query.all()
    return jsonify([{
        'id': document.id,
        'filename': document.filename,
        'original_filename': document.original_filename,
        'category': document.category,
        'description': document.description,
        'confidential': document.confidential,
        'version': document.version,
        'client_id': document.client_id,
        'client_name': f"{document.client.first_name} {document.client.last_name}" if document.client else None,
        'case_id': document.case_id,
        'case_title': document.case.title if document.case else None,
        'uploaded_at': document.uploaded_at.isoformat(),
        'uploaded_by': document.uploaded_by,
        'uploader_name': f"{document.uploader.first_name} {document.uploader.last_name}"
    } for document in documents])

@app.route('/api/documents', methods=['POST'])
@login_required
def api_upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
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
            case_id=request.form.get('case_id'),
            uploaded_by=current_user.id
        )
        db.session.add(document)
        db.session.commit()
        return jsonify({'id': document.id}), 201
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/documents/<int:id>', methods=['GET'])
@login_required
def api_document(id):
    document = Document.query.get_or_404(id)
    return jsonify({
        'id': document.id,
        'filename': document.filename,
        'original_filename': document.original_filename,
        'category': document.category,
        'description': document.description,
        'confidential': document.confidential,
        'version': document.version,
        'client_id': document.client_id,
        'client_name': f"{document.client.first_name} {document.client.last_name}" if document.client else None,
        'case_id': document.case_id,
        'case_title': document.case.title if document.case else None,
        'uploaded_at': document.uploaded_at.isoformat(),
        'uploaded_by': document.uploaded_by,
        'uploader_name': f"{document.uploader.first_name} {document.uploader.last_name}"
    })

@app.route('/api/documents/<int:id>', methods=['PUT'])
@login_required
def api_update_document(id):
    document = Document.query.get_or_404(id)
    data = request.get_json()
    document.category = data['category']
    document.description = data['description']
    document.confidential = data['confidential']
    document.client_id = data['client_id']
    document.case_id = data.get('case_id')
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/documents/<int:id>', methods=['DELETE'])
@login_required
def api_delete_document(id):
    document = Document.query.get_or_404(id)
    # Delete file from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(document)
    db.session.commit()
    return jsonify({'status': 'success'})

# Time Entry API
@app.route('/api/time_entries', methods=['GET'])
@login_required
def api_time_entries():
    time_entries = TimeEntry.query.all()
    return jsonify([{
        'id': entry.id,
        'date': entry.date.isoformat(),
        'hours': entry.hours,
        'description': entry.description,
        'billable': entry.billable,
        'rate': entry.rate,
        'user_id': entry.user_id,
        'user_name': f"{entry.user.first_name} {entry.user.last_name}",
        'case_id': entry.case_id,
        'case_title': entry.case.title if entry.case else None,
        'client_id': entry.client_id,
        'client_name': f"{entry.client.first_name} {entry.client.last_name}",
        'invoice_id': entry.invoice_id,
        'status': entry.status
    } for entry in time_entries])

@app.route('/api/time_entries', methods=['POST'])
@login_required
def api_create_time_entry():
    data = request.get_json()
    time_entry = TimeEntry(
        date=datetime.fromisoformat(data['date']),
        hours=data['hours'],
        description=data['description'],
        billable=data['billable'],
        rate=data['rate'],
        user_id=current_user.id,
        case_id=data.get('case_id'),
        client_id=data['client_id'],
        status='Draft'
    )
    db.session.add(time_entry)
    db.session.commit()
    return jsonify({'id': time_entry.id}), 201

@app.route('/api/time_entries/<int:id>', methods=['GET'])
@login_required
def api_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    return jsonify({
        'id': time_entry.id,
        'date': time_entry.date.isoformat(),
        'hours': time_entry.hours,
        'description': time_entry.description,
        'billable': time_entry.billable,
        'rate': time_entry.rate,
        'user_id': time_entry.user_id,
        'user_name': f"{time_entry.user.first_name} {time_entry.user.last_name}",
        'case_id': time_entry.case_id,
        'case_title': time_entry.case.title if time_entry.case else None,
        'client_id': time_entry.client_id,
        'client_name': f"{time_entry.client.first_name} {time_entry.client.last_name}",
        'invoice_id': time_entry.invoice_id,
        'status': time_entry.status
    })

@app.route('/api/time_entries/<int:id>', methods=['PUT'])
@login_required
def api_update_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    data = request.get_json()
    time_entry.date = datetime.fromisoformat(data['date'])
    time_entry.hours = data['hours']
    time_entry.description = data['description']
    time_entry.billable = data['billable']
    time_entry.rate = data['rate']
    time_entry.case_id = data.get('case_id')
    time_entry.client_id = data['client_id']
    time_entry.status = data['status']
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/time_entries/<int:id>', methods=['DELETE'])
@login_required
def api_delete_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    db.session.delete(time_entry)
    db.session.commit()
    return jsonify({'status': 'success'})

# Invoice API
@app.route('/api/invoices', methods=['GET'])
@login_required
def api_invoices():
    invoices = Invoice.query.all()
    return jsonify([{
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'issue_date': invoice.issue_date.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'amount': invoice.amount,
        'status': invoice.status,
        'notes': invoice.notes,
        'case_id': invoice.case_id,
        'case_title': invoice.case.title if invoice.case else None,
        'client_id': invoice.client_id,
        'client_name': f"{invoice.client.first_name} {invoice.client.last_name}",
        'payments': [{
            'id': payment.id,
            'amount': payment.amount,
            'payment_date': payment.payment_date.isoformat(),
            'method': payment.method,
            'reference': payment.reference
        } for payment in invoice.payments]
    } for invoice in invoices])

@app.route('/api/invoices', methods=['POST'])
@login_required
def api_create_invoice():
    data = request.get_json()
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
        issue_date=datetime.fromisoformat(data['issue_date']),
        due_date=datetime.fromisoformat(data['due_date']),
        amount=data['amount'],
        status=data['status'],
        notes=data['notes'],
        case_id=data.get('case_id'),
        client_id=data['client_id']
    )
    db.session.add(invoice)
    db.session.commit()
    return jsonify({'id': invoice.id}), 201

@app.route('/api/invoices/<int:id>', methods=['GET'])
@login_required
def api_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return jsonify({
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'issue_date': invoice.issue_date.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'amount': invoice.amount,
        'status': invoice.status,
        'notes': invoice.notes,
        'case_id': invoice.case_id,
        'case_title': invoice.case.title if invoice.case else None,
        'client_id': invoice.client_id,
        'client_name': f"{invoice.client.first_name} {invoice.client.last_name}",
        'payments': [{
            'id': payment.id,
            'amount': payment.amount,
            'payment_date': payment.payment_date.isoformat(),
            'method': payment.method,
            'reference': payment.reference
        } for payment in invoice.payments]
    })

@app.route('/api/invoices/<int:id>', methods=['PUT'])
@login_required
def api_update_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    data = request.get_json()
    invoice.issue_date = datetime.fromisoformat(data['issue_date'])
    invoice.due_date = datetime.fromisoformat(data['due_date'])
    invoice.amount = data['amount']
    invoice.status = data['status']
    invoice.notes = data['notes']
    invoice.case_id = data.get('case_id')
    invoice.client_id = data['client_id']
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/invoices/<int:id>', methods=['DELETE'])
@login_required
def api_delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    return jsonify({'status': 'success'})

# Search API
@app.route('/api/search', methods=['GET'])
@login_required
def api_search():
    query = request.args.get('q', '')
    jurisdiction = request.args.get('jurisdiction', '')
    case_type = request.args.get('case_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # In a real implementation, this would query a legal database
    # For this example, we'll return mock results
    results = [
        {
            'id': 1,
            'title': 'Smith v. Johnson',
            'type': 'Case Law',
            'jurisdiction': 'Federal',
            'date': '2023-05-15',
            'summary': 'A landmark case in contract law that established new precedents for breach of contract claims.',
            'citation': '123 U.S. 456 (2023)'
        },
        {
            'id': 2,
            'title': 'Doe v. State of California',
            'type': 'Case Law',
            'jurisdiction': 'State',
            'date': '2022-11-30',
            'summary': 'A significant criminal case that redefined the standards for evidence admissibility.',
            'citation': '456 Cal. 789 (2022)'
        },
        {
            'id': 3,
            'title': 'Administrative Law Reform Act',
            'type': 'Statute',
            'jurisdiction': 'Federal',
            'date': '2023-01-20',
            'summary': 'Recent legislation that overhauls administrative procedures at the federal level.',
            'citation': 'Pub. L. 117-123'
        }
    ]
    
    # Filter results based on search parameters
    if query:
        results = [r for r in results if query.lower() in r['title'].lower() or query.lower() in r['summary'].lower()]
    
    if jurisdiction:
        results = [r for r in results if jurisdiction.lower() in r['jurisdiction'].lower()]
    
    if case_type:
        results = [r for r in results if case_type.lower() in r['type'].lower()]
    
    if date_from:
        results = [r for r in results if r['date'] >= date_from]
    
    if date_to:
        results = [r for r in results if r['date'] <= date_to]
    
    return jsonify(results)

# Login and Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=request.form.get('remember-me'))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
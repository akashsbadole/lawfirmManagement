from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, SearchHistory
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime
import os, json
from werkzeug.utils import secure_filename
from flask import abort
from functools import wraps

# Load legal dictionary (JSON) at application startup
# This ensures it's only loaded once when the Flask app initializes.
# Make sure 'legal_dictionary.json' is in the root directory or adjust path.
with open('legal_dictionary.json', 'r') as f:
    legal_dictionary = json.load(f)

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_anonymous or current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.')
                return redirect(url_for('dashboard')) # Redirect to dashboard or login
            return f(*args, **kwargs)
        return decorated_function
    return decorator


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
@role_required(['admin', 'lawyer', 'staff'])
def clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'lawyer'])
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
    
@app.route('/api/external-search', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer'])
def api_external_search():
    query = request.args.get('q', '')
    search_engine = request.args.get('search_engine', 'google')
    
    mock_results = [
        {
            "title": f"Legal Resource: {query} (External)",
            "link": "https://example.com/external-resource",
            "snippet": f"This is an external sample result for: {query}.",
            "citation": "External. v. Ref., 2024 INT.L 100",
            "displayLink": "external.com"
        },
        {
            "title": f"Another External Case: {query}",
            "link": "https://example.com/external-case",
            "snippet": f"Details about another external legal case for: {query}.",
            "citation": "OtherCase, 2024 FED 200",
            "displayLink": "federal-law.com"
        }
    ]
    
    search_history_entry = SearchHistory(
        query=query,
        search_type='external',
        search_engine=search_engine,
        results={'external_results': mock_results},
        user_id=current_user.id
    )
    db.session.add(search_history_entry)
    db.session.commit()
    
    return jsonify({
        "results": mock_results,
        "search_engine": search_engine,
        "query": query
    })

@app.route('/api/search/history', methods=['GET'])
@login_required
@role_required(['admin', 'lawyer', 'staff'])
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
from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, SearchHistory, CaseLaw

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Client': Client, 'Case': Case,
            'Appointment': Appointment, 'Document': Document,
            'TimeEntry': TimeEntry, 'Invoice': Invoice, 'Payment': Payment,
            'SearchHistory': SearchHistory, 'CaseLaw': CaseLaw}

if __name__ == '__main__':
    # You might want to call create_sample_data here if you want to re-populate every run in debug mode
    # For now, it's recommended to run populate_db.py explicitly from the terminal
    app.run(debug=True)
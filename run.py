from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, SearchHistory

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Client': Client, 'Case': Case,
            'Appointment': Appointment, 'Document': Document,
            'TimeEntry': TimeEntry, 'Invoice': Invoice, 'Payment': Payment,
            'SearchHistory': SearchHistory}

if __name__ == '__main__':
    app.run(debug=True)
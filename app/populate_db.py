from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, SearchHistory, CaseLaw
from datetime import datetime
from werkzeug.security import generate_password_hash
import random

def create_sample_data():
    with app.app_context():
        db.create_all() # Ensure all tables are created based on models

        # Create sample users
        if User.query.count() == 0:
            print("Adding sample users...")
            admin_user = User(username='admin', email='admin@example.com', first_name='Admin', last_name='User', role='admin', hourly_rate=0.0)
            admin_user.set_password('adminpass')
            db.session.add(admin_user)

            lawyer_user = User(username='lawyer', email='lawyer@example.com', first_name='Lawyer', last_name='User', role='lawyer', hourly_rate=250.0)
            lawyer_user.set_password('lawyerpass')
            db.session.add(lawyer_user)

            staff_user = User(username='staff', email='staff@example.com', first_name='Staff', last_name='User', role='staff', hourly_rate=50.0)
            staff_user.set_password('staffpass')
            db.session.add(staff_user)
            db.session.commit()

        # Create sample clients
        if Client.query.count() == 0:
            print("Adding sample clients...")
            client1 = Client(first_name='Alice', last_name='Smith', email='alice@example.com', phone='111-222-3333', address='123 Main St', company='ABC Corp', category='Individual', notes='Initial consultation on estate planning.')
            client2 = Client(first_name='Bob', last_name='Johnson', email='bob@example.com', phone='444-555-6666', address='456 Oak Ave', company='XYZ Inc', category='Corporate', notes='Ongoing litigation support.')
            db.session.add_all([client1, client2])
            db.session.commit()
            # Re-fetch clients to ensure they are session-managed for relationships
            client1 = Client.query.filter_by(first_name='Alice').first()
            client2 = Client.query.filter_by(first_name='Bob').first()

        # Create sample cases
        if Case.query.count() == 0:
            print("Adding sample cases...")
            case1 = Case(case_number='CL001', title='Smith v. Jones', description='Civil dispute over property lines.', status='Open', priority='High', practice_area='Real Estate', case_type='Civil', budget=15000.0, client_id=client1.id)
            case2 = Case(case_number='CL002', title='State v. Johnson', description='Criminal defense for fraud charges.', status='In Progress', priority='Urgent', practice_area='Criminal Law', case_type='Criminal', budget=25000.0, client_id=client2.id)
            db.session.add_all([case1, case2])
            db.session.commit()
            # Re-fetch cases
            case1 = Case.query.filter_by(case_number='CL001').first()
            case2 = Case.query.filter_by(case_number='CL002').first()

            # Assign lawyer to cases
            lawyer_user = User.query.filter_by(username='lawyer').first()
            if lawyer_user:
                case1.assigned_users.append(lawyer_user)
                case2.assigned_users.append(lawyer_user)
                db.session.commit()

        # Create sample documents
        if Document.query.count() == 0:
            print("Adding sample documents...")
            doc1 = Document(filename='contract_smith_jones.pdf', original_filename='Contract for Smith v Jones.pdf', category='Contracts', description='Purchase agreement details for Smith property.', client_id=client1.id, case_id=case1.id, uploaded_by=admin_user.id)
            doc2 = Document(filename='police_report_johnson.docx', original_filename='Police Report - Johnson Case.docx', category='Evidence', description='Initial police report regarding the fraud investigation.', client_id=client2.id, case_id=case2.id, uploaded_by=lawyer_user.id)
            doc3 = Document(filename='will_template.pdf', original_filename='Standard Will Template.pdf', category='Templates', description='Generic will template for estate planning.', client_id=None, case_id=None, uploaded_by=staff_user.id)
            db.session.add_all([doc1, doc2, doc3])
            db.session.commit()
            doc1 = Document.query.filter_by(filename='contract_smith_jones.pdf').first()


        # Create sample appointments
        if Appointment.query.count() == 0:
            print("Adding sample appointments...")
            appt1 = Appointment(title='Client Meeting - Alice Smith', start_time=datetime(2025, 10, 26, 10, 0), end_time=datetime(2025, 10, 26, 11, 0), location='Office Meeting Room', type='Consultation', status='Scheduled', notes='Discuss new property acquisition.', client_id=client1.id, case_id=case1.id, user_id=lawyer_user.id)
            appt2 = Appointment(title='Court Hearing - Johnson Case', start_time=datetime(2025, 11, 15, 9, 0), end_time=datetime(2025, 11, 15, 13, 0), location='District Court', type='Court Appearance', status='Scheduled', notes='First hearing on criminal fraud.', client_id=client2.id, case_id=case2.id, user_id=lawyer_user.id)
            db.session.add_all([appt1, appt2])
            db.session.commit()
        
        # Create sample time entries
        if TimeEntry.query.count() == 0:
            print("Adding sample time entries...")
            te1 = TimeEntry(date=datetime(2025, 10, 20).date(), hours=2.5, description='Research on property law for Smith v. Jones.', billable=True, rate=250.0, user_id=lawyer_user.id, case_id=case1.id, client_id=client1.id, status='Approved')
            te2 = TimeEntry(date=datetime(2025, 10, 21).date(), hours=1.0, description='Client call with Bob Johnson.', billable=True, rate=250.0, user_id=lawyer_user.id, case_id=case2.id, client_id=client2.id, status='Submitted')
            db.session.add_all([te1, te2])
            db.session.commit()
        
        # Create sample invoices
        if Invoice.query.count() == 0:
            print("Adding sample invoices...")
            inv1 = Invoice(invoice_number='INV1001', issue_date=datetime(2025, 11, 1).date(), due_date=datetime(2025, 11, 30).date(), amount=500.0, status='Sent', notes='Monthly retainer.', client_id=client1.id, case_id=case1.id)
            inv2 = Invoice(invoice_number='INV1002', issue_date=datetime(2025, 11, 5).date(), due_date=datetime(2025, 12, 5).date(), amount=750.0, status='Draft', notes='Legal services for October.', client_id=client2.id, case_id=case2.id)
            db.session.add_all([inv1, inv2])
            db.session.commit()

        # Add sample CaseLaw entries
        if CaseLaw.query.count() == 0:
            print("Adding sample CaseLaw entries...")
            caselaw1 = CaseLaw(
                title='Roe v. Wade',
                citation='410 U.S. 113 (1973)',
                year=1973,
                court='Supreme Court of the United States',
                jurisdiction='Federal',
                summary='Landmark decision by the United States Supreme Court establishing a woman\'s right to an abortion.',
                full_text='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
            )
            caselaw2 = CaseLaw(
                title='Miranda v. Arizona',
                citation='384 U.S. 436 (1966)',
                year=1966,
                court='Supreme Court of the United States',
                jurisdiction='Federal',
                summary='The Supreme Court ruled that detained criminal suspects, prior to custodial interrogation, must be read their constitutional right to an attorney and against self-incrimination.',
                full_text='Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.'
            )
            caselaw3 = CaseLaw(
                title='Brown v. Board of Education',
                citation='347 U.S. 483 (1954)',
                year=1954,
                court='Supreme Court of the United States',
                jurisdiction='Federal',
                summary='State-sanctioned segregation of public schools was a violation of the 14th Amendment and was therefore unconstitutional.',
                full_text='Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur?'
            )
            db.session.add_all([caselaw1, caselaw2, caselaw3])
            db.session.commit()
            print(f"Added {CaseLaw.query.count()} CaseLaw entries.")

if __name__ == '__main__':
    # Only run if called directly (not during flask db migrate/upgrade)
    if app.config['DEBUG']: # Or another config variable to control seeding
        create_sample_data()
        print("Sample data added/ensured.")

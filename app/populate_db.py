# app/populate_db.py
from app import app, db
from app.models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment
from datetime import datetime, timedelta

with app.app_context():
    db.drop_all()
    db.create_all()

    # ---- USERS ----
    admin = User(username="admin", email="admin@example.com", first_name="Admin", last_name="User", role="admin")
    admin.set_password("admin123")

    lawyer = User(username="lawyer1", email="lawyer1@example.com", first_name="John", last_name="Doe", role="lawyer", hourly_rate=200.0)
    lawyer.set_password("lawyer123")

    staff = User(username="staff1", email="staff1@example.com", first_name="Jane", last_name="Smith", role="staff")
    staff.set_password("staff123")

    db.session.add_all([admin, lawyer, staff])
    db.session.commit()

    # ---- CLIENTS ----
    client1 = Client(first_name="Michael", last_name="Johnson", email="michael@example.com", phone="9876543210",
                     address="123 Street, Mumbai", company="Johnson & Co", category="Corporate", notes="VIP client")
    client2 = Client(first_name="Priya", last_name="Sharma", email="priya@example.com", phone="9123456780",
                     address="456 Road, Delhi", company="Sharma Pvt Ltd", category="Individual", notes="Family case")

    db.session.add_all([client1, client2])
    db.session.commit()

    # ---- CASES ----
    case1 = Case(case_number="C-1001", title="Corporate Fraud Case", description="Case regarding corporate fraud",
                 status="Open", priority="High", practice_area="Corporate Law", case_type="Fraud",
                 budget=50000, client=client1)
    case2 = Case(case_number="C-1002", title="Divorce Settlement", description="Divorce settlement case",
                 status="In Progress", priority="Medium", practice_area="Family Law", case_type="Divorce",
                 budget=20000, client=client2)

    case1.assigned_users.append(lawyer)
    case2.assigned_users.append(lawyer)

    db.session.add_all([case1, case2])
    db.session.commit()

    # ---- APPOINTMENTS ----
    appt1 = Appointment(title="Court Hearing", start_time=datetime.utcnow(),
                        end_time=datetime.utcnow() + timedelta(hours=2), location="Mumbai Court",
                        type="Court Appearance", status="Scheduled", notes="Bring documents",
                        client=client1, case=case1, user_id=lawyer.id)

    db.session.add(appt1)
    db.session.commit()

    print("✅ Database populated with dummy data!")

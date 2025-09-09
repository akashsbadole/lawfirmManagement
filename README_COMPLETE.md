# 🏛️ Legal Management System - Complete Enterprise Solution

## 📋 **Overview**

A comprehensive, enterprise-ready legal practice management system built with Flask, featuring complete case management, client portal, billing, time tracking, document management, and multi-tenant cloud architecture.

## 🎯 **Two Deployment Options**

### 1. **Single-Tenant Version** (Current Directory)
- Perfect for individual law firms
- Simpler deployment and management
- All features included for one organization

### 2. **Multi-Tenant Version** (`legal-multi-tenant/`)
- SaaS-ready for multiple law firms
- Tenant isolation and management
- Subscription and billing support
- Scalable cloud architecture

## 🚀 **Quick Start**

### **Single-Tenant Setup**

```bash
# 1. Clone and setup
git clone <repository>
cd lawfirm-management

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
flask db upgrade

# 5. Setup initial data
python setup_initial_data.py

# 6. Run application
python run.py
```

### **Multi-Tenant Setup**

```bash
# 1. Navigate to multi-tenant version
cd legal-multi-tenant

# 2. Follow same setup steps as above
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
flask db upgrade
python setup_initial_data.py
python run.py
```

## 🔑 **Default Login Credentials**

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| **Admin** | `admin` | `admin123` | Full system access |
| **Lawyer** | `jdoe` | `lawyer123` | Case & client management |
| **Staff** | `msmith` | `staff123` | Support role, limited access |

> ⚠️ **IMPORTANT**: Change default passwords in production!

## 🎨 **Key Features**

### **📊 Enhanced Dashboard**
- Interactive charts and analytics
- Real-time statistics
- Financial metrics and trends
- Quick action buttons
- Task and appointment overview

### **👥 Advanced User Management**
- Role-based access control (Admin, Lawyer, Staff)
- 25+ granular permissions
- User activation/deactivation
- Comprehensive audit trails
- Session management

### **📁 Complete Case Management**
- Case lifecycle tracking
- Budget and time management
- Team assignments
- Document association
- Status workflows

### **🤝 Client Portal**
- Secure client access
- Document sharing
- Invoice viewing
- Appointment scheduling
- Communication tools

### **💰 Comprehensive Billing**
- Automated invoice generation
- Multiple payment methods
- Trust account management
- Payment tracking
- Overdue management

### **⏰ Time Tracking**
- Detailed time entries
- Billable vs non-billable hours
- Rate management
- Approval workflows
- Productivity analytics

### **📋 Task Management**
- Team collaboration
- Priority management
- Due date tracking
- Case-specific tasks
- Progress monitoring

### **🎫 Support System**
- Ticket management
- Internal notes
- Priority handling
- Assignment workflows
- Support analytics

### **🔍 Legal Search Engine**
- Multi-engine search (Google, Bing, DuckDuckGo)
- Indian legal database integration
- Citation extraction
- Search analytics
- Legal resource access

### **📧 Email Automation**
- Template system
- Automated notifications
- Appointment reminders
- Invoice notifications
- Communication logging

### **🔒 Enterprise Security**
- Data encryption
- Audit logging
- Role-based permissions
- Session management
- Backup system

## 🏗️ **Architecture**

### **Technology Stack**
- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: Bootstrap 5, Chart.js
- **Authentication**: Flask-Login
- **Migration**: Flask-Migrate
- **API**: RESTful endpoints

### **Database Schema**
- **Core Models**: User, Client, Case, Document, TimeEntry, Invoice
- **Extended Models**: Task, SupportTicket, EmailTemplate, AuditLog
- **Multi-tenant**: Tenant model with isolation
- **Security**: Encrypted sensitive data

## 🌐 **Multi-Tenant Features**

### **Tenant Management**
- Subdomain-based tenant identification
- Custom domain support
- Tenant isolation and security
- Subscription management
- Usage limits and quotas

### **Subscription Plans**
- **Basic**: 5 users, 100 cases, 1GB storage
- **Premium**: 25 users, 500 cases, 5GB storage
- **Enterprise**: Unlimited users, cases, 50GB storage

### **Tenant Features**
- Independent user management
- Separate configurations
- Tenant-specific analytics
- Data export capabilities
- Backup management

## 📱 **API Documentation**

### **Authentication**
```bash
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123"
}
```

### **Cases API**
```bash
GET /api/cases                    # List all cases
POST /api/cases                   # Create new case
GET /api/cases/{id}              # Get case details
PUT /api/cases/{id}              # Update case
DELETE /api/cases/{id}           # Delete case
```

### **Clients API**
```bash
GET /api/clients                 # List all clients
POST /api/clients                # Create new client
GET /api/clients/{id}           # Get client details
PUT /api/clients/{id}           # Update client
```

### **Time Tracking API**
```bash
GET /api/time-entries           # List time entries
POST /api/time-entries          # Create time entry
PUT /api/time-entries/{id}      # Update time entry
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
DATABASE_URL=sqlite:///lawfirm.db

# Security
SECRET_KEY=your-secret-key-here

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Search APIs
GOOGLE_SEARCH_API_KEY=your-google-api-key
GOOGLE_SEARCH_CX=your-custom-search-id
BING_SEARCH_API_KEY=your-bing-api-key

# File Upload
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads
```

### **System Settings**
Configurable via admin interface:
- Firm name and branding
- Default billing rates
- Invoice due periods
- File size limits
- Security policies

## 📊 **Analytics & Reporting**

### **Dashboard Metrics**
- Revenue trends and forecasting
- Case status distribution
- Practice area analytics
- User productivity metrics
- Client profitability analysis

### **Financial Reports**
- Revenue by period
- Outstanding invoices
- Payment history
- Trust account balances
- Expense tracking

### **Operational Reports**
- Case load analysis
- Time utilization
- Document statistics
- User activity logs
- System performance

## 🔐 **Security Features**

### **Data Protection**
- Password hashing (Werkzeug)
- Session management
- CSRF protection
- SQL injection prevention
- XSS protection

### **Access Control**
- Role-based permissions
- Resource-level security
- Audit trail logging
- Failed login tracking
- Session timeout

### **Compliance**
- Data retention policies
- Audit log maintenance
- Backup procedures
- Privacy controls
- GDPR compliance ready

## 🚀 **Deployment**

### **Development**
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
```

### **Production**
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app

# Using Docker
docker build -t legal-management .
docker run -p 8000:8000 legal-management

# Using systemd service
sudo systemctl start legal-management
sudo systemctl enable legal-management
```

### **Cloud Deployment**
- **AWS**: EC2, RDS, S3, CloudFront
- **Azure**: App Service, SQL Database, Blob Storage
- **GCP**: App Engine, Cloud SQL, Cloud Storage
- **Heroku**: Web dyno, Postgres addon

## 📚 **Documentation**

### **User Guides**
- [Admin Guide](docs/admin-guide.md)
- [Lawyer Guide](docs/lawyer-guide.md)
- [Staff Guide](docs/staff-guide.md)
- [Client Portal Guide](docs/client-guide.md)

### **Technical Documentation**
- [API Reference](docs/api-reference.md)
- [Database Schema](docs/database-schema.md)
- [Deployment Guide](docs/deployment.md)
- [Multi-tenant Setup](docs/multi-tenant.md)

## 🤝 **Contributing**

### **Development Setup**
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### **Code Standards**
- PEP 8 compliance
- Type hints where applicable
- Comprehensive docstrings
- Unit test coverage
- Security best practices

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

### **Getting Help**
- **Documentation**: Check the docs/ directory
- **Issues**: Create GitHub issue
- **Email**: support@legalmanagement.com
- **Community**: Join our Discord server

### **Professional Services**
- Custom development
- Enterprise deployment
- Training and support
- Data migration services

## 🎉 **Acknowledgments**

- Flask community for the excellent framework
- Bootstrap team for the UI components
- Chart.js for visualization capabilities
- All contributors and testers

---

## 📈 **Roadmap**

### **Version 2.0 (Planned)**
- [ ] Mobile applications (iOS/Android)
- [ ] Advanced AI features
- [ ] Blockchain document verification
- [ ] Advanced analytics and ML
- [ ] Video conferencing integration
- [ ] Advanced workflow automation

### **Version 1.5 (In Progress)**
- [x] Multi-tenant architecture
- [x] Enhanced dashboard
- [x] Support system
- [x] Task management
- [x] Email automation
- [ ] Two-factor authentication
- [ ] Advanced reporting
- [ ] API rate limiting

---

**🏛️ Legal Management System - Empowering Legal Professionals with Technology**

*Built with ❤️ for the legal community*
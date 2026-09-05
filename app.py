import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config, INTERNSHIP_FEES, INTERNSHIP_PRICING
from models import db, User, JobPosting, JobApplication, Payment
from routes import main_bp, auth_bp, contact_bp, admin_bp

csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure upload directories exist
    upload_resumes = app.config.get('UPLOAD_FOLDER_RESUMES', os.path.join(app.root_path, 'uploads', 'resumes'))
    upload_documents = app.config.get('UPLOAD_FOLDER_DOCUMENTS', os.path.join(app.root_path, 'uploads', 'documents'))
    os.makedirs(upload_resumes, exist_ok=True)
    os.makedirs(upload_documents, exist_ok=True)


    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Exempt Cashfree webhook endpoint from CSRF
    from routes.main import cashfree_webhook
    csrf.exempt(cashfree_webhook)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'


    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(admin_bp)

    # Global context processors for Jinja templates
    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.now().year,
            'app_name': 'Anti-Matrix'
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/404.html'), 500

    # Auto-initialize database tables and seed default data
    with app.app_context():
        db.create_all()

        # Ensure database schema is updated for user_id on job_applications
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'job_applications' in inspector.get_table_names():
                cols = [c['name'] for c in inspector.get_columns('job_applications')]
                if 'user_id' not in cols:
                    with db.engine.connect() as conn:
                        conn.execute(text('ALTER TABLE job_applications ADD COLUMN user_id INTEGER REFERENCES users(id)'))
                        try:
                            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_job_applications_user_id ON job_applications (user_id)'))
                        except Exception:
                            pass
                        conn.commit()
                
                # Auto-link existing applications where user email matches
                with db.engine.connect() as conn:
                    conn.execute(text('''
                        UPDATE job_applications
                        SET user_id = (
                            SELECT id FROM users WHERE LOWER(users.email) = LOWER(job_applications.email) LIMIT 1
                        )
                        WHERE user_id IS NULL AND EXISTS (
                            SELECT 1 FROM users WHERE LOWER(users.email) = LOWER(job_applications.email)
                        )
                    '''))
                    conn.commit()

            if 'employee_documents' in inspector.get_table_names():
                emp_doc_col_objs = inspector.get_columns('employee_documents')
                emp_doc_cols = [c['name'] for c in emp_doc_col_objs]
                emp_id_col = next((c for c in emp_doc_col_objs if c['name'] == 'employee_id'), None)

                # If employee_id is NOT NULL in SQLite table definition, migrate it non-destructively
                if emp_id_col and not emp_id_col.get('nullable', True):
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE IF NOT EXISTS employee_documents_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                application_id INTEGER REFERENCES job_applications(id) ON DELETE CASCADE,
                                employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
                                template_id INTEGER REFERENCES document_templates(id) ON DELETE SET NULL,
                                document_type VARCHAR(50) NOT NULL DEFAULT 'offer_letter',
                                file_name VARCHAR(255) NOT NULL,
                                file_path VARCHAR(500) NOT NULL,
                                status VARCHAR(30) NOT NULL DEFAULT 'GENERATED',
                                email_status VARCHAR(30) NOT NULL DEFAULT 'not_sent',
                                email_error TEXT,
                                generated_at DATETIME NOT NULL,
                                verified_at DATETIME,
                                sent_at DATETIME,
                                created_at DATETIME NOT NULL,
                                updated_at DATETIME NOT NULL
                            )
                        '''))
                        existing_cols = set(emp_doc_cols)
                        target_cols = [c for c in ['id', 'employee_id', 'document_type', 'file_name', 'file_path', 'status', 'email_status', 'email_error', 'generated_at', 'verified_at', 'sent_at', 'created_at', 'updated_at', 'template_id', 'application_id'] if c in existing_cols]
                        cols_str = ', '.join(target_cols)
                        conn.execute(text(f'INSERT INTO employee_documents_new ({cols_str}) SELECT {cols_str} FROM employee_documents'))
                        conn.execute(text('DROP TABLE employee_documents'))
                        conn.execute(text('ALTER TABLE employee_documents_new RENAME TO employee_documents'))
                        try:
                            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_employee_documents_application_id ON employee_documents (application_id)'))
                            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_employee_documents_employee_id ON employee_documents (employee_id)'))
                        except Exception:
                            pass
                        conn.commit()
                else:
                    if 'template_id' not in emp_doc_cols:
                        with db.engine.connect() as conn:
                            conn.execute(text('ALTER TABLE employee_documents ADD COLUMN template_id INTEGER REFERENCES document_templates(id)'))
                            conn.commit()
                    if 'application_id' not in emp_doc_cols:
                        with db.engine.connect() as conn:
                            conn.execute(text('ALTER TABLE employee_documents ADD COLUMN application_id INTEGER REFERENCES job_applications(id)'))
                            try:
                                conn.execute(text('CREATE INDEX IF NOT EXISTS ix_employee_documents_application_id ON employee_documents (application_id)'))
                            except Exception:
                                pass
                            conn.commit()

                # Backfill application_id for existing employee_documents from employees table
                with db.engine.connect() as conn:
                    conn.execute(text('''
                        UPDATE employee_documents
                        SET application_id = (
                            SELECT application_id FROM employees WHERE employees.id = employee_documents.employee_id LIMIT 1
                        )
                        WHERE application_id IS NULL AND employee_id IS NOT NULL
                    '''))
                    conn.commit()
        except Exception as e:
            app.logger.warning(f"Database auto-migration note: {str(e)}")

        # Seed default admin user if none exists
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            default_admin = User(
                name='Anti-Matrix Admin',
                email=os.environ.get('ADMIN_EMAIL', 'admin@antimatrix.ai'),
                role='admin',
                is_active=True
            )
            default_admin.set_password(os.environ.get('ADMIN_PASSWORD', 'Admin@AntiMatrix2026!'))
            db.session.add(default_admin)
            db.session.commit()

        # Seed default initial jobs if empty
        if JobPosting.query.count() == 0:
            initial_jobs = [
                JobPosting(
                    title='Senior Full-Stack Engineer',
                    department='Engineering',
                    location='Remote (Worldwide)',
                    employment_type='Full-time',
                    skills='React, Node.js, PostgreSQL, AWS, TypeScript',
                    short_description='Lead the development of complex web applications for our enterprise clients, collaborating with product and design.',
                    description='We are looking for a senior full-stack engineer to lead the development of complex web applications for our enterprise clients. You will work closely with product, design, and client teams to design resilient architectures and deliver clean code.',
                    requirements='5+ years of full-stack development experience\nStrong React and Node.js expertise\nExperience with cloud services (AWS/GCP)\nExcellent technical communication and mentoring skills',
                    responsibilities='Architect scalable web frontend and backend systems\nCollaborate directly with clients and cross-functional teams\nConduct code reviews and mentor junior developers',
                    salary='$120k - $160k',
                    is_active=True
                ),
                JobPosting(
                    title='Machine Learning Engineer',
                    department='AI & Data',
                    location='Remote (US/EU)',
                    employment_type='Full-time',
                    skills='Python, PyTorch, MLOps, FastAPI, HuggingFace',
                    short_description='Join our AI team to design and deploy production machine learning systems, LLM pipelines, and predictive analytics.',
                    description='Join our AI team to design and deploy production machine learning systems. You will work on NLP, computer vision, and predictive analytics projects for our high-growth clients.',
                    requirements='3+ years ML engineering experience\nProficiency in Python and PyTorch or TensorFlow\nExperience with model deployment, Docker, and MLOps\nBackground in LLM orchestration or NLP is a strong plus',
                    responsibilities='Build and fine-tune machine learning and deep learning models\nDeploy scalable model inference APIs with FastAPI and Docker\nMonitor model performance and optimize latency',
                    salary='$130k - $170k',
                    is_active=True
                ),
                JobPosting(
                    title='UI/UX Designer',
                    department='Design',
                    location='Remote (Worldwide)',
                    employment_type='Full-time',
                    skills='Figma, User Research, Prototyping, Design Systems',
                    short_description='Craft intuitive, beautiful experiences and robust design systems for our web and mobile products.',
                    description='We need a talented UI/UX designer to craft intuitive, beautiful experiences for our web and mobile products. You will own design from research and wireframing through to high-fidelity delivery.',
                    requirements='3+ years UI/UX design experience\nExpert-level Figma and prototyping skills\nStrong portfolio of shipped digital products\nDeep understanding of design systems and typography',
                    responsibilities='Lead user research and create user personas and journey maps\nDesign responsive UI components and interactive prototypes\nWork closely with frontend engineers during implementation',
                    salary='$90k - $125k',
                    is_active=True
                ),
                JobPosting(
                    title='React Native Developer',
                    department='Mobile',
                    location='Remote (Worldwide)',
                    employment_type='Full-time',
                    skills='React Native, TypeScript, iOS, Android, Redux',
                    short_description='Build high-performance, cross-platform mobile applications for iOS and Android enterprise clients.',
                    description='Build high-performance, cross-platform mobile applications for iOS and Android. You will work on projects ranging from consumer apps to enterprise mobile solutions.',
                    requirements='3+ years React Native development experience\nPublished apps on App Store and Google Play\nStrong TypeScript and state management skills\nFamiliarity with native iOS or Android bridging',
                    responsibilities='Develop performant React Native mobile apps for iOS and Android\nIntegrate third-party SDKs and REST/GraphQL APIs\nOptimize mobile app performance and battery efficiency',
                    salary='$105k - $145k',
                    is_active=True
                ),
                JobPosting(
                    title='DevOps / Cloud Engineer',
                    department='Infrastructure',
                    location='Remote (US/EU)',
                    employment_type='Full-time',
                    skills='AWS, Kubernetes, Terraform, CI/CD, Docker',
                    short_description='Design and manage resilient cloud infrastructure and automated deployment pipelines.',
                    description='Design and manage the cloud infrastructure that powers our clients\' digital products. You will build automated pipelines, ensure security and reliability, and reduce operational overhead.',
                    requirements='4+ years DevOps and SRE experience\nAWS or GCP certification preferred\nHands-on Kubernetes and Terraform experience\nStrong security and compliance mindset',
                    responsibilities='Provision and manage cloud infrastructure using Terraform\nBuild and maintain CI/CD pipelines with GitHub Actions / GitLab\nImplement comprehensive monitoring and incident response tools',
                    salary='$125k - $165k',
                    is_active=True
                ),
                JobPosting(
                    title='Digital Marketing Specialist',
                    department='Marketing',
                    location='Remote (Worldwide)',
                    employment_type='Full-time',
                    skills='SEO, Google Ads, GA4, Content Strategy, Meta Ads',
                    short_description='Drive measurable growth for Anti-Matrix clients through data-backed digital marketing strategies.',
                    description='Drive measurable growth for Anti-Matrix clients through data-backed digital marketing strategies. You will manage campaigns, optimize performance, and report on ROI.',
                    requirements='3+ years digital marketing experience\nGoogle Ads and Meta Ads certification\nStrong analytical skills (GA4, Looker Studio, SEMrush)\nExcellent English copywriting skills',
                    responsibilities='Develop and execute multi-channel digital marketing campaigns\nOptimize SEO and performance marketing funnels\nProduce insightful analytics reports and client presentations',
                    salary='$80k - $110k',
                    is_active=True
                )
            ]
            db.session.add_all(initial_jobs)
            db.session.commit()

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
from models import db, User, JobPosting, JobApplication
from routes import main_bp, auth_bp, contact_bp, admin_bp

csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'uploads', 'resumes')), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

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

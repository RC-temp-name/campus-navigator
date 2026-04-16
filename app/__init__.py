from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-secret-change-in-prod"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///minimap.db"

    # Initialize extensions
    from app.models import db, User, register_user_loader
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    register_user_loader(login_manager)

    # Register blueprints
    from app import events
    app.register_blueprint(events.bp)
    from app import auth
    app.register_blueprint(auth.bp)

    with app.app_context():
        db.create_all()

    @app.cli.command("create-user")
    def create_user():
        """Create the first user (run with: uv run python -m flask --app run create-user)."""
        from werkzeug.security import generate_password_hash
        import getpass
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        if User.query.filter_by(email=email).first():
            print(f"User {email} already exists.")
            return
        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        print(f"User {email} created.")

    return app

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Create a minimal Flask app
app = Flask(__name__)

# Ensure data directory exists
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Created data directory at {data_dir}")

# Configure database
db_path = os.path.join(data_dir, 'stripe.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define minimal AdminUser model
class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

def setup_database():
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Created database tables")
        
        # Create admin user if it doesn't exist
        admin = AdminUser.query.filter_by(email='admin@audiosnipt.com').first()
        if not admin:
            admin = AdminUser(
                email='admin@audiosnipt.com',
                password_hash=generate_password_hash('AudioSnipt2024!')
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user with default credentials")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    try:
        setup_database()
        print("\nDatabase setup completed successfully!")
        print("\nYou can now log in with:")
        print("Email: admin@audiosnipt.com")
        print("Password: AudioSnipt2024!")
    except Exception as e:
        print(f"\nError during database setup: {str(e)}", file=sys.stderr)
        sys.exit(1) 
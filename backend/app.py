from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
import os

# Import models and routes
from models import db, init_sample_data, Admin
from routes import api

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'  # Change this in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # For development, tokens don't expire
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "parking_system.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    api.init_app(app)
    
    return app

app = create_app()

@app.route('/')
def home():
    return {
        'message': 'Vehicle Parking System API', 
        'status': 'running',
        'version': '1.0.0'
    }

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'database': 'connected'}

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        
        # Initialize sample data
        print("Initializing sample data...")
        init_sample_data()
        
        print("Database setup completed successfully!")
        print("=" * 50)
        print("Admin Login Credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("=" * 50)
        
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)

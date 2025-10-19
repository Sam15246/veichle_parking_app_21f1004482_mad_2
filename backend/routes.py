from flask_restful import Api, Resource
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, ParkingLot, ParkingSpot, Reservation, SpotStatus, ReservationStatus
from datetime import datetime

api = Api()

class HelloWorld(Resource):
    def get(self):
        return {'message': 'Vehicle Parking System API v1.0'}, 200

api.add_resource(HelloWorld, '/')

# Authentication Routes
class UserRegister(Resource):
    def post(self):
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if not data or field not in data or not data[field]:
                return {'message': f'{field} is required'}, 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return {'message': 'Username already exists'}, 400
            
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already exists'}, 400
        
        # Create new user (only regular users can register)
        try:
            new_user = User(
                username=data['username'],
                email=data['email'],
                password=data['password'],  # In production, hash this
                full_name=data['full_name'],
                phone=data.get('phone'),
                address=data.get('address'),
                pin_code=data.get('pin_code'),
                role='user'  # Force role to be 'user' - no admin registration
            )
            db.session.add(new_user)
            db.session.commit()
            
            return {
                'message': 'User registered successfully',
                'user_id': new_user.id
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'message': 'Registration failed', 'error': str(e)}, 500

api.add_resource(UserRegister, '/api/register')

class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return {'message': 'Username and password required'}, 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or user.password != data['password']:  # In production, use proper password hashing
            return {'message': 'Invalid credentials'}, 401
        
        # Create access token
        token = create_access_token(identity=user.username)
        
        return {
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role
            }
        }, 200

api.add_resource(UserLogin, '/api/login')

# Admin-only Login (separate endpoint for clarity)
class AdminLogin(Resource):
    def post(self):
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return {'message': 'Username and password required'}, 400
        
        user = User.query.filter_by(username=data['username'], role='admin').first()
        
        if not user or user.password != data['password']:
            return {'message': 'Invalid admin credentials'}, 401
        
        # Create access token
        token = create_access_token(identity=user.username)
        
        return {
            'message': 'Admin login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role
            }
        }, 200

api.add_resource(AdminLogin, '/api/admin/login')

# Protected Routes
class UserProfile(Resource):
    @jwt_required()
    def get(self):
        """Get current user profile"""
        try:
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            
            if not current_user:
                return {'message': 'User not found'}, 404
            
            return {
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'full_name': current_user.full_name,
                    'phone': current_user.phone,
                    'address': current_user.address,
                    'pin_code': current_user.pin_code,
                    'role': current_user.role,
                    'created_at': current_user.created_at.isoformat()
                }
            }, 200
            
        except Exception as e:
            return {'message': 'Failed to get user profile', 'error': str(e)}, 500

api.add_resource(UserProfile, '/api/profile')

class AdminDashboard(Resource):
    @jwt_required()
    def get(self):
        """Admin dashboard data"""
        try:
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            
            if not current_user or current_user.role != 'admin':
                return {'message': 'Admin access required'}, 403
            
            # Get dashboard statistics
            total_users = User.query.filter_by(role='user').count()
            total_lots = ParkingLot.query.count()
            total_spots = ParkingSpot.query.count()
            active_reservations = Reservation.query.filter_by(status=ReservationStatus.ACTIVE.value).count()
            
            return {
                'message': 'Admin dashboard data',
                'statistics': {
                    'total_users': total_users,
                    'total_parking_lots': total_lots,
                    'total_parking_spots': total_spots,
                    'active_reservations': active_reservations
                }
            }, 200
            
        except Exception as e:
            return {'message': 'Failed to get admin dashboard data', 'error': str(e)}, 500

api.add_resource(AdminDashboard, '/api/admin/dashboard')

class UserDashboard(Resource):
    @jwt_required()
    def get(self):
        """User dashboard data"""
        try:
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            
            if not current_user:
                return {'message': 'User not found'}, 404
                
            if current_user.role != 'user':
                return {'message': 'User access required'}, 403
            
            # Get user's reservations
            user_reservations = len(current_user.reservations)
            active_reservations = len([r for r in current_user.reservations if r.status == ReservationStatus.ACTIVE.value])
            
            return {
                'message': 'User dashboard data',
                'user_data': {
                    'total_reservations': user_reservations,
                    'active_reservations': active_reservations,
                    'available_lots': ParkingLot.query.count()
                }
            }, 200
            
        except Exception as e:
            return {'message': 'Failed to get user dashboard data', 'error': str(e)}, 500

api.add_resource(UserDashboard, '/api/user/dashboard')

# Public Routes
class ParkingLotsPublic(Resource):
    def get(self):
        """Get all parking lots (public access)"""
        try:
            lots = ParkingLot.query.all()
            lots_data = []
            
            for lot in lots:
                lots_data.append({
                    'id': lot.id,
                    'prime_location_name': lot.prime_location_name,
                    'address': lot.address,
                    'pin_code': lot.pin_code,
                    'price_per_hour': lot.price_per_hour,
                    'maximum_spots': lot.maximum_spots,
                    'available_spots': lot.available_spots_count,
                    'occupied_spots': lot.occupied_spots_count
                })
            
            return {
                'message': 'Parking lots retrieved successfully',
                'data': lots_data
            }, 200
            
        except Exception as e:
            return {
                'message': 'Failed to retrieve parking lots',
                'error': str(e)
            }, 500

api.add_resource(ParkingLotsPublic, '/api/parking-lots')

# Database Test Route
class DatabaseTest(Resource):
    def get(self):
        try:
            # Test database connection
            users_count = User.query.count()
            lots_count = ParkingLot.query.count()
            spots_count = ParkingSpot.query.count()
            reservations_count = Reservation.query.count()
            
            return {
                'message': 'Database connection successful',
                'statistics': {
                    'users': users_count,
                    'parking_lots': lots_count,
                    'parking_spots': spots_count,
                    'reservations': reservations_count
                }
            }, 200
            
        except Exception as e:
            return {
                'message': 'Database connection failed',
                'error': str(e)
            }, 500

api.add_resource(DatabaseTest, '/api/database/test')

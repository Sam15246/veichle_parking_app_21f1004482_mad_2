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
        
        # Create new user
        try:
            new_user = User(
                username=data['username'],
                email=data['email'],
                password=data['password'],  # In production, hash this
                full_name=data['full_name'],
                phone=data.get('phone'),
                address=data.get('address'),
                pin_code=data.get('pin_code')
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

# Parking Lots API
class ParkingLotsAPI(Resource):
    def get(self):
        """Get all parking lots with availability info"""
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
                    'occupied_spots': lot.occupied_spots_count,
                    'created_at': lot.created_at.isoformat()
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

    @jwt_required()
    def post(self):
        """Create new parking lot (Admin only)"""
        try:
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            
            if not current_user or current_user.role != 'admin':
                return {'message': 'Admin access required'}, 403
            
            data = request.get_json()
            required_fields = ['prime_location_name', 'address', 'pin_code', 'maximum_spots']
            
            for field in required_fields:
                if not data or field not in data or not data[field]:
                    return {'message': f'{field} is required'}, 400
            
            # Check if location already exists
            if ParkingLot.query.filter_by(prime_location_name=data['prime_location_name']).first():
                return {'message': 'Parking lot with this location name already exists'}, 400
            
            new_lot = ParkingLot(
                prime_location_name=data['prime_location_name'],
                address=data['address'],
                pin_code=data['pin_code'],
                price_per_hour=data.get('price_per_hour', 20.0),
                maximum_spots=data['maximum_spots']
            )
            
            db.session.add(new_lot)
            db.session.commit()
            
            # Create parking spots for this lot
            from models import create_parking_spots_for_lot
            create_parking_spots_for_lot(new_lot.id, new_lot.maximum_spots)
            
            return {
                'message': 'Parking lot created successfully',
                'lot_id': new_lot.id
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'message': 'Failed to create parking lot', 'error': str(e)}, 500

api.add_resource(ParkingLotsAPI, '/api/parking-lots')

# Users API (Admin only)
class UsersAPI(Resource):
    @jwt_required()
    def get(self):
        """Get all users (Admin only)"""
        try:
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            
            if not current_user or current_user.role != 'admin':
                return {'message': 'Admin access required'}, 403
            
            users = User.query.all()
            users_data = []
            
            for user in users:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'phone': user.phone,
                    'role': user.role,
                    'created_at': user.created_at.isoformat(),
                    'total_reservations': len(user.reservations)
                })
            
            return {
                'message': 'Users retrieved successfully',
                'data': users_data
            }, 200
            
        except Exception as e:
            return {
                'message': 'Failed to retrieve users',
                'error': str(e)
            }, 500

api.add_resource(UsersAPI, '/api/users')

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

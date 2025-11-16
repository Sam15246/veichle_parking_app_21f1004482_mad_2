from flask_restful import Api, Resource
from flask import request, jsonify, current_app, send_file
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, ParkingLot, ParkingSpot, Reservation, SpotStatus, ReservationStatus, ExportJob
from models import create_parking_spots_for_lot  # helper for initial spot generation
from string import ascii_uppercase
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
import json, os

api = Api()

# Caching helpers
def cache_get(key):
    r = getattr(current_app, 'redis', None)
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None

def cache_set(key, data, ttl):
    r = getattr(current_app, 'redis', None)
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(data))
    except Exception:
        pass

def cache_delete(*keys):
    r = getattr(current_app, 'redis', None)
    if not r or not keys:
        return
    try:
        r.delete(*keys)
    except Exception:
        pass

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
                password=generate_password_hash(data['password']),  # hash password
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
        
        # Enforce user-only login here (admins must use /api/admin/login)
        user = User.query.filter_by(username=data['username'], role='user').first()
        if not user or not check_password_hash(user.password, data['password']):  # verify hash
            return {
                'message': 'Invalid credentials for user login. If you are admin, use /api/admin/login'
            }, 401
        
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
        
        if not user or not check_password_hash(user.password, data['password']):  # verify hash
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

# ------------------------ Public Routes (cached) ------------------------
class ParkingLotsPublic(Resource):
    def get(self):
        cache_key = 'parking_lots_public'
        cached = cache_get(cache_key)
        if cached:
            return cached, 200
        try:
            lots = ParkingLot.query.all()
            lots_data = [{
                'id': lot.id,
                'prime_location_name': lot.prime_location_name,
                'address': lot.address,
                'pin_code': lot.pin_code,
                'price_per_hour': lot.price_per_hour,
                'maximum_spots': lot.maximum_spots,
                'available_spots': lot.available_spots_count,
                'occupied_spots': lot.occupied_spots_count
            } for lot in lots]
            response = {
                'message': 'Parking lots retrieved successfully',
                'data': lots_data
            }
            cache_set(cache_key, response, current_app.config['LOTS_CACHE_TTL'])
            return response, 200
        except Exception as e:
            return {'message': 'Failed to retrieve parking lots', 'error': str(e)}, 500

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

# ------------------------ Admin: Parking Lots CRUD (invalidate cache) ------------------------

class AdminLotsAPI(Resource):
    @jwt_required()
    def get(self):
        cache_key = 'admin_lots_list'
        cached = cache_get(cache_key)
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403
        if cached:
            return cached, 200
        lots = ParkingLot.query.all()
        data = []
        for lot in lots:
            data.append({
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
        response = {'message': 'Lots fetched', 'data': data}
        cache_set(cache_key, response, current_app.config['LOTS_CACHE_TTL'])
        return response, 200

    @jwt_required()
    def post(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403

        data = request.get_json() or {}
        required = ['prime_location_name', 'address', 'pin_code', 'maximum_spots']
        for f in required:
            if not data.get(f):
                return {'message': f'{f} is required'}, 400

        if ParkingLot.query.filter_by(prime_location_name=data['prime_location_name']).first():
            return {'message': 'Parking lot name must be unique'}, 400

        try:
            lot = ParkingLot(
                prime_location_name=data['prime_location_name'],
                address=data['address'],
                pin_code=data['pin_code'],
                price_per_hour=float(data.get('price_per_hour', 20.0)),
                maximum_spots=int(data['maximum_spots'])
            )
            db.session.add(lot); db.session.commit()

            # Auto-create spots to match capacity
            create_parking_spots_for_lot(lot.id, lot.maximum_spots)

            cache_delete('parking_lots_public', 'admin_lots_list', 'admin_analytics_overview')
            return {'message': 'Lot created', 'id': lot.id}, 201
        except Exception as e:
            db.session.rollback()
            return {'message': 'Failed to create lot', 'error': str(e)}, 500

api.add_resource(AdminLotsAPI, '/api/admin/lots')

class AdminLotDetailAPI(Resource):
    @jwt_required()
    def put(self, lot_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403

        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {'message': 'Lot not found'}, 404

        data = request.get_json() or {}
        try:
            # Rename with uniqueness
            if 'prime_location_name' in data and data['prime_location_name']:
                existing = ParkingLot.query.filter_by(prime_location_name=data['prime_location_name']).first()
                if existing and existing.id != lot.id:
                    return {'message': 'Parking lot name must be unique'}, 400
                lot.prime_location_name = data['prime_location_name']

            if 'address' in data and data['address'] is not None:
                lot.address = data['address']
            if 'pin_code' in data and data['pin_code'] is not None:
                lot.pin_code = data['pin_code']
            if 'price_per_hour' in data and data['price_per_hour'] is not None:
                lot.price_per_hour = float(data['price_per_hour'])

            # Capacity rules: only allow increase. Append new spots, do not remove existing.
            if 'maximum_spots' in data and data['maximum_spots'] is not None:
                new_max = int(data['maximum_spots'])
                current_count = len(lot.parking_spots)

                if new_max < current_count:
                    return {'message': 'Reducing capacity below existing spots is not allowed'}, 400

                if new_max > current_count:
                    to_create = new_max - current_count
                    created = 0
                    for letter in ascii_uppercase:
                        if created >= to_create: break
                        for number in range(1, 1000):  # safe upper bound
                            if created >= to_create: break
                            spot_number = f'{letter}{number}'
                            exists = ParkingSpot.query.filter_by(lot_id=lot.id, spot_number=spot_number).first()
                            if exists:
                                continue
                            db.session.add(ParkingSpot(
                                lot_id=lot.id,
                                spot_number=spot_number,
                                status=SpotStatus.AVAILABLE.value
                            ))
                            created += 1
                    lot.maximum_spots = new_max

            db.session.commit()
            cache_delete('parking_lots_public', 'admin_lots_list', 'admin_analytics_overview')
            return {'message': 'Lot updated'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': 'Failed to update lot', 'error': str(e)}, 500

    @jwt_required()
    def delete(self, lot_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403

        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {'message': 'Lot not found'}, 404

        # Block delete if any spot occupied
        any_occupied = any(s.status == SpotStatus.OCCUPIED.value for s in lot.parking_spots)
        if any_occupied:
            return {'message': 'Cannot delete lot with occupied spots'}, 400

        # Block delete if any reservations exist for this lot (any status)
        any_res = db.session.query(Reservation).join(ParkingSpot, Reservation.spot_id == ParkingSpot.id)\
            .filter(ParkingSpot.lot_id == lot_id).first()
        if any_res:
            return {'message': 'Cannot delete lot with existing reservations'}, 400

        try:
            db.session.delete(lot)
            db.session.commit()
            cache_delete('parking_lots_public', 'admin_lots_list', 'admin_analytics_overview')
            return {'message': 'Lot deleted'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': 'Failed to delete lot', 'error': str(e)}, 500

api.add_resource(AdminLotDetailAPI, '/api/admin/lots/<int:lot_id>')

class AdminLotSpotsAPI(Resource):
    @jwt_required()
    def get(self, lot_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403

        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {'message': 'Lot not found'}, 404

        spots = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(ParkingSpot.spot_number.asc()).all()
        data = [{
            'id': s.id,
            'spot_number': s.spot_number,
            'status': s.status
        } for s in spots]

        return {
            'message': 'Spots fetched',
            'lot': {
                'id': lot.id,
                'prime_location_name': lot.prime_location_name,
                'available_spots': lot.available_spots_count,
                'occupied_spots': lot.occupied_spots_count,
                'maximum_spots': lot.maximum_spots
            },
            'data': data
        }, 200

api.add_resource(AdminLotSpotsAPI, '/api/admin/lots/<int:lot_id>/spots')

# ------------------------ Admin: Users List ------------------------
class AdminUsersAPI(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403

        users = User.query.all()
        data = []
        for u in users:
            active_list = Reservation.query.filter_by(
                user_id=u.id,
                status=ReservationStatus.ACTIVE.value
            ).all()
            spots = [r.parking_spot.spot_number for r in active_list if r.parking_spot]
            lots = [r.parking_spot.parking_lot.prime_location_name for r in active_list if r.parking_spot]
            data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'full_name': u.full_name,
                'role': u.role,
                'active_reservations_count': len(active_list),
                'active_spots': spots,
                'active_lots': lots
            })
        return {'message': 'Users fetched', 'data': data}, 200

api.add_resource(AdminUsersAPI, '/api/admin/users')

# ------------------------ User Reservations: Create/Release/Fetch ------------------------

class CreateReservation(Resource):
    @jwt_required()
    def post(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user:
            return {'message': 'User not found'}, 404
        data = request.get_json() or {}
        lot_id = data.get('lot_id')
        vehicle_number = data.get('vehicle_number')
        if not lot_id or not vehicle_number:
            return {'message': 'lot_id and vehicle_number are required'}, 400

        # NEW: enforce configurable max active reservations instead of single reservation
        active_count = Reservation.query.filter_by(
            user_id=current_user.id,
            status=ReservationStatus.ACTIVE.value
        ).count()
        limit = current_app.config.get('MAX_ACTIVE_RESERVATIONS_PER_USER', 5)
        if active_count >= limit:
            return {'message': f'Max active reservations ({limit}) reached'}, 400

        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {'message': 'Parking lot not found'}, 404

        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status=SpotStatus.AVAILABLE.value)\
                                .order_by(ParkingSpot.spot_number.asc()).first()
        if not spot:
            return {'message': 'No available spots in this lot'}, 409

        try:
            spot.status = SpotStatus.OCCUPIED.value
            res = Reservation(
                user_id=current_user.id,
                spot_id=spot.id,
                vehicle_number=vehicle_number,
                status=ReservationStatus.ACTIVE.value,
                estimated_cost=lot.price_per_hour  # first hour minimum charge
            )
            db.session.add(res); db.session.commit()
            cache_delete('parking_lots_public', 'admin_lots_list', 'admin_analytics_overview',
                         f'user_analytics_overview:{current_user.username}')
            return {
                'message': 'Reservation created',
                'reservation': {
                    'id': res.id,
                    'vehicle_number': res.vehicle_number,
                    'status': res.status,
                    'parking_timestamp': res.parking_timestamp.isoformat(),
                    'billed_hours': res.billed_hours,
                    'estimated_first_hour_cost': lot.price_per_hour,
                    'spot': {'id': spot.id, 'spot_number': spot.spot_number},
                    'lot': {'id': lot.id, 'name': lot.prime_location_name, 'price_per_hour': lot.price_per_hour}
                }
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'message': 'Failed to create reservation', 'error': str(e)}, 500

api.add_resource(CreateReservation, '/api/reservations')

class ReleaseReservation(Resource):
    @jwt_required()
    def post(self, reservation_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user:
            return {'message': 'User not found'}, 404

        res = Reservation.query.get(reservation_id)
        if not res:
            return {'message': 'Reservation not found'}, 404

        # Only owner or admin can release
        if res.user_id != current_user.id and current_user.role != 'admin':
            return {'message': 'Not authorized to release this reservation'}, 403

        if res.status != ReservationStatus.ACTIVE.value:
            return {'message': 'Reservation already completed or cancelled'}, 400

        try:
            res.complete_reservation()
            db.session.commit()
            cache_delete('parking_lots_public', 'admin_lots_list', 'admin_analytics_overview',
                         f'user_analytics_overview:{res.user.username}')
            return {
                'message': 'Reservation released',
                'reservation': {
                    'id': res.id,
                    'status': res.status,
                    'leaving_timestamp': res.leaving_timestamp.isoformat(),
                    'billed_hours': res.billed_hours,
                    'final_cost': res.final_cost
                }
            }, 200
        except Exception as e:
            db.session.rollback()
            return {'message': 'Failed to release reservation', 'error': str(e)}, 500

api.add_resource(ReleaseReservation, '/api/reservations/<int:reservation_id>/release')

# REPLACED: ActiveReservation -> ActiveReservations (returns list)
class ActiveReservations(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user:
            return {'message': 'User not found'}, 404
        active_list = Reservation.query.filter_by(
            user_id=current_user.id,
            status=ReservationStatus.ACTIVE.value
        ).order_by(Reservation.parking_timestamp.asc()).all()

        def serialize(r: Reservation):
            spot = r.parking_spot
            lot = spot.parking_lot
            return {
                'id': r.id,
                'vehicle_number': r.vehicle_number,
                'status': r.status,
                'parking_timestamp': r.parking_timestamp.isoformat(),
                'duration_hours': r.duration_hours,
                'billed_hours': r.billed_hours,
                'calculated_cost': r.calculated_cost,
                'spot': {'id': spot.id, 'spot_number': spot.spot_number},
                'lot': {'id': lot.id, 'name': lot.prime_location_name, 'price_per_hour': lot.price_per_hour}
            }

        return {
            'message': 'Active reservations fetched',
            'reservations': [serialize(r) for r in active_list]
        }, 200

# Update resource registration (same endpoint path)
api.add_resource(ActiveReservations, '/api/user/reservations/active')

class UserReservations(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user:
            return {'message': 'User not found'}, 404

        res_list = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.created_at.desc()).all()

        def serialize(r: Reservation):
            spot = r.parking_spot
            lot = spot.parking_lot if spot else None
            return {
                'id': r.id,
                'vehicle_number': r.vehicle_number,
                'status': r.status,
                'parking_timestamp': r.parking_timestamp.isoformat() if r.parking_timestamp else None,
                'leaving_timestamp': r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
                'duration_hours': r.duration_hours,
                'billed_hours': r.billed_hours,
                'final_cost': r.final_cost,
                'calculated_cost': r.calculated_cost,
                'spot': {'id': spot.id, 'spot_number': spot.spot_number} if spot else None,
                'lot': {'id': lot.id, 'name': lot.prime_location_name, 'price_per_hour': lot.price_per_hour} if lot else None
            }

        return {'message': 'Reservations fetched', 'data': [serialize(r) for r in res_list]}, 200

api.add_resource(UserReservations, '/api/user/reservations')

# ------------------------ Admin: Reservations List (History) ------------------------
class AdminReservationsAPI(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403

        # Optional filters: status, user_id, lot_id
        status = request.args.get('status')
        user_id = request.args.get('user_id', type=int)
        lot_id = request.args.get('lot_id', type=int)

        q = Reservation.query
        if status:
            q = q.filter(Reservation.status == status)
        if user_id:
            q = q.filter(Reservation.user_id == user_id)
        if lot_id:
            # join via ParkingSpot to lot
            q = q.join(ParkingSpot, Reservation.spot_id == ParkingSpot.id).filter(ParkingSpot.lot_id == lot_id)

        q = q.order_by(Reservation.created_at.desc())
        reservations = q.all()

        def serialize(r: Reservation):
            spot = r.parking_spot
            lot = spot.parking_lot if spot else None
            user = r.user
            return {
                'id': r.id,
                'user': {'id': user.id, 'username': user.username, 'full_name': user.full_name} if user else None,
                'lot': {'id': lot.id, 'name': lot.prime_location_name, 'price_per_hour': lot.price_per_hour} if lot else None,
                'spot': {'id': spot.id, 'spot_number': spot.spot_number} if spot else None,
                'vehicle_number': r.vehicle_number,
                'status': r.status,
                'parking_timestamp': r.parking_timestamp.isoformat() if r.parking_timestamp else None,
                'leaving_timestamp': r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
                'duration_hours': r.duration_hours,
                'billed_hours': r.billed_hours,
                'estimated_cost': r.estimated_cost,
                'calculated_cost': r.calculated_cost,
                'final_cost': r.final_cost,
            }

        return {'message': 'Reservations fetched', 'data': [serialize(r) for r in reservations]}, 200

api.add_resource(AdminReservationsAPI, '/api/admin/reservations')

# ------------------------ Admin Analytics (cached) ------------------------
class AdminAnalytics(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403
        cache_key = 'admin_analytics_overview'
        cached = cache_get(cache_key)
        if cached:
            return cached, 200
        # ...existing analytics computation (reuse previous logic)...
        lots = ParkingLot.query.all()
        lot_names, occupancy_percent, revenue_values, active_counts, completed_counts = [], [], [], [], []
        for lot in lots:
            lot_names.append(lot.prime_location_name)
            occ = round((lot.occupied_spots_count / lot.maximum_spots) * 100, 2) if lot.maximum_spots else 0.0
            occupancy_percent.append(occ)
            completed_rev = db.session.query(func.coalesce(func.sum(Reservation.final_cost), 0.0)) \
                .join(ParkingSpot, Reservation.spot_id == ParkingSpot.id) \
                .filter(ParkingSpot.lot_id == lot.id,
                        Reservation.status == ReservationStatus.COMPLETED.value).scalar()
            revenue_values.append(float(completed_rev))
            active_count = db.session.query(func.count(Reservation.id)) \
                .join(ParkingSpot, Reservation.spot_id == ParkingSpot.id) \
                .filter(ParkingSpot.lot_id == lot.id,
                        Reservation.status == ReservationStatus.ACTIVE.value).scalar()
            completed_count = db.session.query(func.count(Reservation.id)) \
                .join(ParkingSpot, Reservation.spot_id == ParkingSpot.id) \
                .filter(ParkingSpot.lot_id == lot.id,
                        Reservation.status == ReservationStatus.COMPLETED.value).scalar()
            active_counts.append(active_count)
            completed_counts.append(completed_count)
        total_completed_revenue = db.session.query(func.coalesce(func.sum(Reservation.final_cost), 0.0)) \
            .filter(Reservation.status == ReservationStatus.COMPLETED.value).scalar()
        response = {
            'message': 'Admin analytics overview',
            'data': {
                'lots': lot_names,
                'occupancy_percent': occupancy_percent,
                'revenue_by_lot': revenue_values,
                'active_reservations_by_lot': active_counts,
                'completed_reservations_by_lot': completed_counts,
                'total_completed_revenue': float(total_completed_revenue)
            }
        }
        cache_set(cache_key, response, current_app.config['ANALYTICS_CACHE_TTL'])
        return response, 200

api.add_resource(AdminAnalytics, '/api/admin/analytics/overview')

# ------------------------ User Analytics (cached) ------------------------
class UserAnalytics(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'user':
            return {'message': 'User access required'}, 403
        cache_key = f'user_analytics_overview:{current_user.username}'
        cached = cache_get(cache_key)
        if cached:
            return cached, 200
        completed_res = Reservation.query.filter_by(
            user_id=current_user.id,
            status=ReservationStatus.COMPLETED.value
        ).all()
        usage_map = {}
        total_spent = 0.0
        total_hours = 0.0
        for r in completed_res:
            lot_name = r.parking_spot.parking_lot.prime_location_name
            usage_map.setdefault(lot_name, {'count': 0, 'hours': 0.0, 'cost': 0.0})
            usage_map[lot_name]['count'] += 1
            usage_map[lot_name]['hours'] += r.duration_hours
            usage_map[lot_name]['cost'] += (r.final_cost or 0.0)
            total_spent += (r.final_cost or 0.0)
            total_hours += r.duration_hours
        lots = list(usage_map.keys())
        response = {
            'message': 'User analytics overview',
            'data': {
                'lots': lots,
                'reservations_per_lot': [usage_map[n]['count'] for n in lots],
                'hours_per_lot': [round(usage_map[n]['hours'], 2) for n in lots],
                'cost_per_lot': [round(usage_map[n]['cost'], 2) for n in lots],
                'total_spent': round(total_spent, 2),
                'total_hours': round(total_hours, 2)
            }
        }
        cache_set(cache_key, response, current_app.config['ANALYTICS_CACHE_TTL'])
        return response, 200

api.add_resource(UserAnalytics, '/api/user/analytics/overview')

# ------------------------ Data Export Endpoints ------------------------
from models import ExportJob
from tasks import export_user_history, export_admin_all
import json, os

class UserExportHistory(Resource):
    @jwt_required()
    def post(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'user':
            return {'message': 'User access required'}, 403
        job = ExportJob(job_type='user_history', user_id=current_user.id, status='PENDING')
        db.session.add(job); db.session.commit()
        export_user_history.delay(job.id)
        return {'message': 'Export started', 'job_id': job.id}, 202

class UserExportStatus(Resource):
    @jwt_required()
    def get(self, job_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        job = ExportJob.query.get(job_id)
        if not job or job.user_id != current_user.id:
            return {'message': 'Not found'}, 404
        raw = current_app.redis.get(f"job:{job.id}")
        data = json.loads(raw) if raw else {'status': job.status}
        if job.status == 'COMPLETED' and job.file_path and os.path.isfile(job.file_path):
            data['download'] = f"/api/user/export-history/{job.id}/download"
        return {'job': data}, 200

class UserExportDownload(Resource):
    @jwt_required()
    def get(self, job_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        job = ExportJob.query.get(job_id)
        if not job or job.user_id != current_user.id or job.status != 'COMPLETED':
            return {'message': 'Not available'}, 404
        return send_file(job.file_path, as_attachment=True)

api.add_resource(UserExportHistory, '/api/user/export-history')
api.add_resource(UserExportStatus, '/api/user/export-history/<int:job_id>')
api.add_resource(UserExportDownload, '/api/user/export-history/<int:job_id>/download')

class AdminExportAll(Resource):
    @jwt_required()
    def post(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user or current_user.role != 'admin':
            return {'message': 'Admin access required'}, 403
        job = ExportJob(job_type='admin_all', user_id=current_user.id, status='PENDING')
        db.session.add(job); db.session.commit()
        export_admin_all.delay(job.id)
        return {'message': 'Admin export started', 'job_id': job.id}, 202

class AdminExportStatus(Resource):
    @jwt_required()
    def get(self, job_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        job = ExportJob.query.get(job_id)
        if not job or job.user_id != current_user.id:
            return {'message': 'Not found'}, 404
        raw = current_app.redis.get(f"job:{job.id}")
        data = json.loads(raw) if raw else {'status': job.status}
        if job.status == 'COMPLETED' and job.file_path and os.path.isfile(job.file_path):
            data['download'] = f"/api/admin/export-all/{job.id}/download"
        return {'job': data}, 200

class AdminExportDownload(Resource):
    @jwt_required()
    def get(self, job_id):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        job = ExportJob.query.get(job_id)
        if not job or job.user_id != current_user.id or job.status != 'COMPLETED':
            return {'message': 'Not available'}, 404
        return send_file(job.file_path, as_attachment=True)

api.add_resource(AdminExportAll, '/api/admin/export-all')
api.add_resource(AdminExportStatus, '/api/admin/export-all/<int:job_id>')
api.add_resource(AdminExportDownload, '/api/admin/export-all/<int:job_id>/download')

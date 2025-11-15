from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class SpotStatus(Enum):
    AVAILABLE = 'A'
    OCCUPIED = 'O'

class ReservationStatus(Enum):
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    pin_code = db.Column(db.String(10))
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False, unique=True)  # added unique
    address = db.Column(db.Text, nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False, default=20.0)
    maximum_spots = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', lazy=True, cascade='all, delete-orphan')
    
    @property
    def available_spots_count(self):
        return len([spot for spot in self.parking_spots if spot.status == SpotStatus.AVAILABLE.value])
    
    @property
    def occupied_spots_count(self):
        return len([spot for spot in self.parking_spots if spot.status == SpotStatus.OCCUPIED.value])
    
    def __repr__(self):
        return f'<ParkingLot {self.prime_location_name}>'

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    spot_number = db.Column(db.String(10), nullable=False)  # A1, A2, B1, etc.
    status = db.Column(db.String(1), default=SpotStatus.AVAILABLE.value)  # 'A' or 'O'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='parking_spot', lazy=True)
    
    # Unique constraint for spot number within a lot
    __table_args__ = (db.UniqueConstraint('lot_id', 'spot_number', name='unique_spot_per_lot'),)
    
    @property
    def current_reservation(self):
        """Get current active reservation for this spot"""
        return Reservation.query.filter_by(
            spot_id=self.id, 
            status=ReservationStatus.ACTIVE.value
        ).first()
    
    def __repr__(self):
        return f'<ParkingSpot {self.spot_number} - {self.parking_lot.prime_location_name}>'

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    
    # Timestamps
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cost and Status
    estimated_cost = db.Column(db.Float)
    final_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default=ReservationStatus.ACTIVE.value)
    
    # Additional fields
    remarks = db.Column(db.Text)
    
    @property
    def duration_hours(self):
        """Calculate parking duration in hours"""
        if self.leaving_timestamp:
            duration = self.leaving_timestamp - self.parking_timestamp
            return round(duration.total_seconds() / 3600, 2)
        else:
            # Current duration for active reservations
            duration = datetime.utcnow() - self.parking_timestamp
            return round(duration.total_seconds() / 3600, 2)
    
    @property
    def calculated_cost(self):
        """Calculate cost based on duration and lot price"""
        if hasattr(self.parking_spot, 'parking_lot'):
            price_per_hour = self.parking_spot.parking_lot.price_per_hour
            return round(self.duration_hours * price_per_hour, 2)
        return 0.0
    
    def complete_reservation(self):
        """Mark reservation as completed and update spot status"""
        self.leaving_timestamp = datetime.utcnow()
        self.final_cost = self.calculated_cost
        self.status = ReservationStatus.COMPLETED.value
        self.parking_spot.status = SpotStatus.AVAILABLE.value
    
    def __repr__(self):
        return f'<Reservation {self.id} - User {self.user.username}'

# Helper functions for database operations
def create_parking_spots_for_lot(lot_id, max_spots):
    """Create parking spots for a parking lot"""
    from string import ascii_uppercase
    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return False
    
    # Clear existing spots
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()
    
    # Create new spots with naming convention: A1, A2, ..., B1, B2, etc.
    spots_per_row = 10
    spots_created = 0
    
    for row_index, letter in enumerate(ascii_uppercase):
        if spots_created >= max_spots:
            break
            
        for number in range(1, spots_per_row + 1):
            if spots_created >= max_spots:
                break
                
            spot_number = f"{letter}{number}"
            spot = ParkingSpot(
                lot_id=lot_id,
                spot_number=spot_number,
                status=SpotStatus.AVAILABLE.value
            )
            db.session.add(spot)
            spots_created += 1
    
    db.session.commit()
    return True

class Admin:
    """Admin functionality through User model with role='admin'"""
    
    @staticmethod
    def create_default_admin():
        """Create default admin user if not exists"""
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@parking.com',
                password=generate_password_hash('admin123'),  # hash
                full_name='System Administrator',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('Default admin user created: username="admin", password="admin123"')
        return admin

def init_sample_data():
    """Initialize sample data for development"""
    
    # Create admin
    Admin.create_default_admin()
    
    # Create sample users
    if not User.query.filter_by(username='user1').first():
        user1 = User(
            username='user1',
            email='user1@example.com',
            password=generate_password_hash('user123'),  # hash
            full_name='John Doe',
            phone='9876543210',
            address='123 Main Street',
            pin_code='560001'
        )
        db.session.add(user1)
    
    if not User.query.filter_by(username='user2').first():
        user2 = User(
            username='user2',
            email='user2@example.com',
            password=generate_password_hash('user123'),  # hash
            full_name='Jane Smith',
            phone='9876543211',
            address='456 Park Avenue',
            pin_code='560002'
        )
        db.session.add(user2)
    
    # Create sample parking lots
    if not ParkingLot.query.filter_by(prime_location_name='Koramangala').first():
        lot1 = ParkingLot(
            prime_location_name='Koramangala',
            address='Forum Mall, Koramangala, Bangalore',
            pin_code='560034',
            price_per_hour=25.0,
            maximum_spots=50
        )
        db.session.add(lot1)
        db.session.commit()
        create_parking_spots_for_lot(lot1.id, 50)
    
    if not ParkingLot.query.filter_by(prime_location_name='Indiranagar').first():
        lot2 = ParkingLot(
            prime_location_name='Indiranagar',
            address='100 Feet Road, Indiranagar, Bangalore',
            pin_code='560038',
            price_per_hour=30.0,
            maximum_spots=75
        )
        db.session.add(lot2)
        db.session.commit()
        create_parking_spots_for_lot(lot2.id, 75)
    
    db.session.commit()
    print("Sample data initialized successfully!")

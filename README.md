# Vehicle Parking System - MAD II Project

A comprehensive vehicle parking management system built with Flask (Backend) and Vue.js (Frontend) as part of Modern Application Development II course.

## 🚗 Project Overview

This parking management system provides a complete solution for managing parking lots, reservations, and user accounts with role-based access control.

### **Key Features:**
- **User Management**: Registration, login, and profile management
- **Admin Dashboard**: Parking lot management, user oversight, analytics
- **Parking System**: Real-time spot availability, reservation system
- **Cost Calculation**: Automatic billing based on parking duration
- **Analytics**: Revenue tracking and usage statistics
- **Background Jobs**: Automated reminders and reports

## 🏗️ Architecture

### **Backend (Flask)**
- RESTful API with Flask-RESTful
- JWT Authentication
- SQLAlchemy ORM with SQLite
- Redis caching for performance
- Celery for background tasks

### **Frontend (Vue.js 3)**
- Modern Vue.js 3 with Composition API
- Bootstrap 5 for clean, responsive UI
- Axios for API communication
- Chart.js for analytics visualization

## 📊 Milestone Progress

### **Core Requirements (8 Milestones)**
- [x] Milestone 0: GitHub Repository Setup (5%) ✅
- [ ] Milestone 1: Database Models and Schema Setup (15%)
- [ ] Milestone 2: Authentication & Role-based Access (10%)
- [ ] Milestone 3: Admin Dashboard and Lot/Spot Management (20%)
- [ ] Milestone 4: User Dashboard and Reservation System (15%)
- [ ] Milestone 5: Reservation History and Cost Calculation (10%)
- [ ] Milestone 6: Parking Analytics and Charts (10%)
- [ ] Milestone 7: API Performance Optimization & Redis Caching (5%)
- [ ] Milestone 8: Backend Jobs - Daily Reminders & Monthly Reports (10%)

### **Recommended Enhancements**
- [ ] Search Functionality for Lots and Spots
- [ ] UI/UX Enhancements and PWA Features
- [ ] Advanced Analytics and AI Features

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- Node.js 16+
- Redis server
- Git

### **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

## 🛠️ Technology Stack

**Backend:**
- Flask 3.0
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-RESTful
- Redis & Celery

**Frontend:**
- Vue.js 3
- Vue Router
- Bootstrap 5
- Chart.js
- Axios

## 📝 API Documentation

The API follows RESTful conventions with JWT authentication:

- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET /api/parking-lots` - List available parking lots
- `POST /api/reservations` - Create new reservation
- `GET /api/admin/dashboard` - Admin analytics

## 🎯 Project Goals

1. **Functionality First**: Clean, working features over fancy UI
2. **Role-Based Access**: Clear separation between admin and user capabilities
3. **Real-time Updates**: Live parking availability and status
4. **Performance**: Optimized with caching and background processing
5. **Scalability**: Modular design for easy feature additions


**Developer**: Syed Ali Mujtaba
**Course**: Modern Application Development II  
**Institution**: IIT Madras  

## 📄 License

This project is developed as part of academic coursework for IIT Madras MAD II course.

---

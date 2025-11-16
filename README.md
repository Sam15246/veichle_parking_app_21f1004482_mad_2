# Vehicle Parking System - MAD II Project

A comprehensive vehicle parking management system built with Flask (Backend) and Vue.js (Frontend) as part of Modern Application Development II course.

## 🚗 Project Overview

This parking management system provides a complete solution for managing parking lots, reservations, and user accounts with role-based access control.

### **Key Features:**

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

## 📊 Milestone Progress

### **Core Requirements (8 Milestones)**
- [x] Milestone 0: GitHub Repository Setup (5%) ✅
- [ ] Milestone 1: Database Models and Schema Setup (15%)
- [ ] Milestone 2: Authentication & Role-based Access (10%)
- [ ] Milestone 3: Admin Dashboard and Lot/Spot Management (20%)
- [ ] Milestone 4: User Dashboard and Reservation System (15%)
- [ ] Milestone 5: Reservation History and Cost Calculation (10%)
- [x] Milestone 6: Parking Analytics and Charts (10%)
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

## 🔌 Redis Setup (Caching + Celery Broker)

Options:
- Local install (Linux/macOS): redis-server
- Windows (recommended): Docker
  - docker run -d -p 6379:6379 --name redis redis:7-alpine
- Windows (native): Memurai or Redis for Windows ports

Environment variables (optional):
```bash
# Single URL to drive app Redis + Celery (uses DB 0/1/2 automatically)
set REDIS_URL=redis://127.0.0.1:6379/0
# Optional overrides
set CELERY_BROKER_URL=redis://127.0.0.1:6379/1
set CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
# Tuning
set LOTS_CACHE_TTL=60
set ANALYTICS_CACHE_TTL=120
set MAX_ACTIVE_RESERVATIONS_PER_USER=5
```

## 🧵 Celery Workers + Beat

Start API (creates DB on first run):
```bash
python backend/app.py
```

Start Redis (if not already):
```bash
redis-server
# or Docker:
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

Start Celery worker and beat (Windows: prefer solo pool):
```bash
cd backend
celery -A celery_worker.celery worker -l info --pool solo
celery -A celery_worker.celery beat -l info
```

Verify:
- API health: GET http://localhost:5000/health
- Ops status: GET http://localhost:5000/ops/status (redis.enabled should be true)
- Caching: call GET /api/parking-lots twice (second should be faster; cache invalidates on lot/reservation mutations)
- Tasks: daily/monthly scheduled by Celery beat (18:00 daily, 1st of month 08:00)

Common issues:
- Error 10061 (Windows): Redis not running or blocked; start Redis or use Docker.
- AttributeError user_options: use celery -A celery_worker.celery ... (not the factory).

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

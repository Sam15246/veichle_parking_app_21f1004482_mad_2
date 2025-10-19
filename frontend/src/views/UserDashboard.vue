<template>
  <div class="container mt-4">
    <!-- Header -->
    <div class="row mb-4">
      <div class="col">
        <h2 class="text-primary">
          <i class="bi bi-person-circle"></i>
          User Dashboard
        </h2>
        <p class="text-muted">Welcome back, {{ userFullName }}</p>
      </div>
      <div class="col-auto">
        <button @click="logout" class="btn btn-outline-primary">
          <i class="bi bi-box-arrow-right"></i>
          Logout
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else>
      <!-- User Statistics -->
      <div class="row mb-4">
        <div class="col-md-4 mb-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ userStats.total_reservations }}</h4>
                  <p class="mb-0">Total Bookings</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-calendar-check fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4 mb-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ userStats.active_reservations }}</h4>
                  <p class="mb-0">Active Parking</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-car-front-fill fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4 mb-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ userStats.available_lots }}</h4>
                  <p class="mb-0">Available Lots</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-geo-alt fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="row">
        <div class="col">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">Quick Actions</h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <div class="d-grid">
                    <button class="btn btn-primary">
                      <i class="bi bi-search"></i>
                      Find Parking Spots
                    </button>
                  </div>
                </div>
                <div class="col-md-6 mb-3">
                  <div class="d-grid">
                    <button class="btn btn-success">
                      <i class="bi bi-plus-circle"></i>
                      Book New Spot
                    </button>
                  </div>
                </div>
                <div class="col-md-6 mb-3">
                  <div class="d-grid">
                    <button class="btn btn-info">
                      <i class="bi bi-clock-history"></i>
                      View Booking History
                    </button>
                  </div>
                </div>
                <div class="col-md-6 mb-3">
                  <div class="d-grid">
                    <button class="btn btn-warning">
                      <i class="bi bi-person-gear"></i>
                      Update Profile
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// Reactive data
const loading = ref(true)
const userFullName = ref('')
const userStats = ref({
  total_reservations: 0,
  active_reservations: 0,
  available_lots: 0
})

// Get user info from localStorage
onMounted(async () => {
  // Check authentication
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')
  
  if (!token || userRole !== 'user') {
    router.push('/login')
    return
  }

  userFullName.value = localStorage.getItem('userFullName') || 'User'
  
  // Load dashboard data
  await loadDashboardData()
})

// Load dashboard data
const loadDashboardData = async () => {
  try {
    const token = localStorage.getItem('token')
    
    const response = await axios.get('http://localhost:5000/api/user/dashboard', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    userStats.value = response.data.user_data
    
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    if (error.response?.status === 401 || error.response?.status === 403) {
      logout()
    }
  } finally {
    loading.value = false
  }
}

// Logout function
const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('userId')
  localStorage.removeItem('username')
  localStorage.removeItem('userRole')
  localStorage.removeItem('userFullName')
  router.push('/login')
}
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.btn:hover {
  transform: translateY(-1px);
  transition: transform 0.2s ease-in-out;
}

.fs-1 {
  font-size: 2rem !important;
}
</style>

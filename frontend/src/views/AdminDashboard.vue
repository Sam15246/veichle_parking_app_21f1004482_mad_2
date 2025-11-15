<template>
  <div class="container mt-4">
    <!-- Header -->
    <div class="row mb-4">
      <div class="col">
        <h2 class="text-danger">
          <i class="bi bi-shield-check"></i>
          Admin Dashboard
        </h2>
        <p class="text-muted">Welcome back, {{ userFullName }}</p>
      </div>
      <div class="col-auto">
        <button @click="logout" class="btn btn-outline-danger">
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
      <!-- Statistics Cards -->
      <div class="row mb-4">
        <div class="col-md-3 mb-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ statistics.total_users }}</h4>
                  <p class="mb-0">Total Users</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-people fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-3 mb-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ statistics.total_parking_lots }}</h4>
                  <p class="mb-0">Parking Lots</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-building fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-3 mb-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ statistics.total_parking_spots }}</h4>
                  <p class="mb-0">Parking Spots</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-car-front fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-3 mb-3">
          <div class="card bg-warning text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4>{{ statistics.active_reservations }}</h4>
                  <p class="mb-0">Active Bookings</p>
                </div>
                <div class="align-self-center">
                  <i class="bi bi-clock fs-1"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Manage Parking Lots -->
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Manage Parking Lots</h5>
          <button class="btn btn-sm btn-primary" @click="resetLotForm">Add New Lot</button>
        </div>
        <div class="card-body">
          <!-- Create/Update Form -->
          <form class="row g-3" @submit.prevent="submitLot">
            <div class="col-md-3">
              <label class="form-label">Location Name</label>
              <input v-model="lotForm.prime_location_name" class="form-control" required />
            </div>
            <div class="col-md-3">
              <label class="form-label">Address</label>
              <input v-model="lotForm.address" class="form-control" required />
            </div>
            <div class="col-md-2">
              <label class="form-label">Pin Code</label>
              <input v-model="lotForm.pin_code" class="form-control" required />
            </div>
            <div class="col-md-2">
              <label class="form-label">Price/Hour</label>
              <input type="number" step="0.01" v-model.number="lotForm.price_per_hour" class="form-control" required />
            </div>
            <div class="col-md-2">
              <label class="form-label">Capacity</label>
              <input type="number" min="1" v-model.number="lotForm.maximum_spots" class="form-control" required />
            </div>
            <div class="col-12">
              <button class="btn btn-success me-2" type="submit">
                {{ lotForm.id ? 'Update Lot' : 'Create Lot' }}
              </button>
              <span v-if="lotMessage" :class="['ms-2', lotMessageType==='error'?'text-danger':'text-success']">
                {{ lotMessage }}
              </span>
            </div>
          </form>

          <!-- Lots Table -->
          <div class="table-responsive mt-4">
            <table class="table table-striped align-middle">
              <thead>
                <tr>
                  <th>Name</th><th>Pin</th><th>Price</th><th>Capacity</th><th>Avail</th><th>Occ</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lot in lots" :key="lot.id">
                  <td>{{ lot.prime_location_name }}</td>
                  <td>{{ lot.pin_code }}</td>
                  <td>{{ lot.price_per_hour }}</td>
                  <td>{{ lot.maximum_spots }}</td>
                  <td>{{ lot.available_spots }}</td>
                  <td>{{ lot.occupied_spots }}</td>
                  <td class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-primary" @click="editLot(lot)">Edit</button>
                    <button class="btn btn-sm btn-outline-info" @click="viewSpots(lot)">Spots</button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteLot(lot)">Delete</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Spots Viewer -->
      <div class="card mb-4" v-if="selectedLot">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Spots in {{ selectedLot.prime_location_name }}</h5>
          <button class="btn btn-sm btn-outline-secondary" @click="selectedLot = null">Close</button>
        </div>
        <div class="card-body">
          <div class="mb-2">
            <span class="badge bg-success me-2">Available: {{ spotsSummary.available_spots }}</span>
            <span class="badge bg-danger">Occupied: {{ spotsSummary.occupied_spots }}</span>
          </div>
          <div class="table-responsive">
            <table class="table table-sm table-bordered">
              <thead><tr><th>#</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="s in spots" :key="s.id">
                  <td>{{ s.spot_number }}</td>
                  <td>
                    <span class="badge" :class="s.status==='A'?'bg-success':'bg-danger'">
                      {{ s.status==='A'?'Available':'Occupied' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Users List -->
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">Users</h5>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-striped align-middle">
              <thead>
                <tr><th>Username</th><th>Name</th><th>Email</th><th>Role</th><th>Active Spot</th><th>Lot</th></tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id">
                  <td>{{ u.username }}</td>
                  <td>{{ u.full_name }}</td>
                  <td>{{ u.email }}</td>
                  <td><span class="badge" :class="u.role==='admin'?'bg-danger':'bg-primary'">{{ u.role }}</span></td>
                  <td>{{ u.active_spot_number || '-' }}</td>
                  <td>{{ u.active_lot || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- All Reservations (History) -->
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">All Reservations</h5>
          <small class="text-muted">History with duration and cost</small>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-sm table-striped align-middle">
              <thead>
                <tr>
                  <th>#</th>
                  <th>User</th>
                  <th>Lot</th>
                  <th>Spot</th>
                  <th>Vehicle</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Duration (h)</th>
                  <th>Status</th>
                  <th>Price/hr</th>
                  <th>Final Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in reservations" :key="r.id">
                  <td>{{ r.id }}</td>
                  <td>{{ r.user?.username }}</td>
                  <td>{{ r.lot?.name }}</td>
                  <td>{{ r.spot?.spot_number }}</td>
                  <td>{{ r.vehicle_number }}</td>
                  <td>{{ formatDate(r.parking_timestamp) }}</td>
                  <td>{{ r.leaving_timestamp ? formatDate(r.leaving_timestamp) : '-' }}</td>
                  <td>{{ r.duration_hours }}</td>
                  <td>
                    <span class="badge"
                      :class="r.status==='COMPLETED' ? 'bg-success' : (r.status==='ACTIVE' ? 'bg-primary' : 'bg-secondary')">
                      {{ r.status }}
                    </span>
                  </td>
                  <td>₹ {{ r.lot?.price_per_hour }}</td>
                  <td>₹ {{ r.final_cost ?? r.calculated_cost }}</td>
                </tr>
                <tr v-if="reservations.length===0">
                  <td colspan="11" class="text-center text-muted">No reservations found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Analytics -->
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Parking Analytics</h5>
          <small class="text-muted">Occupancy & Revenue</small>
        </div>
        <div class="card-body">
          <div class="row gy-4">
            <div class="col-md-6">
              <h6 class="text-muted">Occupancy (%)</h6>
              <canvas id="adminOccupancyChart"></canvas>
            </div>
            <div class="col-md-6">
              <h6 class="text-muted">Revenue (₹)</h6>
              <canvas id="adminRevenueChart"></canvas>
            </div>
          </div>
          <div class="mt-3">
            <strong>Total Completed Revenue:</strong> ₹ {{ analytics.total_completed_revenue }}
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
const statistics = ref({
  total_users: 0,
  total_parking_lots: 0,
  total_parking_spots: 0,
  active_reservations: 0
})

const lots = ref([])
const lotForm = ref({ id: null, prime_location_name: '', address: '', pin_code: '', price_per_hour: 20, maximum_spots: 10 })
const lotMessage = ref('')
const lotMessageType = ref('success')

const selectedLot = ref(null)
const spots = ref([])
const spotsSummary = ref({ available_spots: 0, occupied_spots: 0 })

const users = ref([])
const reservations = ref([])

const analytics = ref({
  lots: [],
  occupancy_percent: [],
  revenue_by_lot: [],
  total_completed_revenue: 0
})

// Get user info from localStorage
onMounted(async () => {
  // Check authentication
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')
  
  if (!token || userRole !== 'admin') {
    router.push('/login')
    return
  }

  userFullName.value = localStorage.getItem('userFullName') || 'Admin'
  
  // Load dashboard data
  await loadDashboardData()
})

// Load dashboard data
const loadDashboardData = async () => {
  try {
    const token = localStorage.getItem('token')
    
    const response = await axios.get('http://localhost:5000/api/admin/dashboard', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    statistics.value = response.data.statistics
    
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

// Lots
const loadLots = async () => {
  const res = await axios.get('http://localhost:5000/api/admin/lots', { headers: authHeader() })
  lots.value = res.data.data
}

const resetLotForm = () => {
  lotForm.value = { id: null, prime_location_name: '', address: '', pin_code: '', price_per_hour: 20, maximum_spots: 10 }
  lotMessage.value = ''
}

const submitLot = async () => {
  try {
    if (lotForm.value.id) {
      await axios.put(`http://localhost:5000/api/admin/lots/${lotForm.value.id}`, lotForm.value, { headers: authHeader() })
      lotMessage.value = 'Lot updated'; lotMessageType.value = 'success'
    } else {
      await axios.post('http://localhost:5000/api/admin/lots', lotForm.value, { headers: authHeader() })
      lotMessage.value = 'Lot created'; lotMessageType.value = 'success'
    }
    await loadLots(); resetLotForm()
  } catch (e) {
    lotMessage.value = e?.response?.data?.message || 'Operation failed'
    lotMessageType.value = 'error'
  }
}

const editLot = (lot) => {
  lotForm.value = { ...lot, id: lot.id }
  lotMessage.value = ''
}

const deleteLot = async (lot) => {
  if (!confirm(`Delete lot "${lot.prime_location_name}"? This cannot be undone.`)) return
  try {
    await axios.delete(`http://localhost:5000/api/admin/lots/${lot.id}`, { headers: authHeader() })
    await loadLots()
    if (selectedLot.value?.id === lot.id) selectedLot.value = null
  } catch (e) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}

const viewSpots = async (lot) => {
  selectedLot.value = lot
  const res = await axios.get(`http://localhost:5000/api/admin/lots/${lot.id}/spots`, { headers: authHeader() })
  spots.value = res.data.data
  spotsSummary.value = {
    available_spots: res.data.lot.available_spots,
    occupied_spots: res.data.lot.occupied_spots
  }
}

// Users
const loadUsers = async () => {
  const res = await axios.get('http://localhost:5000/api/admin/users', { headers: authHeader() })
  users.value = res.data.data
}

// Reservations
const loadReservations = async () => {
  const res = await axios.get('http://localhost:5000/api/admin/reservations', { headers: authHeader() })
  reservations.value = res.data.data || []
}

// Analytics
const loadAnalytics = async () => {
  const res = await axios.get('http://localhost:5000/api/admin/analytics/overview', { headers: authHeader() })
  analytics.value = res.data.data
  renderAnalyticsCharts()
}

const renderAnalyticsCharts = async () => {
  const { Chart } = await import('chart.js/auto')
  const occCtx = document.getElementById('adminOccupancyChart')
  const revCtx = document.getElementById('adminRevenueChart')
  if (occCtx) {
    new Chart(occCtx, {
      type: 'bar',
      data: {
        labels: analytics.value.lots,
        datasets: [{ label: 'Occupancy %', data: analytics.value.occupancy_percent, backgroundColor: '#0d6efd' }]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } }
    })
  }
  if (revCtx) {
    new Chart(revCtx, {
      type: 'bar',
      data: {
        labels: analytics.value.lots,
        datasets: [{ label: 'Revenue (₹)', data: analytics.value.revenue_by_lot, backgroundColor: '#198754' }]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    })
  }
}

// Extend mounted promise group
onMounted(async () => {
  // ...existing auth + base stats...
  await Promise.all([loadDashboardData(), loadLots(), loadUsers(), loadReservations(), loadAnalytics()])
})

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` })
const formatDate = (iso) => iso ? new Date(iso).toLocaleString() : '-'
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

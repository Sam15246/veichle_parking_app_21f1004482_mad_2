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

      <!-- Active Parking -->
      <div class="card mb-4" v-if="activeReservation">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Active Parking</h5>
          <button class="btn btn-sm btn-outline-danger" @click="releaseActive" :disabled="releasing">
            <span v-if="releasing" class="spinner-border spinner-border-sm me-1"></span>
            Release
          </button>
        </div>
        <div class="card-body">
          <div class="row gy-2">
            <div class="col-md-3"><strong>Lot:</strong> {{ activeReservation.lot.name }}</div>
            <div class="col-md-3"><strong>Spot:</strong> {{ activeReservation.spot.spot_number }}</div>
            <div class="col-md-3"><strong>Vehicle:</strong> {{ activeReservation.vehicle_number }}</div>
            <div class="col-md-3"><strong>Since:</strong> {{ formatDate(activeReservation.parking_timestamp) }}</div>
          </div>
          <div class="mt-2">
            <strong>Duration:</strong> {{ activeReservation.duration_hours }} h
            <span class="ms-3"><strong>Est. Cost:</strong> ₹ {{ activeReservation.calculated_cost }}</span>
          </div>
        </div>
      </div>

      <!-- Available Lots (Book) -->
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Available Parking Lots</h5>
          <small class="text-muted">Click Book to auto-allocate a spot</small>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-striped align-middle">
              <thead>
                <tr>
                  <th>Lot</th><th>Pin</th><th>Price/hr</th><th>Available</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lot in lots" :key="lot.id">
                  <td>{{ lot.prime_location_name }}</td>
                  <td>{{ lot.pin_code }}</td>
                  <td>₹ {{ lot.price_per_hour }}</td>
                  <td>
                    <span class="badge" :class="lot.available_spots>0?'bg-success':'bg-secondary'">
                      {{ lot.available_spots }}
                    </span>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-primary"
                            :disabled="booking || !!activeReservation || lot.available_spots===0"
                            @click="bookLot(lot)">
                      <span v-if="bookingLotId===lot.id && booking" class="spinner-border spinner-border-sm me-1"></span>
                      Book
                    </button>
                  </td>
                </tr>
                <tr v-if="lots.length===0">
                  <td colspan="5" class="text-center text-muted">No lots found</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="actionMessage" :class="['mt-2', actionType==='error'?'text-danger':'text-success']">
            {{ actionMessage }}
          </div>
        </div>
      </div>

      <!-- Reservation History -->
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">Reservation History</h5>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-sm table-bordered">
              <thead>
                <tr>
                  <th>#</th><th>Lot</th><th>Spot</th><th>Vehicle</th>
                  <th>Start</th><th>End</th><th>Status</th><th>Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in history" :key="r.id">
                  <td>{{ r.id }}</td>
                  <td>{{ r.lot?.name }}</td>
                  <td>{{ r.spot?.spot_number }}</td>
                  <td>{{ r.vehicle_number }}</td>
                  <td>{{ formatDate(r.parking_timestamp) }}</td>
                  <td>{{ r.leaving_timestamp ? formatDate(r.leaving_timestamp) : '-' }}</td>
                  <td>
                    <span class="badge"
                          :class="r.status==='COMPLETED'?'bg-success':(r.status==='ACTIVE'?'bg-primary':'bg-secondary')">
                      {{ r.status }}
                    </span>
                  </td>
                  <td>₹ {{ r.final_cost ?? r.calculated_cost }}</td>
                </tr>
                <tr v-if="history.length===0">
                  <td colspan="8" class="text-center text-muted">No reservations yet</td>
                </tr>
              </tbody>
            </table>
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
const userStats = ref({ total_reservations: 0, active_reservations: 0, available_lots: 0 })

// New state
const lots = ref([])
const activeReservation = ref(null)
const history = ref([])
const booking = ref(false)
const bookingLotId = ref(null)
const releasing = ref(false)
const actionMessage = ref('')
const actionType = ref('success')

// Helpers
const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` })
const formatDate = (iso) => iso ? new Date(iso).toLocaleString() : '-'

// Mounted
onMounted(async () => {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')
  if (!token || userRole !== 'user') {
    router.push('/login')
    return
  }
  userFullName.value = localStorage.getItem('userFullName') || 'User'
  await Promise.all([
    loadDashboardData(),
    loadLots(),
    loadActiveReservation(),
    loadHistory()
  ])
})

// Existing stats
const loadDashboardData = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('http://localhost:5000/api/user/dashboard', {
      headers: { Authorization: `Bearer ${token}` }
    })
    userStats.value = response.data.user_data
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) logout()
  } finally {
    loading.value = false
  }
}

// New loads
const loadLots = async () => {
  const res = await axios.get('http://localhost:5000/api/parking-lots')
  lots.value = res.data.data || []
}

const loadActiveReservation = async () => {
  const res = await axios.get('http://localhost:5000/api/user/reservations/active', { headers: authHeader() })
  activeReservation.value = res.data.reservation || null
}

const loadHistory = async () => {
  const res = await axios.get('http://localhost:5000/api/user/reservations', { headers: authHeader() })
  history.value = res.data.data || []
}

// Actions
const bookLot = async (lot) => {
  actionMessage.value = ''
  actionType.value = 'success'
  const vehicle_number = window.prompt(`Enter vehicle number to book at ${lot.prime_location_name}:`)
  if (!vehicle_number) return
  booking.value = true
  bookingLotId.value = lot.id
  try {
    await axios.post('http://localhost:5000/api/reservations', {
      lot_id: lot.id,
      vehicle_number
    }, { headers: authHeader() })
    actionMessage.value = 'Reservation created successfully'
    actionType.value = 'success'
    await Promise.all([loadActiveReservation(), loadLots(), loadHistory(), loadDashboardData()])
  } catch (e) {
    actionMessage.value = e?.response?.data?.message || 'Reservation failed'
    actionType.value = 'error'
  } finally {
    booking.value = false
    bookingLotId.value = null
  }
}

const releaseActive = async () => {
  if (!activeReservation.value) return
  releasing.value = true
  actionMessage.value = ''
  actionType.value = 'success'
  try {
    await axios.post(`http://localhost:5000/api/reservations/${activeReservation.value.id}/release`, {}, { headers: authHeader() })
    actionMessage.value = 'Reservation released'
    actionType.value = 'success'
    await Promise.all([loadActiveReservation(), loadLots(), loadHistory(), loadDashboardData()])
  } catch (e) {
    actionMessage.value = e?.response?.data?.message || 'Release failed'
    actionType.value = 'error'
  } finally {
    releasing.value = false
  }
}

// Logout
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

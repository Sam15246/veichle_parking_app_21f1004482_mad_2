<template>
  <div class="container mt-4">
    <!-- Header -->
    <div class="row mb-3 align-items-center">
      <div class="col">
        <h2 class="text-primary">
          <i class="bi bi-person-circle"></i>
          User Dashboard
        </h2>
        <p class="text-muted mb-0">Welcome back, {{ userFullName }}</p>
      </div>
      <div class="col-auto d-flex gap-2">
        <!-- New top action buttons -->
        <button class="btn btn-outline-secondary" @click="scrollToLots">
          <i class="bi bi-search"></i> Find Parking Spots
        </button>
        <button class="btn btn-outline-warning" @click="openProfileModal">
          <i class="bi bi-person-gear"></i> Update Profile
        </button>
        <button @click="logout" class="btn btn-outline-primary">
          <i class="bi bi-box-arrow-right"></i> Logout
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Content -->
    <div v-else>
      <!-- Stats -->
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

      <!-- Active Parkings (multiple) -->
      <div class="card mb-4" v-if="activeReservations.length">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Active Parkings ({{ activeReservations.length }})</h5>
          <small class="text-muted">You can have multiple active reservations</small>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-sm table-striped align-middle">
              <thead>
                <tr>
                  <th>#</th><th>Lot</th><th>Spot</th><th>Vehicle</th><th>Since</th><th>Duration (h)</th><th>Billed (h)</th><th>Est. Cost</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in activeReservations" :key="r.id">
                  <td>{{ r.id }}</td>
                  <td>{{ r.lot.name }}</td>
                  <td>{{ r.spot.spot_number }}</td>
                  <td>{{ r.vehicle_number }}</td>
                  <td>{{ formatDate(r.parking_timestamp) }}</td>
                  <td>{{ r.duration_hours }}</td>
                  <td>{{ r.billed_hours }}</td>
                  <td>₹ {{ r.calculated_cost }}</td>
                  <td>
                    <button class="btn btn-sm btn-outline-danger"
                            :disabled="releasingId===r.id"
                            @click="releaseReservation(r)">
                      <span v-if="releasingId===r.id" class="spinner-border spinner-border-sm me-1"></span>
                      Release
                    </button>
                  </td>
                </tr>
                <tr v-if="activeReservations.length===0">
                  <td colspan="9" class="text-center text-muted">No active reservations</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Available Lots (Book) -->
      <div class="card mb-4" id="lotsSection">
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
                            :disabled="bookingLotId===lot.id || lot.available_spots===0"
                            @click="bookLot(lot)">
                      <span v-if="bookingLotId===lot.id" class="spinner-border spinner-border-sm me-1"></span>
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
                  <th>Start</th><th>End</th><th>Duration (h)</th><th>Billed (h)</th><th>Status</th><th>Cost</th>
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
                  <td>{{ r.duration_hours }}</td>
                  <td>{{ r.billed_hours }}</td>
                  <td>
                    <span class="badge"
                          :class="r.status==='COMPLETED'?'bg-success':(r.status==='ACTIVE'?'bg-primary':'bg-secondary')">
                      {{ r.status }}
                    </span>
                  </td>
                  <td>₹ {{ r.final_cost ?? r.calculated_cost }}</td>
                </tr>
                <tr v-if="history.length===0">
                  <td colspan="10" class="text-center text-muted">No reservations yet</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- User Analytics -->
      <div class="card mb-4" v-if="uAnalytics.lots.length">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Your Parking Analytics</h5>
          <small class="text-muted">Reservations & Spending</small>
        </div>
        <div class="card-body">
          <div class="row gy-4">
            <div class="col-md-6">
              <h6 class="text-muted">Reservations per Lot</h6>
              <canvas id="userUsageChart"></canvas>
            </div>
            <div class="col-md-6">
              <h6 class="text-muted">Cost per Lot (₹)</h6>
              <canvas id="userCostChart"></canvas>
            </div>
          </div>
          <div class="mt-3">
            <strong>Total Spent:</strong> ₹ {{ uAnalytics.total_spent }}
            <span class="ms-3"><strong>Total Hours:</strong> {{ uAnalytics.total_hours }} h</span>
          </div>
        </div>
      </div>

      <!-- Profile Modal -->
      <div class="modal fade" id="profileModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Update Profile</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div v-if="profileMessage" :class="['mb-2', profileMessageType==='error'?'text-danger':'text-success']">
                {{ profileMessage }}
              </div>
              <form @submit.prevent="saveProfile">
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input class="form-control" v-model="profileForm.full_name" required />
                </div>
                <div class="mb-3">
                  <label class="form-label">Phone</label>
                  <input class="form-control" v-model="profileForm.phone" />
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <textarea class="form-control" rows="2" v-model="profileForm.address"></textarea>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pin Code</label>
                  <input class="form-control" v-model="profileForm.pin_code" />
                </div>
                <div class="d-flex justify-content-end gap-2">
                  <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                  <button type="submit" class="btn btn-primary" :disabled="profileSaving">
                    <span v-if="profileSaving" class="spinner-border spinner-border-sm me-1"></span>
                    Save
                  </button>
                </div>
              </form>
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
const activeReservations = ref([])
const history = ref([])
const booking = ref(false)
const bookingLotId = ref(null)
const releasingId = ref(null)
const actionMessage = ref('')
const actionType = ref('success')
const uAnalytics = ref({
  lots: [],
  reservations_per_lot: [],
  hours_per_lot: [],
  cost_per_lot: [],
  total_spent: 0,
  total_hours: 0
})
const profileForm = ref({ full_name: '', phone: '', address: '', pin_code: '' })
const profileMessage = ref('')
const profileMessageType = ref('success')
const profileSaving = ref(false)

// Helpers
const authHeader = () => ({ Authorization: `Bearer ${sessionStorage.getItem('token')}` })
const formatDate = (iso) => iso ? new Date(iso).toLocaleString() : '-'

// Mounted
onMounted(async () => {
  const token = sessionStorage.getItem('token')
  const userRole = sessionStorage.getItem('userRole')
  if (!token || userRole !== 'user') {
    router.push('/login')
    return
  }
  userFullName.value = sessionStorage.getItem('userFullName') || 'User'
  await Promise.all([
    loadDashboardData(),
    loadLots(),
    loadActiveReservations(),
    loadHistory(),
    loadUserAnalytics(),
    loadProfile()
  ])
})

// Existing stats
const loadDashboardData = async () => {
  try {
    const token = sessionStorage.getItem('token')
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

const loadActiveReservations = async () => {
  const res = await axios.get('http://localhost:5000/api/user/reservations/active', { headers: authHeader() })
  activeReservations.value = res.data.reservations || []
}

const loadHistory = async () => {
  const res = await axios.get('http://localhost:5000/api/user/reservations', { headers: authHeader() })
  history.value = res.data.data || []
}

const loadUserAnalytics = async () => {
  const res = await axios.get('http://localhost:5000/api/user/analytics/overview', { headers: authHeader() })
  uAnalytics.value = res.data.data
  renderUserCharts()
}

const loadProfile = async () => {
  try {
    const res = await axios.get('http://localhost:5000/api/profile', { headers: authHeader() })
    const u = res.data.user
    profileForm.value = {
      full_name: u.full_name || '',
      phone: u.phone || '',
      address: u.address || '',
      pin_code: u.pin_code || ''
    }
  } catch (e) {
    // ignore
  }
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
    await Promise.all([loadActiveReservations(), loadLots(), loadHistory(), loadDashboardData()])
  } catch (e) {
    actionMessage.value = e?.response?.data?.message || 'Reservation failed'
    actionType.value = 'error'
  } finally {
    booking.value = false
    bookingLotId.value = null
  }
}

const releaseReservation = async (r) => {
  releasingId.value = r.id
  actionMessage.value = ''
  actionType.value = 'success'
  try {
    await axios.post(`http://localhost:5000/api/reservations/${r.id}/release`, {}, { headers: authHeader() })
    actionMessage.value = `Reservation ${r.id} released`
    actionType.value = 'success'
    await Promise.all([loadActiveReservations(), loadLots(), loadHistory(), loadDashboardData()])
  } catch (e) {
    actionMessage.value = e?.response?.data?.message || 'Release failed'
    actionType.value = 'error'
  } finally {
    releasingId.value = null
  }
}

const renderUserCharts = async () => {
  const { Chart } = await import('chart.js/auto')

  const usageCtx = document.getElementById('userUsageChart')
  const costCtx = document.getElementById('userCostChart')

  if (usageCtx) {
    new Chart(usageCtx, {
      type: 'bar',
      data: {
        labels: uAnalytics.value.lots,
        datasets: [{
          label: 'Reservations',
            data: uAnalytics.value.reservations_per_lot,
            backgroundColor: '#0d6efd'
        }]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    })
  }

  if (costCtx) {
    new Chart(costCtx, {
      type: 'bar',
      data: {
        labels: uAnalytics.value.lots,
        datasets: [{
          label: 'Cost (₹)',
          data: uAnalytics.value.cost_per_lot,
          backgroundColor: '#dc3545'
        }]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    })
  }
}

// Open modal using Bootstrap
const openProfileModal = () => {
  profileMessage.value = ''
  profileMessageType.value = 'success'
  const modalEl = document.getElementById('profileModal')
  if (!modalEl) return
  const modal = new window.bootstrap.Modal(modalEl)
  modal.show()
}

// Save profile
const saveProfile = async () => {
  profileSaving.value = true
  profileMessage.value = ''
  profileMessageType.value = 'success'
  try {
    await axios.put('http://localhost:5000/api/profile', profileForm.value, { headers: authHeader() })
    profileMessage.value = 'Profile updated'
    profileMessageType.value = 'success'
    sessionStorage.setItem('userFullName', profileForm.value.full_name)
    userFullName.value = profileForm.value.full_name
  } catch (e) {
    profileMessage.value = e?.response?.data?.message || 'Update failed'
    profileMessageType.value = 'error'
  } finally {
    profileSaving.value = false
  }
}

// Scroll to lots section
const scrollToLots = () => {
  const el = document.getElementById('lotsSection')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Logout
const logout = () => {
  sessionStorage.clear()
  localStorage.clear()
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

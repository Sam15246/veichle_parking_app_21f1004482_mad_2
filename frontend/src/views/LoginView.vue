<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h3 class="text-center">Login</h3>
          </div>
          <div class="card-body">
            <!-- Login Type Selector -->
            <div class="mb-3">
              <div class="btn-group w-100" role="group">
                <input type="radio" class="btn-check" id="userLogin" v-model="loginType" value="user" autocomplete="off">
                <label class="btn btn-outline-primary" for="userLogin">User Login</label>
                
                <input type="radio" class="btn-check" id="adminLogin" v-model="loginType" value="admin" autocomplete="off">
                <label class="btn btn-outline-danger" for="adminLogin">Admin Login</label>
              </div>
            </div>

            <!-- Alert Messages -->
            <div v-if="errorMessage" class="alert alert-danger" role="alert">
              {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success" role="alert">
              {{ successMessage }}
            </div>

            <!-- Login Form -->
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="username" 
                  v-model="credentials.username"
                  required 
                  autocomplete="username"
                >
              </div>
              
              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="password" 
                  v-model="credentials.password"
                  required
                  autocomplete="current-password"
                >
              </div>
              
              <button 
                type="submit" 
                class="btn w-100"
                :class="loginType === 'admin' ? 'btn-danger' : 'btn-primary'"
                :disabled="loading"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loginType === 'admin' ? 'Admin Login' : 'User Login' }}
              </button>
            </form>

            <!-- Register Link for Users -->
            <div v-if="loginType === 'user'" class="text-center mt-3">
              <p class="mb-0">Don't have an account? 
                <router-link to="/register" class="text-decoration-none">Register here</router-link>
              </p>
            </div>

            <!-- Demo Credentials -->
            <div class="mt-4 p-3 bg-light rounded">
              <h6>Demo Credentials:</h6>
              <div v-if="loginType === 'admin'">
                <strong>Admin:</strong> username: admin, password: admin123
              </div>
              <div v-else>
                <strong>User:</strong> username: user1, password: user123
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// Reactive data
const loginType = ref('user')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const credentials = ref({
  username: '',
  password: ''
})

// Check if user is already logged in
onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    const userRole = localStorage.getItem('userRole')
    redirectBasedOnRole(userRole)
  }
})

// Handle login
const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    // Determine API endpoint based on login type
    const endpoint = loginType.value === 'admin' 
      ? 'http://localhost:5000/api/admin/login'
      : 'http://localhost:5000/api/login'

    const response = await axios.post(endpoint, {
      username: credentials.value.username,
      password: credentials.value.password
    })

    // Store authentication data
    localStorage.setItem('token', response.data.token)
    localStorage.setItem('userId', response.data.user.id)
    localStorage.setItem('username', response.data.user.username)
    localStorage.setItem('userRole', response.data.user.role)
    localStorage.setItem('userFullName', response.data.user.full_name)

    successMessage.value = response.data.message

    // Redirect based on role
    setTimeout(() => {
      redirectBasedOnRole(response.data.user.role)
    }, 1000)

  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message
    } else {
      errorMessage.value = 'Login failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

// Role-based redirect
const redirectBasedOnRole = (role) => {
  if (role === 'admin') {
    router.push('/admin/dashboard')
  } else {
    router.push('/user/dashboard')
  }
}

// Clear form
const clearForm = () => {
  credentials.value.username = ''
  credentials.value.password = ''
  errorMessage.value = ''
  successMessage.value = ''
}

// Watch login type change to clear form
watch(loginType, () => {
  clearForm()
})
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.btn-check:checked + .btn-outline-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: white;
}

.btn-check:checked + .btn-outline-danger {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}
</style>

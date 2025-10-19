<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header">
            <h3 class="text-center">User Registration</h3>
            <p class="text-center text-muted mb-0">Create your parking account</p>
          </div>
          <div class="card-body">
            <!-- Alert Messages -->
            <div v-if="errorMessage" class="alert alert-danger" role="alert">
              {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success" role="alert">
              {{ successMessage }}
            </div>

            <!-- Registration Form -->
            <form @submit.prevent="handleRegister">
              <div class="row">
                <!-- Username -->
                <div class="col-md-6 mb-3">
                  <label for="username" class="form-label">Username *</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="username" 
                    v-model="formData.username"
                    required
                    autocomplete="username"
                  >
                </div>

                <!-- Email -->
                <div class="col-md-6 mb-3">
                  <label for="email" class="form-label">Email *</label>
                  <input 
                    type="email" 
                    class="form-control" 
                    id="email" 
                    v-model="formData.email"
                    required
                    autocomplete="email"
                  >
                </div>
              </div>

              <div class="row">
                <!-- Full Name -->
                <div class="col-md-6 mb-3">
                  <label for="fullName" class="form-label">Full Name *</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="fullName" 
                    v-model="formData.full_name"
                    required
                    autocomplete="name"
                  >
                </div>

                <!-- Phone -->
                <div class="col-md-6 mb-3">
                  <label for="phone" class="form-label">Phone Number</label>
                  <input 
                    type="tel" 
                    class="form-control" 
                    id="phone" 
                    v-model="formData.phone"
                    autocomplete="tel"
                  >
                </div>
              </div>

              <!-- Password -->
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="password" class="form-label">Password *</label>
                  <input 
                    type="password" 
                    class="form-control" 
                    id="password" 
                    v-model="formData.password"
                    required
                    autocomplete="new-password"
                  >
                </div>

                <!-- Confirm Password -->
                <div class="col-md-6 mb-3">
                  <label for="confirmPassword" class="form-label">Confirm Password *</label>
                  <input 
                    type="password" 
                    class="form-control" 
                    id="confirmPassword" 
                    v-model="confirmPassword"
                    required
                    autocomplete="new-password"
                  >
                </div>
              </div>

              <!-- Address -->
              <div class="mb-3">
                <label for="address" class="form-label">Address</label>
                <textarea 
                  class="form-control" 
                  id="address" 
                  rows="2"
                  v-model="formData.address"
                  autocomplete="street-address"
                ></textarea>
              </div>

              <!-- Pin Code -->
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="pinCode" class="form-label">Pin Code</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="pinCode" 
                    v-model="formData.pin_code"
                    autocomplete="postal-code"
                  >
                </div>
              </div>

              <!-- Submit Button -->
              <button 
                type="submit" 
                class="btn btn-primary w-100"
                :disabled="loading || !isPasswordMatch"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                Register Account
              </button>

              <!-- Password Match Warning -->
              <div v-if="!isPasswordMatch && confirmPassword" class="text-danger mt-2">
                <small>Passwords do not match</small>
              </div>
            </form>

            <!-- Login Link -->
            <div class="text-center mt-3">
              <p class="mb-0">Already have an account? 
                <router-link to="/login" class="text-decoration-none">Login here</router-link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// Reactive data
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const confirmPassword = ref('')

const formData = ref({
  username: '',
  email: '',
  full_name: '',
  phone: '',
  password: '',
  address: '',
  pin_code: ''
})

// Computed property for password matching
const isPasswordMatch = computed(() => {
  return formData.value.password === confirmPassword.value
})

// Handle registration
const handleRegister = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  // Check if passwords match
  if (!isPasswordMatch.value) {
    errorMessage.value = 'Passwords do not match'
    loading.value = false
    return
  }

  try {
    const response = await axios.post('http://localhost:5000/api/register', formData.value)
    
    successMessage.value = response.data.message + ' Redirecting to login...'
    
    // Clear form
    clearForm()
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)

  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message
    } else {
      errorMessage.value = 'Registration failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

// Clear form
const clearForm = () => {
  formData.value = {
    username: '',
    email: '',
    full_name: '',
    phone: '',
    password: '',
    address: '',
    pin_code: ''
  }
  confirmPassword.value = ''
}
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}
</style>

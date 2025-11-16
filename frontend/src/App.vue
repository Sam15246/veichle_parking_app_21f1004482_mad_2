<script setup>
import { onMounted, ref } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from '@/components/NavBar.vue'

// Authentication state using Composition API (no Pinia)
const isLoggedIn = ref(false)
const userRole = ref('')
const username = ref('')

// Initialize authentication on app start
onMounted(() => {
  initializeAuth()
})

const initializeAuth = () => {
  // Migrate once from localStorage if sessionStorage is empty
  if (!sessionStorage.getItem('token') && localStorage.getItem('token')) {
    const keys = ['token', 'userRole', 'userId', 'username', 'userFullName']
    keys.forEach(k => {
      const v = localStorage.getItem(k)
      if (v) sessionStorage.setItem(k, v)
    })
  }
  const token = sessionStorage.getItem('token')
  const role = sessionStorage.getItem('userRole')
  const user = sessionStorage.getItem('username')

  if (token && role && user) {
    isLoggedIn.value = true
    userRole.value = role
    username.value = user
  } else {
    isLoggedIn.value = false
    userRole.value = ''
    username.value = ''
  }
}
</script>

<template>
  <div id="app">
    <!-- Navigation Bar -->
    <NavBar />
    
    <!-- Main Content Area -->
    <main>
      <RouterView />
    </main>
    
    <!-- Footer -->
    <footer class="bg-dark text-white text-center py-3 mt-5">
      <div class="container">
        <p class="mb-0">
          <i class="bi bi-car-front"></i>
          Vehicle Parking System &copy; 2025 | Built with Vue.js & Flask
        </p>
      </div>
    </footer>
  </div>
</template>

<style>
/* Global styles */
body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f8f9fa;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  padding-top: 2rem;
}

/* Custom Bootstrap overrides */
.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.card:hover {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.15s ease-in-out;
}

/* Loading spinner */
.loading-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: #007bff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Alert styles */
.alert {
  border-radius: 0.5rem;
}

/* Responsive utilities */
@media (max-width: 768px) {
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>

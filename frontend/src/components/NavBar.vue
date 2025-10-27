<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
      <router-link class="navbar-brand" to="/">VPS</router-link>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navContent"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div id="navContent" class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/">Home</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/about">About</router-link>
          </li>
        </ul>
        <ul class="navbar-nav ms-auto">
          <li v-if="!isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/login">Login</router-link>
          </li>
          <li v-if="!isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/register">Register</router-link>
          </li>
          <li v-else class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
              <i class="bi bi-person-circle me-1"></i>{{ username }}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li v-if="userRole==='admin'">
                <router-link class="dropdown-item" to="/admin/dashboard">Admin Dashboard</router-link>
              </li>
              <li v-else>
                <router-link class="dropdown-item" to="/user/dashboard">User Dashboard</router-link>
              </li>
              <li><hr class="dropdown-divider" /></li>
              <li><a class="dropdown-item" href="#" @click.prevent="logout">Logout</a></li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoggedIn = ref(false)
const userRole = ref('')
const username = ref('')

const init = () => {
  const token = localStorage.getItem('token')
  userRole.value = localStorage.getItem('userRole') || ''
  username.value = localStorage.getItem('username') || ''
  isLoggedIn.value = !!token
}
onMounted(init)

const logout = () => {
  localStorage.clear()
  init()
  router.push('/login')
}
</script>

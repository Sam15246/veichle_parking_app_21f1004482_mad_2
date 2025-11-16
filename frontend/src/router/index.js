import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import UserDashboard from '../views/UserDashboard.vue'

// Helper: per-tab auth with safe migration from localStorage
function getAuth() {
  let token = sessionStorage.getItem('token')
  let userRole = sessionStorage.getItem('userRole')
  if (!token) {
    const lt = localStorage.getItem('token')
    const lr = localStorage.getItem('userRole')
    const uid = localStorage.getItem('userId')
    const un = localStorage.getItem('username')
    const fn = localStorage.getItem('userFullName')
    if (lt) sessionStorage.setItem('token', lt)
    if (lr) sessionStorage.setItem('userRole', lr)
    if (uid) sessionStorage.setItem('userId', uid)
    if (un) sessionStorage.setItem('username', un)
    if (fn) sessionStorage.setItem('userFullName', fn)
    token = lt
    userRole = lr
  }
  return { token, userRole }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/user/dashboard',
      name: 'user-dashboard',
      component: UserDashboard,
      meta: { requiresAuth: true, role: 'user' }
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue')
    }
  ]
})

// Navigation guards for authentication (sessionStorage first)
router.beforeEach((to) => {
  const { token, userRole } = getAuth()

  if (to.meta.requiresAuth) {
    if (!token) return '/login'
    if (to.meta.role && to.meta.role !== userRole) {
      return userRole === 'admin' ? '/admin/dashboard' : '/user/dashboard'
    }
  }

  if (token && (to.name === 'login' || to.name === 'register')) {
    return userRole === 'admin' ? '/admin/dashboard' : '/user/dashboard'
  }

  return true
})

export default router

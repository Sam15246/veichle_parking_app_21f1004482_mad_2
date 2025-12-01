import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import UserDashboard from '../views/UserDashboard.vue'

// Helper: per-tab auth (read sessionStorage first, fallback to localStorage)
function getAuth() {
  const token = sessionStorage.getItem('token') || localStorage.getItem('token')
  const userRole = sessionStorage.getItem('userRole') || localStorage.getItem('userRole')
  return { token, userRole }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/user/dashboard',
      name: 'user-dashboard',
      component: UserDashboard,
      meta: { requiresAuth: true, role: 'user' },
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
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

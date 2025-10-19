import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import UserDashboard from '../views/UserDashboard.vue'

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

// Navigation guards for authentication
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!token) {
      return '/login'
    }

    // Check role-based access
    if (to.meta.role && to.meta.role !== userRole) {
      // Redirect to appropriate dashboard based on user role
      if (userRole === 'admin') {
        return '/admin/dashboard'
      } else {
        return '/user/dashboard'
      }
    }
  }

  // Redirect authenticated users away from login/register pages
  if (token && (to.name === 'login' || to.name === 'register')) {
    if (userRole === 'admin') {
      return '/admin/dashboard'
    } else {
      return '/user/dashboard'
    }
  }

  return true
})

export default router

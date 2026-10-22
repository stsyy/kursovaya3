import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from './pages/LoginPage.vue'
import MainLayout from './pages/MainLayout.vue'
import SchedulePage from './pages/SchedulePage.vue'
import AppointmentsPage from './pages/AppointmentsPage.vue'
import AvailabilityPage from './pages/AvailabilityPage.vue'
import DoctorsPage from './pages/DoctorsPage.vue'
import RoomsPage from './pages/RoomsPage.vue'
import AccountsPage from './pages/AccountsPage.vue'
import ReschedulePage from './pages/ReschedulePage.vue'

const routes = [
  { path: '/login', component: LoginPage, meta: { public: true } },
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/schedule' },
      { path: 'schedule', component: SchedulePage, meta: { title: 'Расписание' } },
      { path: 'appointments', component: AppointmentsPage, meta: { title: 'Записи пациентов' } },
      { path: 'availability', component: AvailabilityPage, meta: { title: 'Доступность врачей' } },
      { path: 'reschedule', component: ReschedulePage, meta: { title: 'Перенос записей' } },
      { path: 'doctors', component: DoctorsPage, meta: { title: 'Врачи' } },
      { path: 'rooms', component: RoomsPage, meta: { title: 'Кабинеты' } },
      { path: 'accounts', component: AccountsPage, meta: { title: 'Учётные записи' } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (!to.meta.public && !sessionStorage.getItem('token')) return '/login'
})

export default router

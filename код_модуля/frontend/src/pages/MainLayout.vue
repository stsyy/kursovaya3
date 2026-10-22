<template>
  <div class="layout">
    <NavBar :current-user="currentUser" @logout="logout" />
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import api from '../api'

const router = useRouter()
const currentUser = sessionStorage.getItem('fullName') || ''

async function logout() {
  try { await api.post('auth/logout/') } catch { /* сеанс уже завершён */ }
  sessionStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
main { flex: 1; padding: 24px 28px; overflow-x: auto; }
</style>

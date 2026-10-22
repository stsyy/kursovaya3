<template>
  <div class="login-wrap">
    <form class="login-card" @submit.prevent="submit">
      <h1>Модуль администратора</h1>
      <p class="muted">Врачебно-физкультурный диспансер</p>
      <label>Логин <input v-model.trim="login" name="login" autocomplete="username" required /></label>
      <label>Пароль <input v-model="password" name="password" type="password" autocomplete="current-password" required /></label>
      <div v-if="errorMessage" class="error" data-test="login-error">{{ errorMessage }}</div>
      <button class="primary" type="submit" :disabled="loading">Войти</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorText } from '../api'

const router = useRouter()
const login = ref('')
const password = ref('')
const errorMessage = ref('')
const loading = ref(false)

async function submit() {
  errorMessage.value = ''
  loading.value = true
  try {
    const { data } = await api.post('auth/login/', { login: login.value, password: password.value })
    if (data.role === 'doctor') {
      // врач работает в модуле ведения приёма
      window.location.href = data.redirect
      return
    }
    sessionStorage.setItem('token', data.token)
    sessionStorage.setItem('fullName', data.full_name)
    router.push('/schedule')
  } catch (e) {
    showError(errorText(e))
  } finally {
    loading.value = false
  }
}

function showError(text) {
  errorMessage.value = text
}
</script>

<style scoped>
.login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.login-card { background: #fff; padding: 32px; border-radius: 12px; width: 360px; display: grid; gap: 14px; box-shadow: 0 6px 24px rgba(0,0,0,.08); }
.login-card h1 { margin: 0; }
.login-card p { margin: -8px 0 4px; }
</style>

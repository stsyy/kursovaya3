<template>
  <nav>
    <div class="brand">Модуль администратора</div>
    <router-link v-for="item in items" :key="item.route" :to="item.route">{{ item.title }}</router-link>
    <div class="user">
      <div>{{ currentUser }}</div>
      <button @click="$emit('logout')">Выйти</button>
    </div>
  </nav>
</template>

<script setup>
defineProps({ currentUser: String })
defineEmits(['logout'])

const items = [
  { route: '/schedule', title: 'Расписание' },
  { route: '/appointments', title: 'Записи пациентов' },
  { route: '/availability', title: 'Доступность врачей' },
  { route: '/reschedule', title: 'Перенос записей' },
  { route: '/doctors', title: 'Врачи' },
  { route: '/rooms', title: 'Кабинеты' },
  { route: '/accounts', title: 'Учётные записи' },
]
</script>

<style scoped>
nav { width: 220px; background: #1b2b45; color: #cfd8e3; display: flex; flex-direction: column; padding: 18px 0; flex-shrink: 0; }
.brand { font-weight: 600; color: #fff; padding: 0 20px 18px; font-size: 15px; }
a { color: #cfd8e3; text-decoration: none; padding: 10px 20px; }
a:hover { background: #24395a; }
a.router-link-active { background: #1e6fd9; color: #fff; }
.user { margin-top: auto; padding: 16px 20px 0; font-size: 13px; display: grid; gap: 8px; }
</style>

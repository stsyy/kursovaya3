<template>
  <section>
    <h1>Учётные записи</h1>
    <div class="toolbar"><button class="primary" @click="openCreate">Создать</button></div>
    <div v-if="message" class="info">{{ message }}</div>
    <div v-if="error" class="error">{{ error }}</div>
    <table>
      <thead><tr><th>ФИО</th><th>Логин</th><th>Роль</th><th>Телефон</th><th>Состояние</th><th></th></tr></thead>
      <tbody>
        <tr v-for="a in accounts" :key="a.id">
          <td>{{ a.full_name }}</td><td>{{ a.login }}</td><td>{{ roles[a.role] }}</td><td>{{ a.phone }}</td>
          <td><span :class="['badge', a.state === 'active' ? 'active' : 'blocked']">{{ a.state === 'active' ? 'активна' : 'заблокирована' }}</span></td>
          <td><div class="actions">
            <button @click="openEdit(a)">Изменить</button>
            <button v-if="a.state === 'active'" @click="block(a)">Заблокировать</button>
            <button v-else @click="unblock(a)">Разблокировать</button>
            <button @click="resetPassword(a)">Сбросить пароль</button>
            <button class="danger" @click="toRemove = a">Удалить</button>
          </div></td>
        </tr>
      </tbody>
    </table>
    <AccountForm v-if="editing" :account="editing" @saved="onSaved" @cancel="editing = null" />
    <ConfirmDialog v-if="toRemove" :message="`Удалить учётную запись ${toRemove.full_name}?`"
                   @confirm="remove" @cancel="toRemove = null" />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api, { errorText } from '../api'
import AccountForm from '../components/AccountForm.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const roles = { admin: 'Администратор', doctor: 'Врач' }
const accounts = ref([])
const editing = ref(null)
const toRemove = ref(null)
const error = ref('')
const message = ref('')

async function load() { accounts.value = (await api.get('accounts/')).data }
function openCreate() { editing.value = {} }
function openEdit(a) { editing.value = a }
function onSaved() { editing.value = null; load() }

async function run(fn) {
  error.value = ''; message.value = ''
  try { await fn(); await load() } catch (e) { error.value = errorText(e) }
}
const block = (a) => run(() => api.post(`accounts/${a.id}/block/`))
const unblock = (a) => run(() => api.post(`accounts/${a.id}/unblock/`))
const resetPassword = (a) => run(async () => {
  const { data } = await api.post(`accounts/${a.id}/reset-password/`)
  message.value = `Временный пароль для ${a.full_name}: ${data.temp_password}`
})
const remove = () => run(async () => { const a = toRemove.value; toRemove.value = null; await api.delete(`accounts/${a.id}/`) })

onMounted(load)
</script>

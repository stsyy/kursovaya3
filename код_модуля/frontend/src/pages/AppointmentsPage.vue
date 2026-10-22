<template>
  <section>
    <h1>Записи пациентов</h1>
    <div class="toolbar">
      <label>Врач <select v-model="filters.doctor"><option :value="null">Все врачи</option>
        <option v-for="d in doctors" :key="d.id" :value="d.id">{{ d.full_name }}</option></select></label>
      <label>Дата <input v-model="filters.date" type="date" /></label>
      <label>Статус <select v-model="filters.status"><option :value="null">Все</option>
        <option value="active">активна</option><option value="pending">ожидает кода из SMS</option>
        <option value="moved">перенесена</option><option value="cancelled">отменена</option></select></label>
      <label>Способ записи <select v-model="filters.channel"><option :value="null">Все</option>
        <option value="registry">регистратура</option><option value="online">форма онлайн-записи</option></select></label>
      <label>Телефон <input v-model.trim="filters.phone" placeholder="+7…" /></label>
      <button @click="applyFilter">Найти</button>
      <button class="primary" @click="showForm = true">Новая запись</button>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="message" class="info">{{ message }}</div>
    <table>
      <thead><tr><th>Дата</th><th>Время</th><th>Пациент</th><th>Телефон</th><th>Врач</th><th>Кабинет</th><th>Способ записи</th><th>Статус</th><th></th></tr></thead>
      <tbody>
        <tr v-for="a in appointments" :key="a.id">
          <td>{{ fmtDate(a.date) }}</td><td>{{ fmtTime(a.start_time) }}</td><td>{{ a.patient_name }}</td>
          <td>{{ a.patient_phone }}</td><td>{{ a.doctor_name }}</td><td>{{ a.room_number }}</td>
          <td>{{ a.channel_display }}</td>
          <td><span :class="['badge', a.status]">{{ a.status_display }}</span></td>
          <td v-if="a.status === 'active' || a.status === 'pending'"><div class="actions">
            <button @click="reschedule(a)">Перенести</button>
            <button class="danger" @click="toCancel = a">Отменить</button></div></td><td v-else></td>
        </tr>
        <tr v-if="!appointments.length"><td colspan="9" class="muted">Записей не найдено</td></tr>
      </tbody>
    </table>
    <AppointmentForm v-if="showForm" @saved="onSaved" @cancel="showForm = false" />
    <ConfirmDialog v-if="toCancel" :message="`Отменить запись ${toCancel.patient_name} на ${fmtDate(toCancel.date)} ${fmtTime(toCancel.start_time)}? Пациенту будет отправлено SMS.`"
                   @confirm="cancelAppointment" @cancel="toCancel = null" />
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorText, fmtDate, fmtTime } from '../api'
import AppointmentForm from '../components/AppointmentForm.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const filters = reactive({ doctor: null, date: '', status: null, channel: null, phone: '' })
const appointments = ref([]); const doctors = ref([])
const showForm = ref(false); const toCancel = ref(null); const error = ref(''); const message = ref('')

async function applyFilter() {
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
  appointments.value = (await api.get('appointments/', { params })).data
}
function onSaved(a) { showForm.value = false; message.value = `Пациент ${a.patient_name} записан на ${fmtDate(a.date)} ${fmtTime(a.start_time)}.`; applyFilter() }
function reschedule(a) { router.push({ path: '/reschedule', query: { appointment: a.id } }) }
async function cancelAppointment() {
  error.value = ''; message.value = ''
  try { await api.post(`appointments/${toCancel.value.id}/cancel/`); message.value = 'Запись отменена, пациенту отправлено SMS-уведомление.' }
  catch (e) { error.value = errorText(e) }
  toCancel.value = null; applyFilter()
}
onMounted(async () => { doctors.value = (await api.get('doctors/')).data; applyFilter() })
</script>

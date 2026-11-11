<template>
  <section>
    <h1>Перенос записей</h1>
    <div v-if="message" class="info" data-test="move-result">{{ message }}</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid">
      <div>
        <h3>Записи для переноса</h3>
        <table>
          <thead><tr><th>Пациент</th><th>Телефон</th><th>Исходный приём</th><th>Врач</th></tr></thead>
          <tbody>
            <tr v-for="a in affected" :key="a.id" :class="{ selected: current?.id === a.id }" @click="loadProposals(a)">
              <td>{{ a.patient_name }}</td><td>{{ a.patient_phone }}</td>
              <td>{{ fmtDate(a.date) }} {{ fmtTime(a.start_time) }}</td><td>{{ a.doctor_name }}<br><span class="muted">{{ a.specialization }}</span></td>
            </tr>
            <tr v-if="!affected.length"><td colspan="4" class="muted">Записей, требующих переноса, нет</td></tr>
          </tbody>
        </table>
      </div>
      <div>
        <h3>Предложенные слоты <span v-if="current" class="muted">для {{ current.patient_name }}</span></h3>
        <table v-if="current">
          <thead><tr><th>Дата и время</th><th>Врач</th><th>Кабинет</th><th></th></tr></thead>
          <tbody>
            <tr v-for="s in proposedSlots" :key="s.id">
              <td>{{ fmtDate(s.date) }} {{ fmtTime(s.start_time) }}</td><td>{{ s.doctor_name }}<br><span class="muted">{{ s.specialization_name }}</span></td><td>{{ s.room_number }}</td>
              <td><button class="primary" @click="confirmMove(current, s)">Перенести</button></td>
            </tr>
            <tr v-if="!proposedSlots.length"><td colspan="4" class="muted">Свободных слотов врачей той же специализации нет</td></tr>
          </tbody>
        </table>
        <p v-else class="muted">Выберите запись слева, чтобы подобрать слоты.</p>
        <button v-if="current" class="danger" @click="toCancel = current">Отменить запись</button>
      </div>
    </div>
    <ConfirmDialog v-if="toCancel" :message="`Подходящего слота нет? Отменить запись ${toCancel.patient_name}? Пациенту будет отправлено SMS.`"
                   @confirm="cancelAppointment" @cancel="toCancel = null" />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api, { errorText, fmtDate, fmtTime } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const route = useRoute()
const affected = ref([]); const proposedSlots = ref([]); const current = ref(null)
const toCancel = ref(null); const message = ref(''); const error = ref('')

async function load() {
  if (route.query.appointment) {
    const { data } = await api.get(`appointments/${route.query.appointment}/`)
    affected.value = ['active', 'pending'].includes(data.status) ? [data] : []
  } else {
    affected.value = (await api.get('appointments/affected/')).data
  }
  current.value = null
  if (affected.value.length) loadProposals(affected.value[0])
}

async function loadProposals(a) {
  current.value = a
  proposedSlots.value = (await api.get(`appointments/${a.id}/proposals/`)).data
}

async function confirmMove(a, s) {
  error.value = ''; message.value = ''
  try {
    await api.post(`appointments/${a.id}/reschedule/`, { slot: s.id })
    message.value = `Запись ${a.patient_name} перенесена на ${fmtDate(s.date)} ${fmtTime(s.start_time)} к врачу ${s.doctor_name}. SMS-уведомление отправлено.`
    if (route.query.appointment) affected.value = []
    else await load()
    if (!affected.value.length) current.value = null
  } catch (e) { error.value = errorText(e); loadProposals(a) }
}

async function cancelAppointment() {
  const a = toCancel.value; toCancel.value = null
  try {
    await api.post(`appointments/${a.id}/cancel/`)
    message.value = `Запись ${a.patient_name} отменена. SMS-уведомление отправлено.`
    if (route.query.appointment) { affected.value = []; current.value = null } else await load()
  } catch (e) { error.value = errorText(e) }
}

onMounted(load)
</script>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
h3 { font-size: 15px; margin: 0 0 8px; }
tbody tr { cursor: pointer; }
.danger { margin-top: 12px; }
</style>

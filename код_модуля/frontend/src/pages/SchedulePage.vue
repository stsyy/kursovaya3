<template>
  <section>
    <h1>Расписание</h1>
    <div class="toolbar">
      <label>Врач <select v-model="doctorFilter"><option :value="null">Все врачи</option>
        <option v-for="d in doctors" :key="d.id" :value="d.id">{{ d.full_name }}</option></select></label>
      <label>Кабинет <select v-model="roomFilter"><option :value="null">Все кабинеты</option>
        <option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.number }}</option></select></label>
      <label>С <input v-model="dateFrom" type="date" /></label>
      <label>По <input v-model="dateTo" type="date" /></label>
      <button @click="applyFilter">Показать</button>
      <button class="primary" @click="openShiftForm()">Создать смену</button>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="affectedCount" class="info">
      Затронуто записей пациентов: {{ affectedCount }}.
      <router-link to="/reschedule">Перейти к переносу записей</router-link>
    </div>
    <p class="legend"><span class="badge free">свободен</span> <span class="badge busy">занят</span>
      <span class="badge blocked">заблокирован</span> <span class="muted">— нажмите на свободный или занятый слот, чтобы заблокировать его</span></p>
    <table>
      <thead><tr><th>Дата</th><th>Врач</th><th>Кабинет</th><th>Время</th><th>Слоты</th><th></th></tr></thead>
      <tbody>
        <tr v-for="s in shifts" :key="s.id">
          <td>{{ fmtDate(s.date) }}</td><td>{{ s.doctor_name }}</td><td>{{ s.room_number }}</td>
          <td>{{ fmtTime(s.start_time) }}–{{ fmtTime(s.end_time) }}</td>
          <td class="slots">
            <span v-for="sl in s.slots" :key="sl.id" :class="['badge', 'slot', sl.status]" :title="sl.status_display"
                  @click="sl.status !== 'blocked' && (slotToBlock = sl)">{{ fmtTime(sl.start_time) }}</span>
          </td>
          <td><div class="actions"><button @click="editShift(s)">Изменить</button>
            <button class="danger" @click="deleteShift(s)">Удалить</button></div></td>
        </tr>
        <tr v-if="!shifts.length"><td colspan="6" class="muted">Смен за выбранный период нет</td></tr>
      </tbody>
    </table>
    <ShiftForm v-if="editing" :shift="editing" :doctors="doctors" :rooms="rooms"
               @saved="onSaved" @cancel="editing = null" />
    <ConfirmDialog v-if="slotToBlock" :message="`Заблокировать слот ${fmtDate(slotToBlock.date)} ${fmtTime(slotToBlock.start_time)}?`"
                   @confirm="blockSlot" @cancel="slotToBlock = null" />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api, { errorText, fmtDate, fmtTime } from '../api'
import ShiftForm from '../components/ShiftForm.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const iso = (d) => d.toISOString().slice(0, 10)
const doctors = ref([]); const rooms = ref([]); const shifts = ref([])
const doctorFilter = ref(null); const roomFilter = ref(null)
const dateFrom = ref(iso(new Date())); const dateTo = ref(iso(new Date(Date.now() + 7 * 864e5)))
const editing = ref(null); const slotToBlock = ref(null)
const error = ref(''); const affectedCount = ref(0)

async function applyFilter() {
  const params = { date_from: dateFrom.value, date_to: dateTo.value }
  if (doctorFilter.value) params.doctor = doctorFilter.value
  if (roomFilter.value) params.room = roomFilter.value
  shifts.value = (await api.get('shifts/', { params })).data
}
function openShiftForm() { editing.value = {} }
function editShift(s) { editing.value = s }
function onSaved(affected) { editing.value = null; affectedCount.value = affected?.length || 0; applyFilter() }

async function deleteShift(s) {
  error.value = ''; affectedCount.value = 0
  try { await api.delete(`shifts/${s.id}/`) } catch (e) {
    error.value = errorText(e); affectedCount.value = e.response?.data?.affected?.length || 0
  }
  applyFilter()
}
async function blockSlot() {
  const { data } = await api.post(`slots/${slotToBlock.value.id}/block/`)
  slotToBlock.value = null; affectedCount.value = data.affected.length; applyFilter()
}

onMounted(async () => {
  doctors.value = (await api.get('doctors/')).data
  rooms.value = (await api.get('rooms/')).data
  applyFilter()
})
</script>

<style scoped>
.slots { display: flex; flex-wrap: wrap; gap: 4px; max-width: 520px; }
.slot { cursor: pointer; }
.legend { margin: 0 0 10px; }
</style>

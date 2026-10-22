<template>
  <div class="overlay">
    <form class="dialog wide" @submit.prevent="save">
      <h2>Запись пациента на приём</h2>
      <div class="fields">
        <div class="row2">
          <label>Телефон пациента <input v-model.trim="phone" name="phone" placeholder="+79XXXXXXXXX" required /></label>
          <button type="button" @click="findPatient">Найти</button>
        </div>
        <div v-if="patient" class="info" data-test="patient-found">Пациент: {{ patient.full_name }} ({{ patient.sport || 'вид спорта не указан' }})</div>
        <template v-else-if="searched">
          <div class="muted">Пациент не найден — введите данные нового пациента</div>
          <label>ФИО <input v-model.trim="newPatient.full_name" name="full_name" required /></label>
          <label>Вид спорта <input v-model.trim="newPatient.sport" name="sport" /></label>
        </template>
        <div class="row3">
          <label>Специализация <select v-model="specialization" @change="loadFreeSlots">
            <option v-for="s in specializations" :key="s.id" :value="s.id">{{ s.name }}</option></select></label>
          <label>Врач <select v-model="doctor" @change="loadFreeSlots"><option :value="null">Любой</option>
            <option v-for="d in doctorsOfSpec" :key="d.id" :value="d.id">{{ d.full_name }}</option></select></label>
          <label>Дата <input v-model="date" type="date" @change="loadFreeSlots" /></label>
        </div>
        <div class="slots">
          <span v-for="s in freeSlots" :key="s.id" :class="['badge', 'free', 'pick', { chosen: slot === s.id }]"
                @click="slot = s.id">{{ fmtDate(s.date) }} {{ fmtTime(s.start_time) }} · {{ s.doctor_name.split(' ')[0] }}</span>
          <span v-if="specialization && !freeSlots.length" class="muted">Свободных слотов нет</span>
        </div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="footer"><button type="button" @click="$emit('cancel')">Отмена</button>
        <button class="primary" type="submit" :disabled="!slot || !searched">Записать</button></div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api, { errorText, fmtDate, fmtTime } from '../api'

const emit = defineEmits(['saved', 'cancel'])
const phone = ref(''); const patient = ref(null); const searched = ref(false)
const newPatient = reactive({ full_name: '', sport: '' })
const specializations = ref([]); const doctors = ref([])
const specialization = ref(null); const doctor = ref(null); const date = ref('')
const freeSlots = ref([]); const slot = ref(null); const error = ref('')
const doctorsOfSpec = computed(() => doctors.value.filter((d) => d.specialization === specialization.value))

onMounted(async () => {
  const [specs, docs] = await Promise.all([api.get('specializations/'), api.get('doctors/')])
  doctors.value = docs.data
  specializations.value = specs.data
})

async function findPatient() {
  const { data } = await api.get('patients/', { params: { phone: phone.value } })
  patient.value = data[0] || null
  searched.value = true
}

async function loadFreeSlots() {
  slot.value = null
  const today = new Date().toISOString().slice(0, 10)
  const params = { status: 'free', date_from: date.value || today }
  if (date.value) params.date_to = date.value
  if (doctor.value) params.doctor = doctor.value
  const ids = new Set(doctorsOfSpec.value.map((d) => d.id))
  const { data } = await api.get('slots/', { params })
  freeSlots.value = data.filter((s) => ids.has(s.doctor)).slice(0, 40)
}

async function save() {
  error.value = ''
  try {
    let p = patient.value
    if (!p) p = (await api.post('patients/', { ...newPatient, phone: phone.value })).data
    const { data } = await api.post('appointments/', { patient: p.id, slot: slot.value })
    emit('saved', data)
  } catch (e) { error.value = errorText(e); loadFreeSlots() }
}
</script>

<style scoped>
.wide { width: 640px; }
.row2 { display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: end; }
.row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.slots { display: flex; flex-wrap: wrap; gap: 6px; max-height: 160px; overflow-y: auto; }
.pick { cursor: pointer; border: 1px solid transparent; }
.chosen { border-color: #1e7b3a; font-weight: 600; }
</style>

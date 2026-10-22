<template>
  <div class="overlay">
    <form class="dialog" @submit.prevent="save">
      <h2>{{ shift.id ? 'Изменение смены' : 'Новая рабочая смена' }}</h2>
      <div class="fields">
        <label>Врач <select v-model="form.doctor" :disabled="!!shift.id" required>
          <option v-for="d in doctors" :key="d.id" :value="d.id">{{ d.full_name }}</option></select></label>
        <label>Кабинет <select v-model="form.room" required>
          <option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.number }} ({{ r.building }})</option></select></label>
        <label>Дата <input v-model="form.date" type="date" :disabled="!!shift.id" required /></label>
        <div class="row">
          <label>Начало <input v-model="form.start_time" type="time" required /></label>
          <label>Окончание <input v-model="form.end_time" type="time" required /></label>
          <label>Слот, мин <input v-model.number="form.slot_minutes" type="number" min="5" step="5" :disabled="!!shift.id" required /></label>
        </div>
      </div>
      <div v-for="c in conflicts" :key="c" class="error" data-test="conflict">{{ c }}</div>
      <div class="footer"><button type="button" @click="$emit('cancel')">Отмена</button>
        <button class="primary" type="submit">Сохранить</button></div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import api, { errorText } from '../api'

const props = defineProps({ shift: Object, doctors: Array, rooms: Array })
const emit = defineEmits(['saved', 'cancel'])
const form = reactive({ doctor: null, room: null, date: '', start_time: '09:00', end_time: '13:00', slot_minutes: 30,
  ...props.shift })
const conflicts = ref([])

function showConflict(e) { conflicts.value = e.response?.data?.errors || [errorText(e)] }

async function save() {
  conflicts.value = []
  try {
    if (props.shift.id) {
      const { data } = await api.patch(`shifts/${props.shift.id}/`,
        { room: form.room, start_time: form.start_time, end_time: form.end_time })
      emit('saved', data.affected)
    } else {
      await api.post('shifts/', form)
      emit('saved', [])
    }
  } catch (e) { showConflict(e) }
}
</script>

<style scoped>
.row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
</style>

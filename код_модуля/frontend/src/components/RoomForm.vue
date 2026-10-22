<template>
  <div class="overlay">
    <form class="dialog" @submit.prevent="save">
      <h2>{{ room.id ? 'Изменение кабинета' : 'Новый кабинет' }}</h2>
      <div class="fields">
        <label>Номер <input v-model.trim="form.number" required /></label>
        <label>Этаж <input v-model.number="form.floor" type="number" min="0" required /></label>
        <label>Корпус <input v-model.trim="form.building" required /></label>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="footer"><button type="button" @click="$emit('cancel')">Отмена</button>
        <button class="primary" type="submit">Сохранить</button></div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import api, { errorText } from '../api'

const props = defineProps({ room: Object })
const emit = defineEmits(['saved', 'cancel'])
const form = reactive({ number: '', floor: 1, building: 'Главный', ...props.room })
const error = ref('')

async function save() {
  try {
    if (props.room.id) await api.patch(`rooms/${props.room.id}/`, form)
    else await api.post('rooms/', form)
    emit('saved')
  } catch (e) { error.value = errorText(e) }
}
</script>

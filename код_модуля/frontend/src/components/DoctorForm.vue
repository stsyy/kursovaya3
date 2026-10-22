<template>
  <div class="overlay">
    <form class="dialog" @submit.prevent="save">
      <h2>{{ doctor.id ? 'Изменение данных врача' : 'Новый врач' }}</h2>
      <div class="fields">
        <label>ФИО <input v-model.trim="form.full_name" required /></label>
        <label>Специализация
          <select v-model="form.specialization" required>
            <option v-for="s in specializations" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </label>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="footer"><button type="button" @click="$emit('cancel')">Отмена</button>
        <button class="primary" type="submit">Сохранить</button></div>
    </form>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api, { errorText } from '../api'

const props = defineProps({ doctor: Object })
const emit = defineEmits(['saved', 'cancel'])
const form = reactive({ full_name: '', specialization: null, ...props.doctor })
const specializations = ref([])
const error = ref('')

onMounted(async () => { specializations.value = (await api.get('specializations/')).data })

async function save() {
  const body = { full_name: form.full_name, specialization: form.specialization }
  try {
    if (props.doctor.id) await api.patch(`doctors/${props.doctor.id}/`, body)
    else await api.post('doctors/', body)
    emit('saved')
  } catch (e) { error.value = errorText(e) }
}
</script>

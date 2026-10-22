<template>
  <div class="overlay">
    <form class="dialog" @submit.prevent="save">
      <h2>{{ period.id ? 'Изменение периода недоступности' : 'Период недоступности врача' }}</h2>
      <div class="fields">
        <label>Врач <select v-model="form.doctor" :disabled="!!period.id" required>
          <option v-for="d in doctors" :key="d.id" :value="d.id">{{ d.full_name }}</option></select></label>
        <label>Причина <select v-model="form.reason" :disabled="!!period.id" required>
          <option value="illness">болезнь</option><option value="vacation">отпуск</option><option value="other">иное</option>
        </select></label>
        <label>Дата начала <input v-model="form.date_from" type="date" :disabled="!!period.id" required /></label>
        <label>Дата окончания <input v-model="form.date_to" type="date" required /></label>
      </div>
      <div v-if="error" class="error" data-test="period-error">{{ error }}</div>
      <div class="footer"><button type="button" @click="$emit('cancel')">Отмена</button>
        <button class="primary" type="submit">Сохранить</button></div>
    </form>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api, { errorText } from '../api'

const props = defineProps({ period: Object })
const emit = defineEmits(['saved', 'cancel'])
const form = reactive({ doctor: null, reason: 'illness', date_from: '', date_to: '', ...props.period })
const doctors = ref([]); const error = ref('')

onMounted(async () => { doctors.value = (await api.get('doctors/')).data })

async function save() {
  error.value = ''
  try {
    const { data } = props.period.id
      ? await api.patch(`unavailability/${props.period.id}/`, { date_to: form.date_to })
      : await api.post('unavailability/', form)
    emit('saved', data.affected)
  } catch (e) { error.value = errorText(e) }
}
</script>

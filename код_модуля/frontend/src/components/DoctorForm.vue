<template>
  <div class="overlay">
    <form class="dialog" @submit.prevent="save">
      <h2>{{ doctor.id ? 'Изменение данных врача' : 'Новый врач' }}</h2>
      <div class="fields">
        <!-- ФИО и телефон врача хранятся в учётной записи сотрудника с ролью «Врач» -->
        <label>Учётная запись врача
          <select v-model="form.account" :disabled="!!doctor.id" required>
            <option v-for="a in freeAccounts" :key="a.id" :value="a.id">{{ a.full_name }} ({{ a.login }})</option>
          </select>
        </label>
        <div v-if="!doctor.id && !freeAccounts.length" class="muted">
          Нет учётных записей с ролью «Врач» без привязки. Сначала создайте учётную запись врача.</div>
        <fieldset>
          <legend>Специализации</legend>
          <label v-for="s in specializations" :key="s.id" class="check">
            <input type="checkbox" :value="s.id" v-model="form.specializations" /> {{ s.name }}</label>
        </fieldset>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="footer"><button type="button" @click="$emit('cancel')">Отмена</button>
        <button class="primary" type="submit" :disabled="!form.specializations.length">Сохранить</button></div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api, { errorText } from '../api'

const props = defineProps({ doctor: Object, doctors: { type: Array, default: () => [] } })
const emit = defineEmits(['saved', 'cancel'])
const form = reactive({ account: null, ...props.doctor, specializations: [...(props.doctor.specializations || [])] })
const specializations = ref([]); const accounts = ref([])
const error = ref('')

// учётные записи врачей, ещё не привязанные к другому врачу
const freeAccounts = computed(() => {
  const used = new Set(props.doctors.filter((d) => d.id !== props.doctor.id).map((d) => d.account))
  return accounts.value.filter((a) => a.role === 'doctor' && !used.has(a.id))
})

onMounted(async () => {
  const [specs, accs] = await Promise.all([api.get('specializations/'), api.get('accounts/')])
  specializations.value = specs.data
  accounts.value = accs.data
})

async function save() {
  const body = { account: form.account, specializations: form.specializations }
  try {
    if (props.doctor.id) await api.patch(`doctors/${props.doctor.id}/`, { specializations: form.specializations })
    else await api.post('doctors/', body)
    emit('saved')
  } catch (e) { error.value = errorText(e) }
}
</script>

<style scoped>
fieldset { border: 1px solid #d0d7de; border-radius: 6px; padding: 8px 12px; }
.check { display: flex; flex-direction: row; align-items: center; gap: 6px; font-weight: normal; }
</style>

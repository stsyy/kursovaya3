<template>
  <section>
    <h1>Врачи</h1>
    <div class="toolbar"><button class="primary" @click="editing = {}">Добавить</button></div>
    <div v-if="error" class="error">{{ error }}</div>
    <table>
      <thead><tr><th>ФИО</th><th>Специализации</th><th>Статус доступности</th><th></th></tr></thead>
      <tbody>
        <tr v-for="d in doctors" :key="d.id">
          <td>{{ d.full_name }}</td><td>{{ d.specialization_names.join(', ') }}</td>
          <td><span :class="['badge', d.availability_status === 'доступен' ? 'active' : 'blocked']">{{ d.availability_status }}</span></td>
          <td><div class="actions"><button @click="editing = d">Изменить</button>
            <button class="danger" @click="remove(d)">Удалить</button></div></td>
        </tr>
      </tbody>
    </table>
    <DoctorForm v-if="editing" :doctor="editing" :doctors="doctors" @saved="editing = null; load()" @cancel="editing = null" />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api, { errorText } from '../api'
import DoctorForm from '../components/DoctorForm.vue'

const doctors = ref([])
const editing = ref(null)
const error = ref('')

async function load() { doctors.value = (await api.get('doctors/')).data }
async function remove(d) {
  error.value = ''
  try { await api.delete(`doctors/${d.id}/`); load() } catch (e) { error.value = errorText(e) }
}
onMounted(load)
</script>

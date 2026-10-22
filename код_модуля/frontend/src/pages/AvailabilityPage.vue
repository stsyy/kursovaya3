<template>
  <section>
    <h1>Доступность врачей</h1>
    <div class="toolbar"><button class="primary" @click="openPeriodForm()">Установить период</button></div>
    <div v-if="error" class="error">{{ error }}</div>
    <table>
      <thead><tr><th>Врач</th><th>Причина</th><th>Дата начала</th><th>Дата окончания</th><th></th></tr></thead>
      <tbody>
        <tr v-for="p in periods" :key="p.id">
          <td>{{ p.doctor_name }}</td><td>{{ p.reason_display }}</td>
          <td>{{ fmtDate(p.date_from) }}</td><td>{{ fmtDate(p.date_to) }}</td>
          <td><div class="actions"><button @click="openPeriodForm(p)">Изменить дату окончания</button>
            <button class="danger" @click="toRemove = p">Снять период</button></div></td>
        </tr>
        <tr v-if="!periods.length"><td colspan="5" class="muted">Периодов недоступности нет</td></tr>
      </tbody>
    </table>
    <PeriodForm v-if="editing" :period="editing" @saved="onSaved" @cancel="editing = null" />
    <ConfirmDialog v-if="toRemove" :message="`Снять период недоступности врача ${toRemove.doctor_name}? Слоты врача будут разблокированы.`"
                   @confirm="removePeriod" @cancel="toRemove = null" />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorText, fmtDate } from '../api'
import PeriodForm from '../components/PeriodForm.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const periods = ref([]); const editing = ref(null); const toRemove = ref(null); const error = ref('')

async function load() { periods.value = (await api.get('unavailability/')).data }
function openPeriodForm(p = {}) { editing.value = p }
function onSaved(affected) {
  editing.value = null
  // есть затронутые записи – сразу открываем перенос (процесс 5.3 → 6.2)
  if (affected?.length) router.push('/reschedule')
  else load()
}
async function removePeriod() {
  try { await api.delete(`unavailability/${toRemove.value.id}/`) } catch (e) { error.value = errorText(e) }
  toRemove.value = null; load()
}
onMounted(load)
</script>

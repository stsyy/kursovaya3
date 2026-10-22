<template>
  <section>
    <h1>Кабинеты</h1>
    <div class="toolbar"><button class="primary" @click="editing = {}">Добавить</button></div>
    <div v-if="error" class="error">{{ error }}</div>
    <table>
      <thead><tr><th>Номер</th><th>Этаж</th><th>Корпус</th><th></th></tr></thead>
      <tbody>
        <tr v-for="r in rooms" :key="r.id">
          <td>{{ r.number }}</td><td>{{ r.floor }}</td><td>{{ r.building }}</td>
          <td><div class="actions"><button @click="editing = r">Изменить</button>
            <button class="danger" @click="remove(r)">Удалить</button></div></td>
        </tr>
      </tbody>
    </table>
    <RoomForm v-if="editing" :room="editing" @saved="editing = null; load()" @cancel="editing = null" />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api, { errorText } from '../api'
import RoomForm from '../components/RoomForm.vue'

const rooms = ref([])
const editing = ref(null)
const error = ref('')

async function load() { rooms.value = (await api.get('rooms/')).data }
async function remove(r) {
  error.value = ''
  try { await api.delete(`rooms/${r.id}/`); load() } catch (e) { error.value = errorText(e) }
}
onMounted(load)
</script>

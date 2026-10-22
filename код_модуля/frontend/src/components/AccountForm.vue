<template>
  <div class="overlay">
    <form class="dialog" @submit.prevent="save">
      <h2>{{ account.id ? 'Изменение учётной записи' : 'Новая учётная запись' }}</h2>
      <div class="fields">
        <label>ФИО <input v-model.trim="form.full_name" required /></label>
        <label>Логин <input v-model.trim="form.login" required /></label>
        <label>{{ account.id ? 'Новый пароль (необязательно)' : 'Временный пароль' }}
          <input v-model="form.password" type="password" minlength="8" :required="!account.id" /></label>
        <label>Роль
          <select v-model="form.role" required>
            <option value="admin">Администратор</option><option value="doctor">Врач</option>
          </select>
        </label>
        <label>Телефон <input v-model.trim="form.phone" placeholder="+7XXXXXXXXXX" /></label>
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

const props = defineProps({ account: Object })
const emit = defineEmits(['saved', 'cancel'])
const form = reactive({ full_name: '', login: '', password: '', role: 'doctor', phone: '', ...props.account })
const error = ref('')

async function save() {
  const body = { ...form }
  if (!body.password) delete body.password
  try {
    if (props.account.id) await api.patch(`accounts/${props.account.id}/`, body)
    else await api.post('accounts/', body)
    emit('saved')
  } catch (e) { error.value = errorText(e) }
}
</script>

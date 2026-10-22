<template>
  <div class="overlay">
    <div class="dialog">
      <h2>Подтверждение</h2>
      <p>{{ message }}</p>
      <div class="footer">
        <button @click="$emit('cancel')">Отмена</button>
        <button class="primary" data-test="confirm" @click="$emit('confirm')">Подтвердить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ message: String })
defineEmits(['confirm', 'cancel'])
</script>

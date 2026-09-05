<script setup lang="ts">
defineProps<{ message: string }>()
defineEmits<{ confirm: []; close: [] }>()
</script>
<template>
  <BaseModal title="Xác nhận" @close="$emit('close')">
    <div class="modal-content">
      <p class="mb-3">{{ message }}</p>
      <button class="btn btn-primary" @click="$emit('confirm')">Xác nhận</button>
      <button class="btn btn-secondary" style="margin-left: 12px" @click="$emit('close')">
        Hủy
      </button>
    </div>
  </BaseModal>
</template>

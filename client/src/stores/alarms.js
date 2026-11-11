import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAlarms = defineStore('alarms', () => {
  const active = ref([])
  async function fetchActive() { return active.value }
  return { active, fetchActive }
})
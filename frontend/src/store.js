import { computed, reactive, watch } from 'vue'

const STORAGE_KEY = 'job-direction-desk-session-v1'

function restore() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}')
    return {
      jobs: Array.isArray(saved.jobs) ? saved.jobs : [],
      selectedIds: Array.isArray(saved.selectedIds) ? saved.selectedIds : [],
    }
  } catch {
    return { jobs: [], selectedIds: [] }
  }
}

const initial = restore()
export const state = reactive({
  jobs: initial.jobs,
  selectedIds: initial.selectedIds,
  profile: null,
  profileJobKey: '',
  groupFeedback: null,
  groupFeedbackInput: '',
  singleFeedback: null,
  singleJobId: '',
  singleFeedbackInput: '',
  analysisMode: 'group',
  searchTab: 'search',
  searchKeyword: '',
  searchCity: '',
  searchEmployment: '',
  searchResults: null,
  usedModelRequests: 0,
  maxModelRequests: 8,
})

watch(
  () => [state.jobs, state.selectedIds],
  () => sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ jobs: state.jobs, selectedIds: state.selectedIds })),
  { deep: true },
)

export const selectedJobs = computed(() => state.selectedIds
  .map(id => state.jobs.find(job => job.id === id))
  .filter(Boolean))

export function addJob(job) {
  const alreadyAdded = state.jobs.some(item => item.id === job.id || item.jd_text.trim() === job.jd_text.trim())
  if (alreadyAdded) return false
  state.jobs.push(job)
  return true
}

export function removeJob(id) {
  state.jobs = state.jobs.filter(job => job.id !== id)
  state.selectedIds = state.selectedIds.filter(item => item !== id)
  invalidateProfile()
}

export function selectAll(checked) {
  state.selectedIds = checked ? state.jobs.map(job => job.id) : []
  invalidateProfile()
}

export function setSelected(ids) {
  state.selectedIds = ids.filter(id => state.jobs.some(job => job.id === id))
  invalidateProfile()
}

export function selectedKey() {
  return selectedJobs.value.map(job => `${job.id}:${job.jd_text}`).join('\u241e')
}

export function invalidateProfile() {
  if (state.profileJobKey !== selectedKey()) {
    state.profile = null
    state.profileJobKey = ''
    state.groupFeedback = null
    state.groupFeedbackInput = ''
  }
}

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>

<template>
  <section class="page-intro">
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
  </section>
</template>

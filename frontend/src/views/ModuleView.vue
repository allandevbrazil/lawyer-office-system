<script setup lang="ts">
defineProps<{ title: string }>();
</script>

<template>
  <section class="dashboard-view">
    <p class="eyebrow">Módulo</p>
    <h1>{{ title }}</h1>
    <p>Esta área está conectada ao shell e será preenchida pela próxima fatia de negócio.</p>
  </section>
</template>

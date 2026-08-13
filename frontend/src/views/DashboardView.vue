<script setup lang="ts">
import { onMounted, ref } from "vue";

import { dashboardApi, type DashboardSummary } from "@/services/api";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const summary = ref<DashboardSummary | null>(null);
const isLoading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  if (!auth.accessToken) return;
  try {
    summary.value = await dashboardApi.summary(auth.accessToken);
  } catch {
    errorMessage.value = "Não foi possível carregar o resumo.";
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <main class="flex-1 p-margin-page max-w-max-width mx-auto w-full">
    <!-- Header -->
    <header class="mb-10">
      <h2
        class="font-label-caps text-label-caps text-on-secondary-container uppercase tracking-widest mb-2"
      >
        Visão Geral
      </h2>
      <h1 class="font-display-lg text-display-lg text-primary">Dashboard</h1>
    </header>

    <!-- KPI Widgets -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-10">
      <!-- Widget 1 -->
      <div
        class="bg-surface-container-lowest border border-tertiary-fixed-dim p-widget-padding flex flex-col justify-between h-32 hover:shadow-[0_4px_20px_rgba(18,28,38,0.05)] transition-shadow duration-300"
      >
        <span class="font-body-md text-body-md text-on-surface-variant">Processos ativos</span>
        <span class="font-headline-md text-headline-md text-primary">{{
          summary?.active_cases ?? 0
        }}</span>
      </div>
      <!-- Widget 2 -->
      <div
        class="bg-surface-container-lowest border border-tertiary-fixed-dim p-widget-padding flex flex-col justify-between h-32 hover:shadow-[0_4px_20px_rgba(18,28,38,0.05)] transition-shadow duration-300"
      >
        <span class="font-body-md text-body-md text-on-surface-variant">Faturas pendentes</span>
        <span class="font-headline-md text-headline-md text-primary">{{
          summary?.pending_invoices ?? 0
        }}</span>
      </div>
      <!-- Widget 3 -->
      <div
        class="bg-surface-container-lowest border border-tertiary-fixed-dim p-widget-padding flex flex-col justify-between h-32 hover:shadow-[0_4px_20px_rgba(18,28,38,0.05)] transition-shadow duration-300"
      >
        <span class="font-body-md text-body-md text-on-surface-variant">Recebido</span>
        <span class="font-headline-md text-headline-md text-primary"
          >R$ {{ Number(summary?.billing_total ?? 0).toFixed(2) }}</span
        >
      </div>
    </div>

    <!-- Main Dashboard Area -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
      <!-- Tasks Overview (Donut Chart placeholder) -->
      <div
        class="lg:col-span-1 bg-surface-container-lowest border border-tertiary-fixed-dim p-widget-padding hover:shadow-[0_4px_20px_rgba(18,28,38,0.05)] transition-shadow duration-300 flex flex-col min-h-[400px]"
      >
        <div class="flex items-center gap-2 mb-6 pb-4 border-b border-surface-variant">
          <span class="material-symbols-outlined text-on-surface-variant">bar_chart</span>
          <h3 class="font-widget-title text-widget-title text-on-surface">Processos por Área</h3>
        </div>
        <div class="flex-1 flex flex-col gap-6">
          <div class="space-y-2">
            <div class="flex justify-between items-center mb-1">
              <span class="font-body-md text-body-md text-on-surface-variant">Cível</span>
              <span class="font-body-md text-body-md font-semibold text-secondary">42 (34%)</span>
            </div>
            <div class="w-full bg-surface-variant/20 h-3 rounded-full overflow-hidden">
              <div class="bg-secondary h-full rounded-full" style="width: 34%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between items-center mb-1">
              <span class="font-body-md text-body-md text-on-surface-variant">Trabalhista</span>
              <span class="font-body-md text-body-md font-semibold text-on-secondary-container"
                >35 (28%)</span
              >
            </div>
            <div class="w-full bg-surface-variant/20 h-3 rounded-full overflow-hidden">
              <div class="bg-on-secondary-container h-full rounded-full" style="width: 28%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between items-center mb-1">
              <span class="font-body-md text-body-md text-on-surface-variant">Tributário</span>
              <span class="font-body-md text-body-md font-semibold text-primary-container"
                >28 (23%)</span
              >
            </div>
            <div class="w-full bg-surface-variant/20 h-3 rounded-full overflow-hidden">
              <div class="bg-primary-container h-full rounded-full" style="width: 23%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between items-center mb-1">
              <span class="font-body-md text-body-md text-on-surface-variant">Criminal</span>
              <span class="font-body-md text-body-md font-semibold text-outline">19 (15%)</span>
            </div>
            <div class="w-full bg-surface-variant/20 h-3 rounded-full overflow-hidden">
              <div class="bg-outline h-full rounded-full" style="width: 15%"></div>
            </div>
          </div>
        </div>
        <div class="mt-6 pt-4 border-t border-surface-variant">
          <p class="text-xs text-on-surface-variant uppercase tracking-widest">
            Total: 124 Processos
          </p>
        </div>
      </div>

      <!-- Team Members / Calendar -->
      <div
        class="lg:col-span-2 bg-surface-container-lowest border border-tertiary-fixed-dim p-widget-padding hover:shadow-[0_4px_20px_rgba(18,28,38,0.05)] transition-shadow duration-300"
      >
        <div class="flex items-center justify-between mb-6 pb-4 border-b border-surface-variant">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-on-surface-variant">calendar_month</span>
            <h3 class="font-widget-title text-widget-title text-on-surface">
              Calendário de Eventos
            </h3>
          </div>
          <span class="text-label-caps text-on-secondary-container uppercase">Outubro 2023</span>
        </div>
        <div class="space-y-4">
          <div class="flex items-center gap-4 p-4 bg-surface-variant/20 rounded">
            <div
              class="flex flex-col items-center justify-center w-16 h-16 bg-primary-container text-on-primary rounded"
            >
              <span class="text-xs font-bold uppercase">Out</span>
              <span class="text-xl font-bold">24</span>
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-primary">Audiência de Conciliação</h4>
              <p class="text-sm text-on-surface-variant">Processo nº 0012345-67.2023.8.19.0001</p>
            </div>
            <span class="text-sm font-semibold text-on-secondary-container">09:00</span>
          </div>
          <div class="flex items-center gap-4 p-4 bg-surface-variant/20 rounded">
            <div
              class="flex flex-col items-center justify-center w-16 h-16 bg-secondary text-on-primary rounded"
            >
              <span class="text-xs font-bold uppercase">Out</span>
              <span class="text-xl font-bold">26</span>
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-primary">Prazo Recursal</h4>
              <p class="text-sm text-on-surface-variant">Apelação Cível - Prazo Final</p>
            </div>
            <span class="text-sm font-semibold text-on-secondary-container">23:59</span>
          </div>
          <div class="flex items-center gap-4 p-4 bg-surface-variant/20 rounded">
            <div
              class="flex flex-col items-center justify-center w-16 h-16 bg-outline text-on-primary rounded"
            >
              <span class="text-xs font-bold uppercase">Out</span>
              <span class="text-xl font-bold">30</span>
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-primary">Reunião com Cliente</h4>
              <p class="text-sm text-on-surface-variant">Caso Silva vs. Estado</p>
            </div>
            <span class="text-sm font-semibold text-on-secondary-container">14:30</span>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const navigation = [
  { label: "Dashboard", path: "/app/dashboard", roles: ["MASTER", "FUNCIONARIO", "CLIENTE"] },
  { label: "Processos", path: "/app/processos", roles: ["MASTER", "FUNCIONARIO", "CLIENTE"] },
  { label: "Faturas", path: "/app/faturas", roles: ["MASTER", "FUNCIONARIO", "CLIENTE"] },
  { label: "Clientes", path: "/app/clientes", roles: ["MASTER", "FUNCIONARIO"] },
  { label: "Documentos", path: "/app/documentos", roles: ["MASTER", "FUNCIONARIO", "CLIENTE"] },
  { label: "Funcionários", path: "/app/funcionarios", roles: ["MASTER", "FUNCIONARIO"] },
  { label: "Wiki", path: "/app/wiki", roles: ["MASTER", "FUNCIONARIO"] },
  { label: "Configurações", path: "/app/configuracoes", roles: ["MASTER"] },
];
const visibleNavigation = computed(() =>
  navigation.filter((item) => item.roles.includes(auth.user?.role ?? "")),
);

async function logout(): Promise<void> {
  await auth.logout();
  await router.push("/login");
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- SideNavBar -->
    <nav
      class="hidden md:flex flex-col h-screen overflow-y-auto w-64 bg-primary-container fixed left-0 top-0 border-r border-outline-variant shadow-sm z-50"
    >
      <div class="p-6">
        <RouterLink
          to="/app/dashboard"
          class="block rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-on-primary"
          aria-label="Ir para o Dashboard"
        >
          <h1 class="font-display-lg text-display-lg text-on-primary font-bold">RISE</h1>
          <p
            class="font-label-caps text-label-caps text-on-secondary-container uppercase tracking-widest mt-1"
          >
            Lawfirm ERP
          </p>
        </RouterLink>
      </div>
      <div class="flex-1 overflow-y-auto">
        <ul class="flex flex-col space-y-1 mt-4">
          <li v-for="item in visibleNavigation" :key="item.path">
            <RouterLink
              :to="item.path"
              class="block px-6 py-3 font-body-md text-body-md hover:bg-primary/20 transition-colors duration-200 text-on-primary"
              active-class="bg-surface-container-highest/10 border-l-4 border-on-tertiary-fixed-variant px-5 py-3 font-widget-title text-widget-title"
            >
              {{ item.label }}
            </RouterLink>
          </li>
        </ul>
      </div>
      <div class="p-6">
        <button
          class="w-full py-3 px-4 border border-outline-variant text-on-primary font-widget-title text-widget-title rounded hover:bg-primary/20 transition-colors flex items-center justify-center gap-2"
          type="button"
          @click="logout"
        >
          <span class="material-symbols-outlined">logout</span>
          <span>Sair</span>
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1 ml-0 md:ml-64">
      <RouterView />
    </main>
  </div>
</template>

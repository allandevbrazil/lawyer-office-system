import { createRouter, createWebHistory } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("@/views/LoginView.vue"), meta: { public: true } },
    {
      path: "/cadastro",
      component: () => import("@/views/RegisterView.vue"),
      meta: { public: true },
    },
    {
      path: "/esqueci-senha",
      component: () => import("@/views/ForgotPasswordView.vue"),
      meta: { public: true },
    },
    {
      path: "/redefinir-senha",
      component: () => import("@/views/ResetPasswordView.vue"),
      meta: { public: true },
    },
    {
      path: "/app",
      component: () => import("@/layouts/AppLayout.vue"),
      children: [
        { path: "", redirect: "/app/dashboard" },
        { path: "dashboard", component: () => import("@/views/DashboardView.vue") },
        { path: "processos", component: () => import("@/views/CasesView.vue") },
        { path: "faturas", component: () => import("@/views/InvoicesView.vue") },
        { path: "clientes", component: () => import("@/views/ClientsView.vue") },
        { path: "documentos", component: () => import("@/views/DocumentsView.vue") },
        { path: "funcionarios", component: () => import("@/views/StaffView.vue") },
        { path: "wiki", component: () => import("@/views/WikiView.vue") },
        { path: "configuracoes", component: () => import("@/views/SettingsView.vue") },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/app" },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.user && auth.accessToken) await auth.restore();
  if (to.meta.public && auth.isAuthenticated) return "/app";
  if (!to.meta.public && !auth.isAuthenticated) return "/login";
  return true;
});

export default router;

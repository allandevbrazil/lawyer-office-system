<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { authApi } from "@/services/api";

const route = useRoute();
const router = useRouter();
const password = ref("");
const message = ref("");
const errorMessage = ref("");

async function submit(): Promise<void> {
  try {
    if (password.value.length < 12) {
      errorMessage.value = "A senha deve ter pelo menos 12 caracteres.";
      return;
    }
    await authApi.resetPassword(String(route.query.token ?? ""), password.value);
    message.value = "Senha redefinida. Você já pode entrar.";
    setTimeout(() => void router.push("/login"), 700);
  } catch {
    errorMessage.value = "O token é inválido ou expirou.";
  }
}
</script>

<template>
  <main class="auth-shell">
    <section class="auth-panel">
      <div class="auth-brand">
        <span class="auth-brand-mark material-symbols-outlined">lock</span>
      </div>
      <h2>Definir nova senha</h2>
      <p class="auth-subtitle">Crie uma senha forte para proteger o acesso ao seu escritório.</p>
      <form class="auth-form" @submit.prevent="submit">
        <label for="reset-password"
          >Nova senha<input
            id="reset-password"
            v-model="password"
            type="password"
            minlength="12"
            autocomplete="new-password"
            required
        /></label>
        <p v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</p>
        <p v-if="message" class="auth-message">{{ message }}</p>
        <button class="auth-submit" type="submit">Redefinir senha</button>
      </form>
      <p class="auth-helper"><RouterLink to="/login">← Voltar para o login</RouterLink></p>
    </section>
  </main>
</template>

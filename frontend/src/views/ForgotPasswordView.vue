<script setup lang="ts">
import { ref } from "vue";

import { authApi } from "@/services/api";

const email = ref("");
const submitted = ref(false);

async function submit(): Promise<void> {
  try {
    await authApi.forgotPassword(email.value);
    submitted.value = true;
  } catch {
    submitted.value = true;
  }
}
</script>

<template>
  <main class="auth-shell">
    <section class="auth-panel">
      <div class="auth-brand">
        <span class="auth-brand-mark material-symbols-outlined">lock_reset</span>
      </div>
      <h2>Recuperar senha</h2>
      <p class="auth-subtitle">
        Insira o e-mail associado à sua conta. Enviaremos um link seguro para redefinir sua senha.
      </p>
      <form v-if="!submitted" class="auth-form" @submit.prevent="submit">
        <label for="forgot-email"
          >E-mail profissional<input
            id="forgot-email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="advogado@lexmodern.com.br"
            required /></label
        ><button class="auth-submit" type="submit">Enviar link de recuperação</button>
      </form>
      <p v-else class="auth-message">
        Se o e-mail estiver cadastrado, você receberá as instruções de recuperação.
      </p>
      <p class="auth-helper"><RouterLink to="/login">← Voltar para o login</RouterLink></p>
    </section>
  </main>
</template>

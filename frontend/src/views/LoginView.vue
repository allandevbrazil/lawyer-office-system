<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const email = ref("");
const password = ref("");
const errorMessage = ref("");
const isLoading = ref(false);
const router = useRouter();
const auth = useAuthStore();
const showPassword = ref(false);

async function submit(): Promise<void> {
  errorMessage.value = "";
  isLoading.value = true;
  try {
    await auth.login(email.value, password.value);
    await router.push("/app");
  } catch {
    errorMessage.value = "Não foi possível autenticar. Verifique seus dados.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <main class="auth-shell">
    <section class="auth-panel" aria-labelledby="login-title">
      <div class="auth-brand">
        <span class="auth-brand-mark material-symbols-outlined">account_balance</span>
      </div>
      <h1 id="login-title">Lex Modern</h1>
      <p class="auth-subtitle">Acesse o seu portal de gestão</p>
      <form class="auth-form" @submit.prevent="submit">
        <label for="email"
          >E-mail<input
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="advogado@lexmodern.com.br"
            required
        /></label>
        <label for="password"
          >Senha
          <div class="auth-password-wrap">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="••••••••"
              required
            /><button
              class="auth-password-toggle"
              type="button"
              aria-label="Mostrar senha"
              @click="showPassword = !showPassword"
            >
              <span class="material-symbols-outlined">{{
                showPassword ? "visibility_off" : "visibility"
              }}</span>
            </button>
          </div></label
        >
        <p v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</p>
        <div class="auth-links">
          <RouterLink to="/esqueci-senha">Esqueci minha senha</RouterLink
          ><RouterLink to="/cadastro">Tenho um convite</RouterLink>
        </div>
        <button class="auth-submit" type="submit" :disabled="isLoading">
          {{ isLoading ? "Entrando..." : "Entrar no sistema"
          }}<span class="material-symbols-outlined">arrow_forward</span>
        </button>
      </form>
      <p class="auth-helper">
        Problemas com o acesso? <a href="mailto:suporte@lexmodern.example">Contate o suporte</a>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { authApi } from "@/services/api";
const route = useRoute();
const router = useRouter();
const fullName = ref("");
const email = ref("");
const password = ref("");
const confirmation = ref("");
const phone = ref("");
const message = ref("");
const errorMessage = ref("");
const showPassword = ref(false);
const showConfirm = ref(false);
function maskPhone(value: string): string {
  const d = value.replace(/\D/g, "").slice(0, 11);
  return d.length < 3
    ? d
    : `(${d.slice(0, 2)}) ${d.slice(2, 7)}${d.length > 7 ? `-${d.slice(7)}` : ""}`;
}
async function submit(): Promise<void> {
  errorMessage.value = "";
  message.value = "";
  if (password.value.length < 12)
    return void (errorMessage.value = "A senha deve ter pelo menos 12 caracteres.");
  if (password.value !== confirmation.value)
    return void (errorMessage.value = "As senhas não conferem.");
  try {
    await authApi.register({
      invite_token: String(route.query.invite ?? ""),
      full_name: fullName.value,
      email: email.value,
      password: password.value,
      phone: phone.value,
    });
    message.value = "Cadastro concluído. Você já pode entrar.";
    setTimeout(() => void router.push("/login"), 900);
  } catch {
    errorMessage.value = "O convite é inválido ou os dados não puderam ser registrados.";
  }
}
</script>
<template>
  <main class="auth-shell auth-split">
    <div class="auth-brand-panel">
      <div>
        <h2>Lex Modern</h2>
        <p>
          Gestão jurídica elevada. Junte-se ao seu escritório em uma plataforma feita para
          profissionais do direito.
        </p>
      </div>
    </div>
    <div class="auth-panel-wrap">
      <section class="auth-panel">
        <div class="auth-brand">
          <span class="auth-brand-mark material-symbols-outlined">person_add</span>
        </div>
        <h2>Criar sua conta</h2>
        <p class="auth-subtitle">Você foi convidado. Preencha seus dados para acessar o sistema.</p>
        <form class="auth-form" @submit.prevent="submit">
          <label>Nome completo<input v-model="fullName" autocomplete="name" required /></label
          ><label>E-mail<input v-model="email" type="email" autocomplete="email" required /></label
          ><label
            >Telefone<input
              :value="phone"
              placeholder="(11) 99999-9999"
              @input="phone = maskPhone(($event.target as HTMLInputElement).value)" /></label
          ><label
            >Senha
            <div class="auth-password-wrap">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                minlength="12"
                autocomplete="new-password"
                required
              /><button
                type="button"
                class="auth-password-toggle"
                @click="showPassword = !showPassword"
              >
                <span class="material-symbols-outlined">{{
                  showPassword ? "visibility_off" : "visibility"
                }}</span>
              </button>
            </div></label
          ><label
            >Confirmar senha
            <div class="auth-password-wrap">
              <input
                v-model="confirmation"
                :type="showConfirm ? 'text' : 'password'"
                minlength="12"
                autocomplete="new-password"
                required
              /><button
                type="button"
                class="auth-password-toggle"
                @click="showConfirm = !showConfirm"
              >
                <span class="material-symbols-outlined">{{
                  showConfirm ? "visibility_off" : "visibility"
                }}</span>
              </button>
            </div></label
          ><label class="auth-check"
            ><input type="checkbox" required /><span
              >Eu li e concordo com os <a href="#">Termos de Uso</a> e a
              <a href="#">Política de Privacidade</a>.</span
            ></label
          >
          <p v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</p>
          <p v-if="message" class="auth-message">{{ message }}</p>
          <button class="auth-submit" type="submit">Finalizar cadastro</button>
        </form>
        <p class="auth-helper">
          Problemas com seu convite?
          <a href="mailto:suporte@lexmodern.example">Contate o administrador</a>.
        </p>
      </section>
    </div>
  </main>
</template>

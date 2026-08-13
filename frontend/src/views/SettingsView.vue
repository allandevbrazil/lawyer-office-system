<script setup lang="ts">
import { onMounted, ref } from "vue";
import { adminApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
const error = ref("");
const saved = ref("");
const form = ref({
  legal_name: "",
  trade_name: "",
  tax_id: "",
  email: "",
  phone: "",
  street: "",
  number: "",
  city: "",
  state: "SP",
  zip: "",
  timezone: "America/Sao_Paulo",
  currency: "BRL",
});
function maskZip(value: string): string {
  const d = value.replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}
function maskPhone(value: string): string {
  const d = value.replace(/\D/g, "").slice(0, 11);
  return d.length < 3
    ? d
    : `(${d.slice(0, 2)}) ${d.slice(2, 7)}${d.length > 7 ? `-${d.slice(7)}` : ""}`;
}
async function load(): Promise<void> {
  if (!auth.accessToken) return;
  try {
    const s = await adminApi.firmSettings(auth.accessToken);
    const address = (s.address_json as Record<string, string> | null) || {};
    form.value = {
      legal_name: String(s.legal_name || ""),
      trade_name: String(s.trade_name || ""),
      tax_id: String(s.tax_id || ""),
      email: String(s.email || ""),
      phone: String(s.phone || ""),
      street: address.street || "",
      number: address.number || "",
      city: address.city || "",
      state: address.state || "SP",
      zip: address.zip || "",
      timezone: String(s.timezone || "America/Sao_Paulo"),
      currency: String(s.currency || "BRL"),
    };
  } catch {
    error.value = "Não foi possível carregar as configurações.";
  }
}
async function save(): Promise<void> {
  if (
    !auth.accessToken ||
    form.value.trade_name.length < 2 ||
    !/^\S+@\S+\.\S+$/.test(form.value.email)
  )
    return void (error.value = "Informe nome e e-mail válidos.");
  try {
    await adminApi.updateFirmSettings(auth.accessToken, {
      legal_name: form.value.legal_name,
      trade_name: form.value.trade_name,
      tax_id: form.value.tax_id,
      email: form.value.email,
      phone: form.value.phone,
      address_json: {
        street: form.value.street,
        number: form.value.number,
        city: form.value.city,
        state: form.value.state,
        zip: form.value.zip,
      },
      timezone: form.value.timezone,
      currency: form.value.currency,
    });
    saved.value = "Alterações salvas.";
    setTimeout(() => (saved.value = ""), 2500);
  } catch {
    error.value = "Não foi possível salvar as configurações.";
  }
}
onMounted(load);
</script>
<template>
  <section class="settings">
    <header><input placeholder="Buscar..." /><span>RS</span></header>
    <main>
      <div class="heading">
        <div>
          <p>Administração</p>
          <h1>Configurações</h1>
          <small>Gerencie as preferências e informações do seu escritório.</small>
        </div>
        <button class="primary" @click="save">Salvar alterações</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="saved" class="success">{{ saved }}</p>
      <div class="grid">
        <section>
          <h2>Dados do escritório</h2>
          <label>Nome legal<input v-model="form.legal_name" /></label
          ><label>Nome fantasia<input v-model="form.trade_name" /></label
          ><label>E-mail corporativo<input v-model="form.email" type="email" /></label
          ><label>CNPJ<input v-model="form.tax_id" /></label>
        </section>
        <section>
          <h2>Localização e contato</h2>
          <label
            >CEP<input
              :value="form.zip"
              @input="form.zip = maskZip(($event.target as HTMLInputElement).value)" /></label
          ><label>Endereço<input v-model="form.street" /></label
          ><label>Número<input v-model="form.number" /></label
          ><label>Cidade<input v-model="form.city" /></label
          ><label
            >Estado<select v-model="form.state">
              <option v-for="state in ['SP', 'RJ', 'MG', 'PR', 'SC', 'RS', 'BA']" :key="state">
                {{ state }}
              </option>
            </select></label
          ><label
            >Telefone<input
              :value="form.phone"
              @input="form.phone = maskPhone(($event.target as HTMLInputElement).value)"
          /></label>
        </section>
        <section>
          <h2>Preferências</h2>
          <label
            >Fuso horário<select v-model="form.timezone">
              <option>America/Sao_Paulo</option>
              <option>America/Manaus</option>
              <option>America/Recife</option>
            </select></label
          ><label
            >Moeda<select v-model="form.currency">
              <option>BRL</option>
              <option>USD</option>
            </select></label
          >
        </section>
      </div>
    </main>
  </section>
</template>
<style scoped>
.settings {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope;
}
.settings > header {
  height: 64px;
  padding: 0 40px 0 48px;
  border-bottom: 1px solid #c4c6cb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.settings header input {
  border: 0;
  background: transparent;
  padding: 10px;
  width: 280px;
}
.settings header span {
  background: #121c26;
  color: #fff;
  border-radius: 50%;
  padding: 9px;
  font-size: 11px;
}
.settings > main {
  width: min(1440px, 100%);
  margin: 0 auto;
  padding: 40px;
}
.heading {
  padding: 0;
  display: flex;
  justify-content: space-between;
  align-items: end;
}
.heading p {
  color: #7b5647;
  text-transform: uppercase;
  font-size: 12px;
}
.heading h1 {
  font: 48px "Libre Caslon Text";
  margin: 6px 0;
}
.primary {
  padding: 12px 18px;
  background: #7b5647;
  color: white;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}
.grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  padding: 0 0 40px;
}
.grid section {
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
  padding: 24px;
  display: grid;
  gap: 16px;
}
.grid section:nth-child(3) {
  grid-column: 2;
}
.grid h2 {
  font: 600 14px "Work Sans";
  text-transform: uppercase;
  color: #7b5647;
}
.grid label {
  display: grid;
  gap: 6px;
  font-size: 13px;
}
.grid input,
.grid select {
  padding: 10px;
  border: 0;
  border-bottom: 1px solid #d7c3b0;
  background: transparent;
}
.error {
  margin: 0 0 16px;
  color: #ba1a1a;
}
.success {
  margin: 0 0 16px;
  color: #2e7d32;
}
@media (max-width: 800px) {
  .heading {
    padding: 24px 16px;
    flex-direction: column;
    align-items: stretch;
    gap: 18px;
  }
  .grid {
    grid-template-columns: 1fr;
    padding: 0 16px 24px;
  }
  .grid section:nth-child(3) {
    grid-column: auto;
  }
}
</style>

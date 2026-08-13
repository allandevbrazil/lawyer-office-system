<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { adminApi, type StaffItem } from "@/services/api";
import { confirmAction, showError, showSuccess } from "@/services/alerts";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
const staff = ref<StaffItem[]>([]);
const search = ref("");
const role = ref("ALL");
const status = ref("ALL");
const error = ref("");
const selected = ref<StaffItem | null>(null);
const editing = ref<StaffItem | null>(null);
const open = ref(false);
const saving = ref(false);
const formError = ref("");
const form = ref({
  full_name: "",
  email: "",
  password: "",
  role: "FUNCIONARIO",
  status: "ACTIVE",
  phone: "",
});
const filtered = computed(() =>
  staff.value.filter(
    (item) =>
      (!search.value ||
        `${item.full_name} ${item.email}`.toLowerCase().includes(search.value.toLowerCase())) &&
      (role.value === "ALL" || item.role === role.value) &&
      (status.value === "ALL" || item.status === status.value),
  ),
);
const initials = (name: string) =>
  name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
const maskPhone = (value: string) => {
  const d = value.replace(/\D/g, "").slice(0, 11);
  return d.length < 3
    ? d
    : `(${d.slice(0, 2)}) ${d.slice(2, 7)}${d.length > 7 ? `-${d.slice(7)}` : ""}`;
};
function create(): void {
  editing.value = null;
  formError.value = "";
  form.value = {
    full_name: "",
    email: "",
    password: "",
    role: "FUNCIONARIO",
    status: "ACTIVE",
    phone: "",
  };
  open.value = true;
}
function edit(item: StaffItem): void {
  selected.value = null;
  editing.value = item;
  form.value = {
    full_name: item.full_name,
    email: item.email,
    password: "",
    role: item.role,
    status: item.status,
    phone: "",
  };
  formError.value = "";
  open.value = true;
}
async function load(): Promise<void> {
  if (!auth.accessToken) return;
  try {
    staff.value = await adminApi.staff(auth.accessToken);
  } catch {
    error.value = "Não foi possível carregar a equipe.";
  }
}
async function save(): Promise<void> {
  if (form.value.full_name.trim().length < 2)
    return void (formError.value = "Informe o nome completo.");
  if (!/^\S+@\S+\.\S+$/.test(form.value.email))
    return void (formError.value = "Informe um e-mail válido.");
  if (!editing.value && form.value.password.length < 8)
    return void (formError.value = "A senha deve ter pelo menos 8 caracteres.");
  if (!auth.accessToken) return;
  saving.value = true;
  try {
    const payload = {
      full_name: form.value.full_name,
      email: form.value.email,
      role: form.value.role,
      status: form.value.status,
      phone: form.value.phone || undefined,
      ...(form.value.password ? { password: form.value.password } : {}),
    };
    const item = editing.value
      ? await adminApi.updateStaff(auth.accessToken, editing.value.id, payload)
      : await adminApi.createStaff(auth.accessToken, { ...payload, password: form.value.password });
    staff.value = editing.value
      ? staff.value.map((x) => (x.id === item.id ? item : x))
      : [item, ...staff.value];
    open.value = false;
  } catch {
    formError.value = "Não foi possível salvar o funcionário.";
  } finally {
    saving.value = false;
  }
}
async function suspend(item: StaffItem): Promise<void> {
  if (
    !auth.accessToken ||
    !(await confirmAction(
      "Suspender funcionário?",
      `${item.full_name} perderá o acesso ao sistema.`,
      "Suspender",
    ))
  )
    return;
  try {
    await adminApi.removeStaff(auth.accessToken, item.id);
    staff.value = staff.value.map((x) => (x.id === item.id ? { ...x, status: "SUSPENDED" } : x));
    showSuccess("Funcionário suspenso");
  } catch {
    error.value = "Não foi possível suspender o funcionário.";
    showError("Suspensão não realizada", error.value);
  }
}
onMounted(load);
</script>
<template>
  <section class="page">
    <header class="top">
      <input
        v-model="search"
        placeholder="Buscar em todo o sistema..."
        aria-label="Buscar funcionários"
      /><span>RS</span>
    </header>
    <main>
      <div class="heading">
        <div>
          <p>Equipe</p>
          <h1>Funcionários</h1>
          <small>Gerencie sua equipe, cargos e permissões de acesso.</small>
        </div>
        <button class="primary" @click="create">＋ Novo funcionário</button>
      </div>
      <div class="filters">
        <input v-model="search" placeholder="Buscar por nome, e-mail ou cargo..." /><select
          v-model="role"
        >
          <option value="ALL">Todos os cargos</option>
          <option value="FUNCIONARIO">Funcionários</option></select
        ><select v-model="status">
          <option value="ALL">Todos os status</option>
          <option value="ACTIVE">Ativo</option>
          <option value="SUSPENDED">Suspenso</option>
        </select>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="table">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Cargo</th>
              <th>E-mail</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.id">
              <td>
                <button class="name" @click="selected = item">
                  <b>{{ initials(item.full_name) }}</b
                  >{{ item.full_name }}
                </button>
              </td>
              <td>{{ item.role }}</td>
              <td>{{ item.email }}</td>
              <td>
                <em>{{ item.status === "ACTIVE" ? "Ativo" : "Suspenso" }}</em>
              </td>
              <td>
                <button @click="selected = item">◉</button><button @click="edit(item)">✎</button
                ><button @click="suspend(item)">⌫</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!filtered.length">Nenhum funcionário encontrado.</p>
      </div>
    </main>
    <div v-if="selected" class="backdrop">
      <section class="modal">
        <header>
          <h2>Detalhes do funcionário</h2>
          <button @click="selected = null">×</button>
        </header>
        <div class="profile">
          <b>{{ initials(selected.full_name) }}</b>
          <div>
            <h3>{{ selected.full_name }}</h3>
            <p>{{ selected.role }} · {{ selected.status }}</p>
          </div>
        </div>
        <p><strong>E-mail:</strong> {{ selected.email }}</p>
        <footer>
          <button class="secondary" @click="selected = null">Fechar</button
          ><button class="primary" @click="edit(selected)">Editar funcionário</button>
        </footer>
      </section>
    </div>
    <div v-if="open" class="backdrop">
      <form class="modal form" @submit.prevent="save">
        <header>
          <h2>{{ editing ? "Editar funcionário" : "Novo funcionário" }}</h2>
          <button type="button" @click="open = false">×</button>
        </header>
        <p v-if="formError" class="error">{{ formError }}</p>
        <label>Nome<input v-model="form.full_name" maxlength="160" required /></label
        ><label>E-mail<input v-model="form.email" type="email" required /></label
        ><label
          >Telefone<input
            :value="form.phone"
            @input="form.phone = maskPhone(($event.target as HTMLInputElement).value)" /></label
        ><label
          >Cargo<select v-model="form.role">
            <option value="FUNCIONARIO">Funcionário</option>
          </select></label
        ><label
          >Status<select v-model="form.status">
            <option value="ACTIVE">Ativo</option>
            <option value="SUSPENDED">Suspenso</option>
          </select></label
        ><label>Senha<input v-model="form.password" type="password" minlength="8" /></label>
        <footer>
          <button type="button" class="secondary" @click="open = false">Cancelar</button
          ><button class="primary" :disabled="saving">
            {{ saving ? "Salvando..." : "Salvar" }}
          </button>
        </footer>
      </form>
    </div>
  </section>
</template>
<style scoped>
.page {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope;
}
.top {
  height: 64px;
  padding: 0 40px 0 48px;
  border-bottom: 1px solid #c4c6cb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.top input {
  border: 0;
  background: transparent;
  padding: 10px;
  width: 280px;
}
.top span {
  background: #121c26;
  color: #fff;
  border-radius: 50%;
  padding: 9px;
  font-size: 11px;
}
.page > main {
  width: min(1440px, 100%);
  margin: 0 auto;
  padding: 40px;
}
.heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  padding: 0;
}
.heading p {
  color: #7b5647;
  text-transform: uppercase;
  font: 600 12px Work Sans;
}
.heading h1 {
  font: 48px "Libre Caslon Text";
  margin: 6px 0;
}
.filters,
.table {
  margin: 0 0 24px;
  padding: 20px;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
}
.filters {
  display: flex;
  gap: 14px;
}
.filters input {
  flex: 1;
  padding: 10px;
}
.filters select,
.form input,
.form select {
  padding: 10px;
  border: 1px solid #c4c6cb;
  background: #fff;
}
.primary,
.secondary {
  padding: 11px 16px;
  border: 1px solid #d7c3b0;
  border-radius: 4px;
  cursor: pointer;
}
.primary {
  background: #7b5647;
  color: #fff;
}
.secondary {
  background: #fff;
}
.table {
  padding: 0;
  overflow: auto;
}
.table table {
  width: 100%;
  border-collapse: collapse;
}
.table th,
.table td {
  padding: 16px;
  border-bottom: 1px solid #e5e2db;
  text-align: left;
}
.table td > button {
  border: 0;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
}
.name {
  display: flex;
  gap: 10px;
  align-items: center;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.name b,
.profile > b {
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #d9e3f2;
  color: #121c26;
  width: 34px;
  height: 34px;
  font-size: 11px;
}
.table em {
  font-style: normal;
  background: #d9e3f2;
  border-radius: 99px;
  padding: 5px 9px;
  font-size: 12px;
}
.backdrop {
  position: fixed;
  inset: 0;
  background: #121c2666;
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 50;
}
.modal {
  width: min(680px, 100%);
  background: #fcf9f2;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
  overflow: hidden;
}
.modal header,
.modal footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 24px;
  border-bottom: 1px solid #d7c3b0;
}
.modal header button {
  border: 0;
  background: transparent;
  font-size: 24px;
}
.modal footer {
  justify-content: flex-end;
  border-top: 1px solid #d7c3b0;
  border-bottom: 0;
}
.profile {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 24px;
}
.profile > b {
  width: 64px;
  height: 64px;
}
.modal > p {
  padding: 0 24px 24px;
}
.form {
  padding: 24px;
  display: grid;
  gap: 13px;
}
.form header,
.form footer {
  margin: 0 -24px;
}
.form label {
  display: grid;
  gap: 6px;
  font-size: 13px;
}
.error {
  color: #ba1a1a;
}
@media (max-width: 700px) {
  .heading {
    padding: 24px 16px;
    align-items: stretch;
    flex-direction: column;
    gap: 18px;
  }
  .filters {
    margin: 0 16px 24px;
    flex-direction: column;
  }
  .table {
    margin: 0 16px 24px;
  }
}
</style>

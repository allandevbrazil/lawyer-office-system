<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import {
  clientsApi,
  type ClientCreateInput,
  type ClientItem,
  type ClientUpdateInput,
} from "@/services/api";
import { confirmAction, showError, showSuccess } from "@/services/alerts";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const search = ref("");
const typeFilter = ref("ALL");
const statusFilter = ref("ALL");
const clients = ref<ClientItem[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");
const selectedClient = ref<ClientItem | null>(null);
const isFormOpen = ref(false);
const editingClient = ref<ClientItem | null>(null);
const isSaving = ref(false);
const isDeleting = ref<string | null>(null);
const formError = ref("");
const form = ref({
  type: "PF" as "PF" | "PJ",
  name: "",
  document_number: "",
  email: "",
  phone: "",
  notes: "",
  status: "ACTIVE",
});
const canManage = computed(() => auth.user?.role !== "CLIENTE");

const filteredClients = computed(() =>
  clients.value.filter(
    (client) =>
      (typeFilter.value === "ALL" || client.type === typeFilter.value) &&
      (statusFilter.value === "ALL" || client.status === statusFilter.value),
  ),
);

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function openCreate(): void {
  editingClient.value = null;
  selectedClient.value = null;
  formError.value = "";
  form.value = {
    type: "PF",
    name: "",
    document_number: "",
    email: "",
    phone: "",
    notes: "",
    status: "ACTIVE",
  };
  isFormOpen.value = true;
}

function openEdit(client: ClientItem): void {
  selectedClient.value = null;
  editingClient.value = client;
  formError.value = "";
  form.value = {
    type: client.type,
    name: client.name,
    document_number: client.document_number ?? "",
    email: client.email ?? "",
    phone: client.phone ?? "",
    notes: client.notes ?? "",
    status: client.status,
  };
  isFormOpen.value = true;
}

function closeForm(): void {
  if (!isSaving.value) isFormOpen.value = false;
}

function validateForm(): string {
  if (form.value.name.trim().length < 2) return "O nome deve ter pelo menos 2 caracteres.";
  if (form.value.name.trim().length > 200) return "O nome deve ter no máximo 200 caracteres.";
  if (form.value.email && !/^\S+@\S+\.\S+$/.test(form.value.email))
    return "Informe um e-mail válido.";
  if (form.value.phone.length > 32) return "O telefone deve ter no máximo 32 caracteres.";
  if (form.value.notes.length > 4000) return "As observações devem ter no máximo 4.000 caracteres.";
  return "";
}

async function loadClients(): Promise<void> {
  if (!auth.accessToken) return;
  isLoading.value = true;
  errorMessage.value = "";
  try {
    clients.value = await clientsApi.list(auth.accessToken, search.value);
  } catch {
    errorMessage.value =
      "Não foi possível carregar os clientes. Faça login novamente se sua sessão expirou.";
  } finally {
    isLoading.value = false;
  }
}

async function saveClient(): Promise<void> {
  formError.value = validateForm();
  if (formError.value || !auth.accessToken) return;
  isSaving.value = true;
  try {
    if (editingClient.value) {
      const payload: ClientUpdateInput = {
        name: form.value.name.trim(),
        email: form.value.email.trim() || undefined,
        phone: form.value.phone.trim() || undefined,
        notes: form.value.notes.trim() || undefined,
        status: form.value.status,
      };
      const updated = await clientsApi.update(auth.accessToken, editingClient.value.id, payload);
      clients.value = clients.value.map((client) => (client.id === updated.id ? updated : client));
    } else {
      const payload: ClientCreateInput = {
        type: form.value.type,
        name: form.value.name.trim(),
        document_number: form.value.document_number.trim() || undefined,
        email: form.value.email.trim() || undefined,
        phone: form.value.phone.trim() || undefined,
        notes: form.value.notes.trim() || undefined,
      };
      const created = await clientsApi.create(auth.accessToken, payload);
      clients.value = [created, ...clients.value];
    }
    isFormOpen.value = false;
  } catch {
    formError.value = "Não foi possível salvar o cliente. Verifique os dados e tente novamente.";
  } finally {
    isSaving.value = false;
  }
}

async function deleteClient(client: ClientItem): Promise<void> {
  if (
    !auth.accessToken ||
    !(await confirmAction(
      "Excluir cliente?",
      `"${client.name}" será removido. Esta ação não pode ser desfeita.`,
      "Excluir cliente",
    ))
  )
    return;
  isDeleting.value = client.id;
  try {
    await clientsApi.remove(auth.accessToken, client.id);
    clients.value = clients.value.filter((item) => item.id !== client.id);
    if (selectedClient.value?.id === client.id) selectedClient.value = null;
    showSuccess("Cliente excluído");
  } catch {
    errorMessage.value =
      "Não foi possível excluir o cliente. Verifique se ele possui processos vinculados.";
    showError("Exclusão não realizada", errorMessage.value);
  } finally {
    isDeleting.value = null;
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") return;
  if (isFormOpen.value) closeForm();
  else selectedClient.value = null;
}

onMounted(loadClients);
watch(search, loadClients);
onMounted(() => window.addEventListener("keydown", handleKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
  <section class="clients-page">
    <header class="clients-topbar">
      <label class="top-search"
        ><span class="material-symbols-outlined">search</span
        ><input v-model="search" aria-label="Buscar clientes" placeholder="Buscar clientes..."
      /></label>
      <div class="top-actions">
        <button class="icon-button" type="button" aria-label="Notificações">
          <span class="material-symbols-outlined">notifications</span></button
        ><button class="icon-button" type="button" aria-label="Ajuda">
          <span class="material-symbols-outlined">help_outline</span></button
        ><button class="avatar-button" type="button" aria-label="Abrir perfil">RS</button>
      </div>
    </header>
    <main class="clients-content">
      <div class="page-heading">
        <div>
          <p class="eyebrow">Relacionamento</p>
          <h1>Clientes</h1>
          <p class="page-description">
            Gerencie sua carteira de clientes, pessoas físicas e jurídicas.
          </p>
        </div>
        <button v-if="canManage" class="primary-button" type="button" @click="openCreate">
          <span class="material-symbols-outlined">add</span>Novo cliente
        </button>
      </div>
      <div class="filter-panel">
        <select v-model="typeFilter" aria-label="Filtrar por tipo">
          <option value="ALL">Todos os tipos</option>
          <option value="PF">Pessoa física (PF)</option>
          <option value="PJ">Pessoa jurídica (PJ)</option></select
        ><select v-model="statusFilter" aria-label="Filtrar por status">
          <option value="ALL">Todos os status</option>
          <option value="ACTIVE">Status: ativo</option>
          <option value="INACTIVE">Status: inativo</option></select
        ><button class="filter-action" type="button">
          <span class="material-symbols-outlined">filter_list</span>Mais filtros
        </button>
      </div>
      <p v-if="isLoading" class="state-message">Carregando clientes...</p>
      <p v-else-if="errorMessage" class="state-message form-error" role="alert">
        {{ errorMessage }}
      </p>
      <div v-else class="table-shell">
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Nome do cliente</th>
                <th>CPF/CNPJ</th>
                <th>E-mail</th>
                <th>Telefone</th>
                <th>Status</th>
                <th class="actions-heading">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="client in filteredClients" :key="client.id">
                <td>
                  <button class="client-name" type="button" @click="selectedClient = client">
                    <span class="client-avatar">{{ initials(client.name) }}</span
                    >{{ client.name }}
                  </button>
                </td>
                <td class="muted-cell">{{ client.document_number || "-" }}</td>
                <td class="muted-cell">{{ client.email || "-" }}</td>
                <td class="muted-cell">{{ client.phone || "-" }}</td>
                <td>
                  <span class="status-tag" :class="{ inactive: client.status !== 'ACTIVE' }">{{
                    client.status === "ACTIVE" ? "Ativo" : "Inativo"
                  }}</span>
                </td>
                <td class="row-actions">
                  <button
                    type="button"
                    aria-label="Visualizar cliente"
                    title="Visualizar"
                    @click="selectedClient = client"
                  >
                    <span class="material-symbols-outlined">visibility</span></button
                  ><button
                    v-if="canManage"
                    type="button"
                    aria-label="Editar cliente"
                    title="Editar"
                    @click="openEdit(client)"
                  >
                    <span class="material-symbols-outlined">edit</span></button
                  ><button
                    v-if="canManage"
                    type="button"
                    aria-label="Excluir cliente"
                    title="Excluir"
                    :disabled="isDeleting === client.id"
                    @click="deleteClient(client)"
                  >
                    <span class="material-symbols-outlined">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="!filteredClients.length" class="empty-state">Nenhum cliente encontrado.</p>
        <div v-else class="table-footer">
          Mostrando {{ filteredClients.length }} de {{ clients.length }} registros
        </div>
      </div>
    </main>

    <div
      v-if="selectedClient"
      class="modal-backdrop"
      role="presentation"
      @click.self="selectedClient = null"
    >
      <section
        class="client-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="client-details-title"
      >
        <header class="modal-header">
          <h2 id="client-details-title">Detalhes do cliente</h2>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar detalhes"
            @click="selectedClient = null"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div class="modal-body">
          <div class="client-profile">
            <span class="large-avatar">{{ initials(selectedClient.name) }}</span>
            <div>
              <h3>{{ selectedClient.name }}</h3>
              <p>
                {{ selectedClient.type === "PF" ? "Pessoa física" : "Pessoa jurídica" }} ·
                {{ selectedClient.status === "ACTIVE" ? "Ativo" : "Inativo" }}
              </p>
            </div>
          </div>
          <dl class="details-grid">
            <div>
              <dt>CPF/CNPJ</dt>
              <dd>{{ selectedClient.document_number || "Não informado" }}</dd>
            </div>
            <div>
              <dt>E-mail</dt>
              <dd>{{ selectedClient.email || "Não informado" }}</dd>
            </div>
            <div>
              <dt>Telefone</dt>
              <dd>{{ selectedClient.phone || "Não informado" }}</dd>
            </div>
            <div>
              <dt>Observações</dt>
              <dd>{{ selectedClient.notes || "Nenhuma observação" }}</dd>
            </div>
          </dl>
        </div>
        <footer class="modal-footer">
          <button class="secondary-button" type="button" @click="selectedClient = null">
            Fechar</button
          ><button
            v-if="canManage"
            class="primary-button"
            type="button"
            @click="openEdit(selectedClient)"
          >
            Editar cliente
          </button>
        </footer>
      </section>
    </div>

    <div
      v-if="isFormOpen && canManage"
      class="modal-backdrop"
      role="presentation"
      @click.self="closeForm"
    >
      <section
        class="client-modal form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="client-form-title"
      >
        <header class="modal-header">
          <h2 id="client-form-title">{{ editingClient ? "Editar cliente" : "Novo cliente" }}</h2>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar formulário"
            @click="closeForm"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <form class="modal-body client-form" novalidate @submit.prevent="saveClient">
          <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
          <div class="form-grid">
            <label
              >Tipo<select v-model="form.type" :disabled="Boolean(editingClient)">
                <option value="PF">Pessoa física</option>
                <option value="PJ">Pessoa jurídica</option>
              </select></label
            ><label>Nome<input v-model="form.name" required minlength="2" maxlength="200" /></label
            ><label>CPF/CNPJ<input v-model="form.document_number" maxlength="128" /></label
            ><label>E-mail<input v-model="form.email" type="email" maxlength="320" /></label
            ><label>Telefone<input v-model="form.phone" maxlength="32" /></label
            ><label v-if="editingClient"
              >Status<select v-model="form.status">
                <option value="ACTIVE">Ativo</option>
                <option value="INACTIVE">Inativo</option>
              </select></label
            >
          </div>
          <label
            >Observações<textarea v-model="form.notes" maxlength="4000" rows="4"></textarea>
          </label>
          <footer class="modal-footer">
            <button class="secondary-button" type="button" @click="closeForm">Cancelar</button
            ><button class="primary-button" type="submit" :disabled="isSaving">
              {{ isSaving ? "Salvando..." : "Salvar cliente" }}
            </button>
          </footer>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.clients-page {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope, sans-serif;
}
.clients-topbar {
  height: 64px;
  padding: 0 40px 0 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #c4c6cb;
  background: #fcf9f2;
  position: sticky;
  top: 0;
  z-index: 10;
}
.top-search {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #44474b;
}
.top-search input {
  width: 280px;
  padding: 9px 12px 9px 0;
  border: 0;
  outline: 0;
  background: transparent;
}
.top-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.icon-button,
.row-actions button {
  border: 0;
  padding: 7px;
  color: #44474b;
  background: transparent;
  cursor: pointer;
}
.avatar-button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: #121c26;
  color: #fff;
  font:
    600 11px "Work Sans",
    sans-serif;
}
.clients-content {
  width: min(1440px, 100%);
  margin: 0 auto;
  padding: 40px;
}
.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 24px;
  margin-bottom: 32px;
}
.eyebrow,
th,
dt {
  font:
    600 12px/1.4 "Work Sans",
    sans-serif;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.eyebrow {
  margin: 0 0 8px;
  color: #7b5647;
}
h1,
h2 {
  margin: 0;
  font-family: "Libre Caslon Text", Georgia, serif;
}
h1 {
  font-size: 48px;
  line-height: 1.1;
}
.page-description {
  margin: 10px 0 0;
  color: #44474b;
}
.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 16px;
  border: 1px solid #d7c3b0;
  border-radius: 4px;
  cursor: pointer;
  font:
    600 14px "Work Sans",
    sans-serif;
}
.primary-button {
  background: #7b5647;
  border-color: #7b5647;
  color: #fff;
}
.secondary-button {
  background: #fff;
  color: #1c1c18;
}
.primary-button:disabled,
.row-actions button:disabled {
  opacity: 0.6;
  cursor: wait;
}
.filter-panel {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  margin-bottom: 24px;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
}
.filter-panel select {
  flex: 1;
  min-width: 150px;
  border: 0;
  border-bottom: 1px solid #d7c3b0;
  padding: 9px 0;
  background: transparent;
  outline: 0;
  color: #44474b;
}
.filter-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  background: transparent;
  color: #7b5647;
  cursor: pointer;
  font:
    600 14px "Work Sans",
    sans-serif;
  white-space: nowrap;
}
.table-shell {
  overflow: hidden;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
  text-align: left;
}
th {
  padding: 16px 20px;
  color: #44474b;
  background: #f6f3ec;
  border-bottom: 1px solid #d7c3b0;
}
td {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(215, 195, 176, 0.7);
  font-size: 14px;
}
.muted-cell {
  color: #44474b;
}
.client-name {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  color: #1c1c18;
  font:
    600 14px "Work Sans",
    sans-serif;
  text-align: left;
}
.client-name:hover {
  color: #7b5647;
}
.client-avatar,
.large-avatar {
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e5e2db;
  color: #7b5647;
  font:
    600 12px "Work Sans",
    sans-serif;
}
.client-avatar {
  width: 32px;
  height: 32px;
}
.large-avatar {
  width: 56px;
  height: 56px;
  font-size: 18px;
}
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 3px;
  background: #e5e2db;
  color: #44474b;
  font:
    700 10px "Work Sans",
    sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.status-tag:not(.inactive) {
  background: #d9e3f2;
  color: #3e4853;
}
.status-tag.inactive {
  background: #ffdad6;
  color: #93000a;
}
.row-actions {
  text-align: right;
  white-space: nowrap;
}
.row-actions button:hover {
  color: #7b5647;
}
.actions-heading {
  text-align: right;
}
.table-footer,
.state-message,
.empty-state {
  padding: 18px 20px;
  color: #44474b;
  font-size: 14px;
}
.form-error {
  color: #ba1a1a;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background: rgba(18, 28, 38, 0.4);
  backdrop-filter: blur(4px);
}
.client-modal {
  width: min(760px, 100%);
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #fcf9f2;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
  box-shadow: 0 24px 60px rgba(18, 28, 38, 0.2);
}
.modal-header,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
  background: #f6f3ec;
  border-bottom: 1px solid #d7c3b0;
}
.modal-header h2 {
  font-size: 24px;
}
.modal-body {
  overflow-y: auto;
  padding: 24px;
}
.modal-footer {
  justify-content: flex-end;
  border-top: 1px solid #d7c3b0;
  border-bottom: 0;
}
.client-profile {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px solid #d7c3b0;
}
.client-profile h3 {
  margin: 0 0 4px;
  font:
    700 22px "Libre Caslon Text",
    Georgia,
    serif;
}
.client-profile p {
  margin: 0;
  color: #44474b;
}
.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 24px 0 0;
}
.details-grid dt {
  margin-bottom: 6px;
  color: #7b5647;
}
.details-grid dd {
  margin: 0;
  color: #44474b;
  line-height: 1.5;
}
.client-form {
  display: grid;
  gap: 16px;
}
.client-form label {
  display: grid;
  gap: 6px;
  color: #44474b;
  font:
    600 12px "Work Sans",
    sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.client-form input,
.client-form textarea,
.client-form select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #c4c6cb;
  border-radius: 4px;
  background: #fff;
  color: #1c1c18;
  outline: 0;
  font:
    400 14px Manrope,
    sans-serif;
  letter-spacing: 0;
  text-transform: none;
}
.client-form input:focus,
.client-form textarea:focus,
.client-form select:focus {
  border-color: #7b5647;
  outline: 2px solid rgba(123, 86, 71, 0.2);
}
.client-form textarea {
  resize: vertical;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.client-form .modal-footer {
  margin: 8px -24px -24px;
}
@media (max-width: 800px) {
  .clients-content {
    padding: 28px 20px;
  }
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .filter-panel {
    align-items: stretch;
    flex-direction: column;
    gap: 12px;
  }
}
@media (max-width: 560px) {
  .clients-topbar {
    padding: 0 16px;
  }
  .top-search input {
    width: 190px;
  }
  .clients-content {
    padding: 24px 16px;
  }
  h1 {
    font-size: 38px;
  }
  .page-heading .primary-button {
    width: 100%;
    justify-content: center;
  }
  .details-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px;
  }
  .client-form .modal-footer {
    margin: 8px -16px -16px;
  }
}
</style>

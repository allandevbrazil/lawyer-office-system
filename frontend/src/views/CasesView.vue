<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import {
  casesApi,
  clientsApi,
  type CaseCreateInput,
  type CaseItem,
  type CaseUpdateInput,
  type ClientItem,
} from "@/services/api";
import { confirmAction, showError, showSuccess } from "@/services/alerts";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const search = ref("");
const cases = ref<CaseItem[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");
const activeFilter = ref("todos");
const selectedCase = ref<CaseItem | null>(null);
const clients = ref<ClientItem[]>([]);
const isFormOpen = ref(false);
const editingCase = ref<CaseItem | null>(null);
const isSaving = ref(false);
const isDeleting = ref<string | null>(null);
const formError = ref("");
const canManage = computed(() => auth.user?.role !== "CLIENTE");
const form = ref({
  client_id: "",
  title: "",
  description: "",
  case_number: "",
  court: "",
  jurisdiction: "",
  case_type: "",
  priority: "NORMAL",
  status: "ACTIVE",
});

const filteredCases = computed(() => {
  if (activeFilter.value === "concluidos") {
    return cases.value.filter(
      (item) => item.status === "ARCHIVED" || item.status.toLowerCase().includes("conclu"),
    );
  }
  if (activeFilter.value === "prioridade") {
    return cases.value.filter(
      (item) =>
        ["HIGH", "URGENT"].includes(item.priority) ||
        item.priority.toLowerCase().includes("alta") ||
        item.priority.toLowerCase().includes("urgent"),
    );
  }
  if (activeFilter.value === "abertos") {
    return cases.value.filter(
      (item) => item.status !== "ARCHIVED" && !item.status.toLowerCase().includes("conclu"),
    );
  }
  return cases.value;
});

function openCase(item: CaseItem): void {
  selectedCase.value = item;
}

function clientName(clientId: string): string {
  return clients.value.find((client) => client.id === clientId)?.name ?? clientId.slice(0, 8);
}

function openCreate(): void {
  editingCase.value = null;
  formError.value = "";
  form.value = {
    client_id: clients.value[0]?.id ?? "",
    title: "",
    description: "",
    case_number: "",
    court: "",
    jurisdiction: "",
    case_type: "",
    priority: "NORMAL",
    status: "ACTIVE",
  };
  isFormOpen.value = true;
}

function openEdit(item: CaseItem): void {
  selectedCase.value = null;
  editingCase.value = item;
  formError.value = "";
  form.value = {
    client_id: item.client_id,
    title: item.title,
    description: item.description ?? "",
    case_number: item.case_number ?? "",
    court: item.court ?? "",
    jurisdiction: item.jurisdiction ?? "",
    case_type: item.case_type ?? "",
    priority: item.priority,
    status: item.status,
  };
  isFormOpen.value = true;
}

function closeForm(): void {
  if (!isSaving.value) isFormOpen.value = false;
}

function validateForm(): string {
  if (!editingCase.value && !form.value.client_id) return "Selecione um cliente.";
  if (form.value.title.trim().length < 3) return "O título deve ter pelo menos 3 caracteres.";
  if (form.value.title.trim().length > 240) return "O título deve ter no máximo 240 caracteres.";
  if (form.value.description.length > 4000)
    return "A descrição deve ter no máximo 4.000 caracteres.";
  return "";
}

async function saveCase(): Promise<void> {
  formError.value = validateForm();
  if (formError.value || !auth.accessToken) return;
  isSaving.value = true;
  try {
    if (editingCase.value) {
      const payload: CaseUpdateInput = {
        title: form.value.title.trim(),
        description: form.value.description.trim() || undefined,
        priority: form.value.priority,
        status: form.value.status,
      };
      const updated = await casesApi.update(auth.accessToken, editingCase.value.id, payload);
      cases.value = cases.value.map((item) => (item.id === updated.id ? updated : item));
    } else {
      const payload: CaseCreateInput = {
        client_id: form.value.client_id,
        title: form.value.title.trim(),
        description: form.value.description.trim() || undefined,
        case_number: form.value.case_number.trim() || undefined,
        court: form.value.court.trim() || undefined,
        jurisdiction: form.value.jurisdiction.trim() || undefined,
        case_type: form.value.case_type.trim() || undefined,
        priority: form.value.priority,
      };
      const created = await casesApi.create(auth.accessToken, payload);
      cases.value = [created, ...cases.value];
    }
    isFormOpen.value = false;
  } catch {
    formError.value = "Não foi possível salvar o processo. Verifique os dados e tente novamente.";
  } finally {
    isSaving.value = false;
  }
}

async function deleteCase(item: CaseItem): Promise<void> {
  if (
    !auth.accessToken ||
    !(await confirmAction(
      "Excluir processo?",
      `"${item.title}" será removido. Esta ação não pode ser desfeita.`,
      "Excluir processo",
    ))
  )
    return;
  isDeleting.value = item.id;
  try {
    await casesApi.remove(auth.accessToken, item.id);
    cases.value = cases.value.filter((current) => current.id !== item.id);
    if (selectedCase.value?.id === item.id) closeCase();
    showSuccess("Processo excluído");
  } catch {
    errorMessage.value = "Não foi possível excluir o processo.";
    showError("Exclusão não realizada", errorMessage.value);
  } finally {
    isDeleting.value = null;
  }
}

function closeCase(): void {
  selectedCase.value = null;
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") return;
  if (isFormOpen.value) closeForm();
  else closeCase();
}

function displayStatus(status: string): string {
  if (status === "ARCHIVED" || status.toLowerCase().includes("conclu")) return "Concluído";
  if (status === "SUSPENDED") return "Suspenso";
  return "Aberto";
}

function displayPriority(priority: string): string {
  if (
    priority === "URGENT" ||
    priority === "HIGH" ||
    priority.toLowerCase().includes("alta") ||
    priority.toLowerCase().includes("urgent")
  )
    return "Urgente";
  if (priority === "LOW") return "Baixa";
  return "Normal";
}

function progressFor(item: CaseItem): number {
  return displayStatus(item.status) === "Concluído"
    ? 100
    : displayPriority(item.priority) === "Urgente"
      ? 25
      : 10;
}

async function loadCases(): Promise<void> {
  if (!auth.accessToken) return;
  isLoading.value = true;
  errorMessage.value = "";
  try {
    cases.value = await casesApi.list(auth.accessToken, search.value);
  } catch {
    errorMessage.value =
      "Não foi possível carregar os processos. Faça login novamente se sua sessão expirou.";
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  await loadCases();
  if (canManage.value && auth.accessToken) {
    clients.value = await clientsApi.list(auth.accessToken);
  }
});
watch(search, loadCases);
onMounted(() => window.addEventListener("keydown", handleKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
  <section class="cases-page">
    <header class="cases-topbar">
      <div class="cases-topbar-actions">
        <label class="top-search">
          <span class="material-symbols-outlined">search</span>
          <input v-model="search" aria-label="Buscar processos" placeholder="Buscar..." />
        </label>
        <button class="icon-button" type="button" aria-label="Notificações" title="Notificações">
          <span class="material-symbols-outlined">notifications</span>
        </button>
        <button class="avatar-button" type="button" aria-label="Abrir perfil">RS</button>
      </div>
    </header>

    <main class="cases-content">
      <div class="page-heading">
        <div>
          <p class="eyebrow">Operação jurídica</p>
          <h1>Processos</h1>
          <p class="page-description">Gerencie e acompanhe processos jurídicos ativos.</p>
        </div>
        <div class="heading-actions">
          <button v-if="canManage" class="secondary-button" type="button">
            <span class="material-symbols-outlined">label</span>Gerenciar etiquetas
          </button>
          <button v-if="canManage" class="secondary-button" type="button">
            <span class="material-symbols-outlined">upload</span>Importar processos
          </button>
          <button v-if="canManage" class="primary-button" type="button" @click="openCreate">
            <span class="material-symbols-outlined">add</span>Adicionar processo
          </button>
        </div>
      </div>

      <div class="filters-bar">
        <div class="filter-tools">
          <button
            class="tool-button"
            type="button"
            aria-label="Alternar colunas"
            title="Alternar colunas"
          >
            <span class="material-symbols-outlined">view_column</span>
          </button>
          <button class="tool-button filter-button" type="button">
            <span class="material-symbols-outlined">filter_list</span>Filtros
          </button>
          <span class="filter-divider"></span>
          <button
            v-for="filter in [
              { key: 'todos', label: 'Todos os processos' },
              { key: 'concluidos', label: 'Concluídos' },
              { key: 'prioridade', label: 'Alta prioridade' },
              { key: 'abertos', label: 'Processos abertos' },
            ]"
            :key="filter.key"
            class="filter-pill"
            :class="{ selected: activeFilter === filter.key }"
            type="button"
            @click="activeFilter = filter.key"
          >
            {{ filter.label }}
          </button>
        </div>
        <label class="table-search">
          <input v-model="search" aria-label="Buscar na tabela" placeholder="Buscar..." />
          <span class="material-symbols-outlined">search</span>
        </label>
      </div>

      <p v-if="isLoading" class="state-message">Carregando processos...</p>
      <p v-else-if="errorMessage" class="state-message form-error" role="alert">
        {{ errorMessage }}
      </p>
      <div v-else class="table-shell">
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Título</th>
                <th>Cliente</th>
                <th>Valor</th>
                <th>Data de início</th>
                <th>Prazo</th>
                <th>Progresso</th>
                <th>Status</th>
                <th class="actions-heading">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredCases" :key="item.id">
                <td class="muted-cell">{{ item.id.slice(0, 8) }}</td>
                <td>
                  <button class="case-title" type="button" @click="openCase(item)">
                    {{ item.title }}</button
                  ><span
                    v-if="displayPriority(item.priority) === 'Urgente'"
                    class="status-tag urgent"
                    >Urgente</span
                  ><span v-else class="status-tag">No prazo</span>
                </td>
                <td class="muted-cell">{{ item.client_id ? clientName(item.client_id) : "-" }}</td>
                <td class="muted-cell">-</td>
                <td class="muted-cell">-</td>
                <td class="muted-cell">-</td>
                <td>
                  <div class="progress-track">
                    <span :style="{ width: `${progressFor(item)}%` }"></span>
                  </div>
                </td>
                <td class="muted-cell">{{ displayStatus(item.status) }}</td>
                <td class="row-actions">
                  <button
                    type="button"
                    aria-label="Visualizar processo"
                    title="Visualizar"
                    @click="openCase(item)"
                  >
                    <span class="material-symbols-outlined">visibility</span></button
                  ><button
                    v-if="canManage"
                    type="button"
                    aria-label="Editar processo"
                    title="Editar"
                    @click="openEdit(item)"
                  >
                    <span class="material-symbols-outlined">edit</span></button
                  ><button
                    v-if="canManage"
                    type="button"
                    aria-label="Excluir processo"
                    title="Excluir"
                    :disabled="isDeleting === item.id"
                    @click="deleteCase(item)"
                  >
                    <span class="material-symbols-outlined">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="!filteredCases.length" class="empty-state">Nenhum processo encontrado.</p>
      </div>
    </main>

    <div v-if="selectedCase" class="modal-backdrop" role="presentation" @click.self="closeCase">
      <section
        class="case-modal"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`case-title-${selectedCase.id}`"
      >
        <header class="modal-header">
          <h2 :id="`case-title-${selectedCase.id}`">
            Detalhes do Processo: {{ selectedCase.title }}
          </h2>
          <button class="icon-button" type="button" aria-label="Fechar detalhes" @click="closeCase">
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div class="modal-body">
          <section class="modal-section">
            <h3>Informações gerais</h3>
            <div class="info-grid">
              <div>
                <small>ID</small><strong>{{ selectedCase.id.slice(0, 8) }}</strong>
              </div>
              <div>
                <small>Status</small><strong>{{ displayStatus(selectedCase.status) }}</strong>
              </div>
              <div><small>Categoria</small><strong>Jurídico</strong></div>
              <div class="priority-box">
                <small>Prioridade</small
                ><strong>{{ displayPriority(selectedCase.priority) }}</strong>
              </div>
            </div>
          </section>
          <section class="modal-section">
            <h3>Descrição do processo</h3>
            <div class="description-box">
              {{
                selectedCase.description ||
                "Processo cadastrado no LegalSuite. Consulte os documentos, atividades e informações relacionadas a este atendimento."
              }}
            </div>
          </section>
          <div class="modal-columns">
            <section class="modal-section">
              <h3>Financeiro</h3>
              <ul class="detail-list">
                <li><span>Valor estimado:</span><strong>-</strong></li>
                <li><span>Faturas pendentes:</span><strong>0</strong></li>
              </ul>
            </section>
            <section class="modal-section">
              <h3>Cronograma</h3>
              <ul class="detail-list">
                <li><span>Início:</span><strong>-</strong></li>
                <li><span>Prazo:</span><strong>-</strong></li>
              </ul>
            </section>
          </div>
          <section class="modal-section">
            <h3>Cliente</h3>
            <div class="team-chip">
              <span>CL</span><strong>{{ clientName(selectedCase.client_id) }}</strong>
            </div>
          </section>
          <section class="modal-section">
            <h3>Atividades recentes</h3>
            <div class="activity-item">
              <span class="activity-dot"></span>
              <div><strong>Processo consultado</strong><small>Agora</small></div>
            </div>
          </section>
        </div>
        <footer class="modal-footer">
          <button class="secondary-button" type="button" @click="closeCase">Fechar</button
          ><button
            v-if="canManage"
            class="primary-button"
            type="button"
            @click="openEdit(selectedCase)"
          >
            Editar processo
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
        class="case-modal form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="case-form-title"
      >
        <header class="modal-header">
          <h2 id="case-form-title">{{ editingCase ? "Editar processo" : "Adicionar processo" }}</h2>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar formulário"
            @click="closeForm"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <form class="modal-body case-form" novalidate @submit.prevent="saveCase">
          <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
          <label v-if="!editingCase"
            >Cliente<select v-model="form.client_id" required>
              <option value="" disabled>Selecione um cliente</option>
              <option v-for="client in clients" :key="client.id" :value="client.id">
                {{ client.name }}
              </option>
            </select></label
          >
          <label
            >Título<input
              v-model="form.title"
              required
              minlength="3"
              maxlength="240"
              placeholder="Ex.: Ação de cobrança"
          /></label>
          <label
            >Descrição<textarea
              v-model="form.description"
              maxlength="4000"
              rows="4"
              placeholder="Descreva o processo"
            ></textarea>
          </label>
          <div class="form-grid">
            <label>Número do processo<input v-model="form.case_number" maxlength="64" /></label
            ><label>Tipo<input v-model="form.case_type" maxlength="120" /></label
            ><label>Vara ou tribunal<input v-model="form.court" maxlength="200" /></label
            ><label>Jurisdição<input v-model="form.jurisdiction" maxlength="160" /></label
            ><label
              >Prioridade<select v-model="form.priority">
                <option value="LOW">Baixa</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">Alta</option>
                <option value="URGENT">Urgente</option>
              </select></label
            ><label v-if="editingCase"
              >Status<select v-model="form.status">
                <option value="ACTIVE">Aberto</option>
                <option value="SUSPENDED">Suspenso</option>
                <option value="ARCHIVED">Arquivado</option>
              </select></label
            >
          </div>
          <footer class="modal-footer">
            <button class="secondary-button" type="button" @click="closeForm">Cancelar</button
            ><button class="primary-button" type="submit" :disabled="isSaving">
              {{ isSaving ? "Salvando..." : "Salvar processo" }}
            </button>
          </footer>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.cases-page {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope, sans-serif;
}
.cases-topbar {
  height: 80px;
  padding: 0 40px 0 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(196, 198, 203, 0.45);
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fcf9f2;
}
h1,
h2 {
  font-family: "Libre Caslon Text", Georgia, serif;
}
.cases-topbar-actions,
.heading-actions,
.filter-tools,
.modal-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}
.top-search,
.table-search {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #75777c;
}
.top-search input {
  width: 190px;
  border: 0;
  border-bottom: 1px solid #c4c6cb;
  background: transparent;
  padding: 8px 0;
  outline: 0;
}
.top-search input:focus,
.table-search input:focus {
  border-color: #7b5647;
}
.icon-button,
.avatar-button,
.row-actions button,
.tool-button {
  border: 0;
  background: transparent;
  color: #44474b;
  cursor: pointer;
}
.icon-button {
  padding: 6px;
}
.avatar-button {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #121c26;
  color: #fff;
  font:
    600 12px "Work Sans",
    sans-serif;
}
.cases-content {
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
.modal-section h3,
th,
small {
  font:
    600 12px/1.4 "Work Sans",
    sans-serif;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.eyebrow {
  color: #7b5647;
  margin: 0 0 8px;
}
h1 {
  margin: 0;
  font-size: 48px;
  line-height: 1.1;
}
.page-description {
  margin: 10px 0 0;
  color: #44474b;
}
.primary-button,
.secondary-button,
.tool-button,
.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 4px;
  cursor: pointer;
  font:
    600 14px "Work Sans",
    sans-serif;
  white-space: nowrap;
}
.primary-button,
.secondary-button {
  padding: 11px 16px;
  border: 1px solid #d7c3b0;
}
.primary-button {
  background: #7b5647;
  color: #fff;
  border-color: #7b5647;
}
.secondary-button {
  background: #fff;
  color: #1c1c18;
}
.primary-button:hover,
.secondary-button:hover {
  filter: brightness(0.96);
}
.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 8px;
  margin-bottom: 24px;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
}
.tool-button {
  padding: 8px 12px;
  background: #f1eee7;
  border: 1px solid rgba(196, 198, 203, 0.5);
}
.filter-divider {
  width: 1px;
  height: 24px;
  background: #c4c6cb;
  margin: 0 4px;
}
.filter-pill {
  border: 1px solid rgba(196, 198, 203, 0.7);
  padding: 8px 13px;
  color: #44474b;
  background: transparent;
}
.filter-pill.selected {
  color: #7b5647;
  background: rgba(254, 204, 185, 0.25);
  border-color: #feccb9;
}
.table-search {
  padding-right: 8px;
  background: #f6f3ec;
  border: 1px solid #d7c3b0;
  border-radius: 999px;
}
.table-search input {
  width: 190px;
  padding: 9px 0 9px 14px;
  border: 0;
  outline: 0;
  background: transparent;
}
.table-shell {
  overflow: hidden;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 10px;
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
  text-align: left;
}
th {
  padding: 16px 20px;
  color: #44474b;
  background: rgba(246, 243, 236, 0.6);
  border-bottom: 1px solid #d7c3b0;
}
td {
  padding: 18px 20px;
  border-bottom: 1px solid rgba(215, 195, 176, 0.45);
  font-size: 14px;
  vertical-align: middle;
}
tbody tr:hover {
  background: rgba(246, 243, 236, 0.5);
}
.muted-cell {
  color: #44474b;
}
.case-title {
  display: block;
  border: 0;
  padding: 0;
  margin-bottom: 7px;
  background: transparent;
  color: #1c1c18;
  cursor: pointer;
  font:
    500 15px Manrope,
    sans-serif;
  text-align: left;
}
.case-title:hover {
  color: #7b5647;
}
.status-tag {
  display: inline-block;
  padding: 3px 7px;
  border-radius: 3px;
  background: #e5e2db;
  color: #44474b;
  font:
    700 10px "Work Sans",
    sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.status-tag.urgent {
  background: #ffdad6;
  color: #93000a;
}
.progress-track {
  width: 90px;
  height: 6px;
  background: #e5e2db;
  border-radius: 999px;
}
.progress-track span {
  display: block;
  height: 100%;
  background: #121c26;
  border-radius: inherit;
}
.row-actions {
  text-align: right;
  white-space: nowrap;
}
.row-actions button {
  padding: 4px;
}
.row-actions button:hover {
  color: #7b5647;
}
.actions-heading {
  text-align: right;
}
.state-message,
.empty-state {
  padding: 32px;
  color: #44474b;
}
.form-error {
  color: #ba1a1a;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(18, 28, 38, 0.4);
  backdrop-filter: blur(4px);
}
.case-modal {
  width: min(900px, 100%);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fcf9f2;
  border: 1px solid #d7c3b0;
  border-radius: 10px;
  box-shadow: 0 24px 60px rgba(18, 28, 38, 0.2);
}
.modal-header,
.modal-footer {
  padding: 16px 24px;
  background: #f6f3ec;
  border-bottom: 1px solid #d7c3b0;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
h2 {
  margin: 0;
  font-size: 24px;
}
.modal-body {
  overflow-y: auto;
  padding: 24px;
}
.case-form {
  display: grid;
  gap: 16px;
}
.case-form label {
  display: grid;
  gap: 6px;
  color: #44474b;
  font:
    600 12px "Work Sans",
    sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.case-form input,
.case-form textarea,
.case-form select {
  width: 100%;
  border: 1px solid #c4c6cb;
  border-radius: 4px;
  padding: 10px 12px;
  color: #1c1c18;
  background: #fff;
  font:
    400 14px Manrope,
    sans-serif;
  letter-spacing: 0;
  text-transform: none;
}
.case-form input:focus,
.case-form textarea:focus,
.case-form select:focus {
  outline: 2px solid rgba(123, 86, 71, 0.25);
  border-color: #7b5647;
}
.case-form textarea {
  resize: vertical;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.case-form .modal-footer {
  margin: 8px -24px -24px;
}
.primary-button:disabled,
.row-actions button:disabled {
  cursor: wait;
  opacity: 0.6;
}
.modal-footer {
  justify-content: flex-end;
  border-top: 1px solid #d7c3b0;
  border-bottom: 0;
}
.modal-section {
  margin-bottom: 24px;
}
.modal-section h3 {
  margin: 0 0 12px;
  color: #7b5647;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.info-grid > div,
.description-box {
  padding: 13px;
  background: #f6f3ec;
  border: 1px solid rgba(196, 198, 203, 0.35);
  border-radius: 4px;
}
.info-grid small,
.info-grid strong {
  display: block;
}
.info-grid small {
  color: #44474b;
  margin-bottom: 5px;
}
.priority-box {
  background: rgba(255, 218, 214, 0.4) !important;
  border-color: #ffdad6 !important;
}
.priority-box strong {
  color: #ba1a1a;
}
.description-box {
  color: #44474b;
  line-height: 1.6;
}
.modal-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}
.detail-list {
  padding: 0;
  margin: 0;
  list-style: none;
}
.detail-list li {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(196, 198, 203, 0.5);
  font-size: 14px;
}
.detail-list span {
  color: #44474b;
}
.team-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px 7px 7px;
  border: 1px solid rgba(196, 198, 203, 0.5);
  border-radius: 999px;
  background: #f1eee7;
}
.team-chip span {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border-radius: 50%;
  background: #bdc7d5;
  font:
    700 10px "Work Sans",
    sans-serif;
}
.activity-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.activity-dot {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 50%;
  background: #7b5647;
}
.activity-item strong,
.activity-item small {
  display: block;
}
.activity-item small {
  margin-top: 3px;
  color: #44474b;
  letter-spacing: 0;
  text-transform: none;
}
@media (max-width: 900px) {
  .cases-content {
    padding: 28px 20px;
  }
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .heading-actions {
    flex-wrap: wrap;
  }
  .filters-bar {
    align-items: stretch;
    flex-direction: column;
  }
  .filter-tools {
    flex-wrap: wrap;
  }
  .table-search {
    align-self: flex-start;
  }
}
@media (max-width: 600px) {
  .cases-topbar {
    height: 68px;
    padding: 0 20px;
  }
  .top-search {
    display: none;
  }
  h1 {
    font-size: 38px;
  }
  .cases-content {
    padding: 24px 16px;
  }
  .heading-actions {
    display: grid;
    width: 100%;
    grid-template-columns: 1fr;
  }
  .heading-actions button {
    justify-content: center;
  }
  .info-grid,
  .modal-columns {
    grid-template-columns: 1fr 1fr;
  }
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px;
  }
  h2 {
    font-size: 20px;
  }
}
</style>

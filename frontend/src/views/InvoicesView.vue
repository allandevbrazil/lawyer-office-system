<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import {
  clientsApi,
  invoicesApi,
  type ClientItem,
  type Invoice,
  type InvoiceCreateInput,
} from "@/services/api";
import { confirmAction, showError, showSuccess } from "@/services/alerts";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const invoices = ref<Invoice[]>([]);
const clients = ref<ClientItem[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");
const search = ref("");
const statusFilter = ref("ALL");
const selectedInvoice = ref<Invoice | null>(null);
const isFormOpen = ref(false);
const isSaving = ref(false);
const isDeleting = ref<string | null>(null);
const formError = ref("");
const form = ref({
  client_id: "",
  number: "",
  description: "",
  discount: "0.00",
  due_date: "",
  item_description: "Honorários advocatícios",
  quantity: "1",
  unit_price: "0.00",
});
const canManage = computed(() => auth.user?.role !== "CLIENTE");

const filteredInvoices = computed(() =>
  invoices.value.filter((invoice) => {
    const term = search.value.toLowerCase().trim();
    const matchesSearch =
      !term ||
      invoice.number.toLowerCase().includes(term) ||
      clientName(invoice.client_id).toLowerCase().includes(term);
    return matchesSearch && (statusFilter.value === "ALL" || invoice.status === statusFilter.value);
  }),
);
const totals = computed(() => ({
  paid: invoices.value
    .filter((invoice) => invoice.status === "PAID")
    .reduce((sum, invoice) => sum + Number(invoice.total), 0),
  overdue: invoices.value
    .filter((invoice) => invoice.status === "OVERDUE")
    .reduce((sum, invoice) => sum + Number(invoice.total), 0),
  open: invoices.value
    .filter((invoice) => ["PENDING", "OVERDUE"].includes(invoice.status))
    .reduce((sum, invoice) => sum + Number(invoice.total), 0),
}));

function money(value: string | number): string {
  return Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function clientName(clientId: string): string {
  return clients.value.find((client) => client.id === clientId)?.name ?? clientId.slice(0, 8);
}
function statusLabel(status: string): string {
  return (
    {
      PENDING: "Aguardando vencimento",
      PAID: "Pago em dia",
      OVERDUE: "Vencido",
      CANCELLED: "Cancelada",
    }[status] ?? status
  );
}
function statusClass(status: string): string {
  return status.toLowerCase();
}
function closeModal(): void {
  selectedInvoice.value = null;
}
function openCreate(): void {
  formError.value = "";
  form.value = {
    client_id: clients.value[0]?.id ?? "",
    number: `FAT-${String(invoices.value.length + 1).padStart(6, "0")}`,
    description: "",
    discount: "0.00",
    due_date: new Date(Date.now() + 15 * 86400000).toISOString().slice(0, 10),
    item_description: "Honorários advocatícios",
    quantity: "1",
    unit_price: "0.00",
  };
  isFormOpen.value = true;
}
function closeForm(): void {
  if (!isSaving.value) isFormOpen.value = false;
}
function validateForm(): string {
  if (!form.value.client_id) return "Selecione um cliente.";
  if (form.value.number.trim().length < 2) return "Informe o número da fatura.";
  if (!form.value.due_date) return "Informe a data de vencimento.";
  if (Number(form.value.quantity) <= 0 || Number(form.value.unit_price) < 0)
    return "Quantidade e valor precisam ser válidos.";
  if (form.value.item_description.trim().length < 2) return "Descreva o item da fatura.";
  return "";
}

async function loadData(): Promise<void> {
  if (!auth.accessToken) return;
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const invoiceData = await invoicesApi.list(auth.accessToken);
    invoices.value = invoiceData;
    if (canManage.value) clients.value = await clientsApi.list(auth.accessToken);
  } catch {
    errorMessage.value = "Não foi possível carregar as faturas.";
  } finally {
    isLoading.value = false;
  }
}
async function saveInvoice(): Promise<void> {
  formError.value = validateForm();
  if (formError.value || !auth.accessToken) return;
  isSaving.value = true;
  try {
    const payload: InvoiceCreateInput = {
      client_id: form.value.client_id,
      number: form.value.number.trim(),
      description: form.value.description.trim() || undefined,
      discount: form.value.discount || "0.00",
      due_date: form.value.due_date,
      items: [
        {
          description: form.value.item_description.trim(),
          quantity: form.value.quantity,
          unit_price: form.value.unit_price,
        },
      ],
    };
    const created = await invoicesApi.create(auth.accessToken, payload);
    invoices.value = [created, ...invoices.value];
    isFormOpen.value = false;
  } catch {
    formError.value = "Não foi possível criar a fatura. Verifique os dados.";
  } finally {
    isSaving.value = false;
  }
}
async function updateStatus(invoice: Invoice, status: string): Promise<void> {
  if (!auth.accessToken || status === invoice.status) return;
  try {
    const updated = await invoicesApi.updateStatus(auth.accessToken, invoice.id, { status });
    invoices.value = invoices.value.map((item) => (item.id === updated.id ? updated : item));
    if (selectedInvoice.value?.id === updated.id) selectedInvoice.value = updated;
  } catch {
    errorMessage.value = "Não foi possível atualizar o status da fatura.";
  }
}
async function deleteInvoice(invoice: Invoice): Promise<void> {
  if (
    !auth.accessToken ||
    !(await confirmAction(
      "Excluir fatura?",
      `"${invoice.number}" será removida. Esta ação não pode ser desfeita.`,
      "Excluir fatura",
    ))
  )
    return;
  isDeleting.value = invoice.id;
  try {
    await invoicesApi.remove(auth.accessToken, invoice.id);
    invoices.value = invoices.value.filter((item) => item.id !== invoice.id);
    closeModal();
    showSuccess("Fatura excluída");
  } catch {
    errorMessage.value = "Não foi possível excluir a fatura.";
    showError("Exclusão não realizada", errorMessage.value);
  } finally {
    isDeleting.value = null;
  }
}
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    if (isFormOpen.value) closeForm();
    else closeModal();
  }
}
onMounted(loadData);
onMounted(() => window.addEventListener("keydown", handleKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
  <section class="invoices-page">
    <header class="invoices-topbar">
      <label class="top-search"
        ><span class="material-symbols-outlined">search</span
        ><input v-model="search" aria-label="Buscar faturas" placeholder="Buscar..."
      /></label>
      <div class="top-actions">
        <button class="icon-button" type="button" aria-label="Notificações">
          <span class="material-symbols-outlined">notifications</span></button
        ><button class="icon-button" type="button" aria-label="Ajuda">
          <span class="material-symbols-outlined">help_outline</span></button
        ><button class="avatar-button" type="button">RS</button>
      </div>
    </header>
    <main class="invoices-content">
      <div class="page-heading">
        <div>
          <p class="eyebrow">Financeiro</p>
          <h1>Faturas</h1>
          <p class="description">Gerencie e acompanhe o faturamento do escritório.</p>
        </div>
        <div class="heading-actions">
          <button v-if="canManage" class="primary-button" type="button" @click="openCreate">
            <span class="material-symbols-outlined">add</span>Criar nova fatura</button
          ><button class="secondary-button" type="button">
            <span class="material-symbols-outlined">payments</span>Pagamentos em lote</button
          ><button class="secondary-button" type="button">
            <span class="material-symbols-outlined">download</span>Exportação
          </button>
        </div>
      </div>
      <div class="summary-grid">
        <article class="summary-card paid">
          <span class="material-symbols-outlined">check_circle</span>
          <div>
            <small>Faturas pagas</small><strong>{{ money(totals.paid) }}</strong>
          </div>
        </article>
        <article class="summary-card overdue">
          <span class="material-symbols-outlined">error</span>
          <div>
            <small>Faturas em atraso</small><strong>{{ money(totals.overdue) }}</strong>
          </div>
        </article>
        <article class="summary-card open">
          <span class="material-symbols-outlined">pending_actions</span>
          <div>
            <small>Faturas em aberto</small><strong>{{ money(totals.open) }}</strong>
          </div>
        </article>
      </div>
      <div class="controls">
        <select v-model="statusFilter" aria-label="Filtrar faturas">
          <option value="ALL">Todos os status</option>
          <option value="PENDING">Em aberto</option>
          <option value="PAID">Pagas</option>
          <option value="OVERDUE">Em atraso</option>
          <option value="CANCELLED">Canceladas</option></select
        ><span class="results-label">{{ filteredInvoices.length }} resultado(s)</span
        ><button class="filter-button" type="button">
          <span class="material-symbols-outlined">filter_list</span>Filtros
        </button>
      </div>
      <p v-if="isLoading" class="state-message">Carregando faturas...</p>
      <p v-else-if="errorMessage" class="state-message form-error" role="alert">
        {{ errorMessage }}
      </p>
      <div v-else class="table-shell">
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Fatura #</th>
                <th>Valor</th>
                <th>Data</th>
                <th>Cliente</th>
                <th>Vencimento</th>
                <th>Status</th>
                <th class="actions-heading">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invoice in filteredInvoices" :key="invoice.id">
                <td>
                  <button class="invoice-number" type="button" @click="selectedInvoice = invoice">
                    {{ invoice.number }}
                  </button>
                </td>
                <td>{{ money(invoice.total) }}</td>
                <td>{{ invoice.issued_at.slice(0, 10) }}</td>
                <td>{{ clientName(invoice.client_id) }}</td>
                <td>{{ invoice.due_date }}</td>
                <td>
                  <select
                    v-if="canManage"
                    class="status-select"
                    :class="statusClass(invoice.status)"
                    :value="invoice.status"
                    aria-label="Status da fatura"
                    @change="updateStatus(invoice, ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="PENDING">Aguardando vencimento</option>
                    <option value="PAID">Pago em dia</option>
                    <option value="OVERDUE">Vencido</option>
                    <option value="CANCELLED">Cancelada</option></select
                  ><span v-else class="status-text">{{ statusLabel(invoice.status) }}</span>
                </td>
                <td class="row-actions">
                  <button
                    type="button"
                    aria-label="Visualizar fatura"
                    title="Visualizar"
                    @click="selectedInvoice = invoice"
                  >
                    <span class="material-symbols-outlined">visibility</span></button
                  ><button
                    v-if="canManage"
                    type="button"
                    aria-label="Excluir fatura"
                    title="Excluir"
                    :disabled="isDeleting === invoice.id"
                    @click="deleteInvoice(invoice)"
                  >
                    <span class="material-symbols-outlined">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="!filteredInvoices.length" class="empty-state">Nenhuma fatura encontrada.</p>
        <div v-else class="table-footer">Mostrando {{ filteredInvoices.length }} resultado(s)</div>
      </div>
    </main>
    <div v-if="selectedInvoice" class="modal-backdrop" role="presentation" @click.self="closeModal">
      <section
        class="invoice-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="invoice-details-title"
      >
        <header class="modal-header">
          <h2 id="invoice-details-title">Detalhes da fatura {{ selectedInvoice.number }}</h2>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar detalhes"
            @click="closeModal"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div class="modal-body">
          <dl class="details-grid">
            <div>
              <dt>Cliente</dt>
              <dd>{{ clientName(selectedInvoice.client_id) }}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{{ statusLabel(selectedInvoice.status) }}</dd>
            </div>
            <div>
              <dt>Subtotal</dt>
              <dd>{{ money(selectedInvoice.subtotal) }}</dd>
            </div>
            <div>
              <dt>Desconto</dt>
              <dd>{{ money(selectedInvoice.discount) }}</dd>
            </div>
            <div>
              <dt>Total</dt>
              <dd class="total-value">{{ money(selectedInvoice.total) }}</dd>
            </div>
            <div>
              <dt>Vencimento</dt>
              <dd>{{ selectedInvoice.due_date }}</dd>
            </div>
          </dl>
          <h3>Itens</h3>
          <ul class="items-list">
            <li v-for="item in selectedInvoice.items" :key="item.id">
              <span>{{ item.description }} ({{ item.quantity }}x)</span
              ><strong>{{ money(item.amount) }}</strong>
            </li>
          </ul>
        </div>
        <footer class="modal-footer">
          <button class="secondary-button" type="button" @click="closeModal">Fechar</button
          ><button
            v-if="canManage"
            class="danger-button"
            type="button"
            @click="deleteInvoice(selectedInvoice)"
          >
            Excluir fatura
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
        class="invoice-modal form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="invoice-form-title"
      >
        <header class="modal-header">
          <h2 id="invoice-form-title">Criar nova fatura</h2>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar formulário"
            @click="closeForm"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <form class="modal-body invoice-form" novalidate @submit.prevent="saveInvoice">
          <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
          <div class="form-grid">
            <label
              >Cliente<select v-model="form.client_id" required>
                <option value="" disabled>Selecione um cliente</option>
                <option v-for="client in clients" :key="client.id" :value="client.id">
                  {{ client.name }}
                </option>
              </select></label
            ><label>Número<input v-model="form.number" required maxlength="40" /></label
            ><label>Vencimento<input v-model="form.due_date" required type="date" /></label
            ><label
              >Desconto<input v-model="form.discount" type="number" min="0" step="0.01"
            /></label>
          </div>
          <label>Descrição<input v-model="form.description" maxlength="500" /></label>
          <div class="item-box">
            <h3>Item da fatura</h3>
            <div class="form-grid">
              <label>Descrição<input v-model="form.item_description" required /></label
              ><label
                >Quantidade<input
                  v-model="form.quantity"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required /></label
              ><label
                >Valor unitário<input
                  v-model="form.unit_price"
                  type="number"
                  min="0"
                  step="0.01"
                  required
              /></label>
            </div>
          </div>
          <footer class="modal-footer">
            <button class="secondary-button" type="button" @click="closeForm">Cancelar</button
            ><button class="primary-button" type="submit" :disabled="isSaving">
              {{ isSaving ? "Salvando..." : "Salvar fatura" }}
            </button>
          </footer>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.invoices-page {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope, sans-serif;
}
.invoices-topbar {
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
  align-items: center;
  gap: 8px;
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
.invoices-content {
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
small,
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
.description {
  margin: 10px 0 0;
  color: #44474b;
}
.heading-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.primary-button,
.secondary-button,
.danger-button,
.filter-button {
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
.secondary-button,
.filter-button {
  background: #fff;
  color: #1c1c18;
}
.danger-button {
  background: #ffdad6;
  border-color: #ffdad6;
  color: #93000a;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}
.summary-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border: 1px solid #d7c3b0;
  background: #fff;
  border-radius: 4px;
}
.summary-card > span {
  font-size: 24px;
}
.summary-card small,
.summary-card strong {
  display: block;
}
.summary-card strong {
  margin-top: 8px;
  font:
    600 24px "Libre Caslon Text",
    Georgia,
    serif;
}
.summary-card.paid {
  color: #2e7d32;
}
.summary-card.overdue {
  color: #d32f2f;
}
.summary-card.open {
  color: #f57c00;
}
.summary-card div {
  color: #1c1c18;
}
.controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.controls select,
.filter-button {
  padding: 9px 12px;
  border: 1px solid #c4c6cb;
  border-radius: 4px;
  background: #fff;
  color: #44474b;
}
.results-label {
  flex: 1;
  color: #44474b;
  font-size: 14px;
}
.table-shell {
  overflow: hidden;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 4px;
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  min-width: 920px;
  border-collapse: collapse;
  text-align: left;
}
th {
  padding: 16px;
  color: #44474b;
  background: #f6f3ec;
  border-bottom: 1px solid #d7c3b0;
  white-space: nowrap;
}
td {
  padding: 16px;
  border-bottom: 1px solid rgba(215, 195, 176, 0.6);
  font-size: 14px;
  white-space: nowrap;
}
.invoice-number {
  border: 0;
  padding: 0;
  background: transparent;
  color: #121c26;
  cursor: pointer;
  font-weight: 600;
}
.invoice-number:hover {
  color: #7b5647;
}
.status-select {
  padding: 6px 8px;
  border: 0;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.status-select.pending {
  background: #fff3e0;
  color: #f57c00;
}
.status-select.paid {
  background: #e8f5e9;
  color: #2e7d32;
}
.status-select.overdue {
  background: #fce4e4;
  color: #d32f2f;
}
.status-select.cancelled {
  background: #e5e2db;
  color: #44474b;
}
.actions-heading,
.row-actions {
  text-align: right;
}
.row-actions {
  white-space: nowrap;
}
.row-actions button:hover {
  color: #7b5647;
}
.row-actions button:disabled {
  opacity: 0.5;
  cursor: wait;
}
.table-footer,
.state-message,
.empty-state {
  padding: 18px 16px;
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
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(18, 28, 38, 0.4);
  backdrop-filter: blur(4px);
}
.invoice-modal {
  width: min(800px, 100%);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 0 0 24px;
}
.details-grid dt {
  margin-bottom: 6px;
  color: #7b5647;
}
.details-grid dd {
  margin: 0;
  color: #44474b;
}
.total-value {
  color: #7b5647;
  font-weight: 700;
}
.modal-body h3 {
  margin: 20px 0 10px;
  font:
    600 12px "Work Sans",
    sans-serif;
  color: #7b5647;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.items-list {
  padding: 0;
  margin: 0;
  list-style: none;
}
.items-list li {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #d7c3b0;
}
.invoice-form {
  display: grid;
  gap: 16px;
}
.invoice-form label {
  display: grid;
  gap: 6px;
  color: #44474b;
  font:
    600 12px "Work Sans",
    sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.invoice-form input,
.invoice-form textarea,
.invoice-form select {
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
.invoice-form input:focus,
.invoice-form select:focus {
  border-color: #7b5647;
  outline: 2px solid rgba(123, 86, 71, 0.2);
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.item-box {
  padding: 16px;
  background: #f6f3ec;
  border: 1px solid #d7c3b0;
  border-radius: 4px;
}
.item-box h3 {
  margin-top: 0;
}
.invoice-form .modal-footer {
  margin: 8px -24px -24px;
}
@media (max-width: 900px) {
  .invoices-content {
    padding: 28px 20px;
  }
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .summary-grid {
    grid-template-columns: 1fr;
  }
  .heading-actions {
    width: 100%;
  }
}
@media (max-width: 560px) {
  .invoices-topbar {
    padding: 0 16px;
  }
  .top-search input {
    width: 190px;
  }
  .invoices-content {
    padding: 24px 16px;
  }
  h1 {
    font-size: 38px;
  }
  .heading-actions {
    display: grid;
    grid-template-columns: 1fr;
  }
  .heading-actions button {
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
  .invoice-form .modal-footer {
    margin: 8px -16px -16px;
  }
}
</style>

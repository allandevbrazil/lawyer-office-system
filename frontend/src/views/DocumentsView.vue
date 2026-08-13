<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { clientsApi, documentsApi, type ClientItem, type DocumentItem } from "@/services/api";
import { confirmAction, showError, showSuccess } from "@/services/alerts";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const documents = ref<DocumentItem[]>([]);
const clients = ref<ClientItem[]>([]);
const search = ref("");
const visibilityFilter = ref("ALL");
const isLoading = ref(true);
const errorMessage = ref("");
const selectedDocument = ref<DocumentItem | null>(null);
const previewUrl = ref("");
const isUploadOpen = ref(false);
const selectedFile = ref<File | null>(null);
const uploadClientId = ref("");
const uploadVisibility = ref("INTERNAL");
const isUploading = ref(false);
const isDeleting = ref<string | null>(null);
const formError = ref("");
const canManage = computed(() => auth.user?.role !== "CLIENTE");

const filteredDocuments = computed(() =>
  documents.value.filter((document) => {
    const term = search.value.toLowerCase().trim();
    return (
      (!term ||
        document.file_name.toLowerCase().includes(term) ||
        document.mime_type.toLowerCase().includes(term)) &&
      (visibilityFilter.value === "ALL" || document.visibility === visibilityFilter.value)
    );
  }),
);

function clientName(id: string | null): string {
  return id ? (clients.value.find((client) => client.id === id)?.name ?? id.slice(0, 8)) : "-";
}
function fileIcon(document: DocumentItem): string {
  if (document.mime_type === "application/pdf") return "picture_as_pdf";
  if (document.mime_type.startsWith("image/")) return "image";
  return "description";
}
function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
function fileDate(value: string): string {
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "medium", timeStyle: "short" });
}
function closeDocument(): void {
  selectedDocument.value = null;
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = "";
}

async function loadDocuments(): Promise<void> {
  if (!auth.accessToken) return;
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const documentData = await documentsApi.list(auth.accessToken);
    documents.value = documentData;
    if (canManage.value) clients.value = await clientsApi.list(auth.accessToken);
  } catch {
    errorMessage.value = "Não foi possível carregar os documentos.";
  } finally {
    isLoading.value = false;
  }
}
async function openDocument(document: DocumentItem): Promise<void> {
  if (!auth.accessToken) return;
  closeDocument();
  selectedDocument.value = document;
  try {
    const blob = await documentsApi.download(auth.accessToken, document.id);
    previewUrl.value = URL.createObjectURL(blob);
  } catch {
    errorMessage.value = "Não foi possível visualizar este documento.";
  }
}
async function downloadDocument(document: DocumentItem): Promise<void> {
  if (!auth.accessToken) return;
  try {
    const blob = await documentsApi.download(auth.accessToken, document.id);
    const url = URL.createObjectURL(blob);
    const anchor = window.document.createElement("a");
    anchor.href = url;
    anchor.download = document.file_name;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch {
    errorMessage.value = "Não foi possível baixar o documento.";
  }
}
function chooseFile(event: Event): void {
  selectedFile.value = (event.target as HTMLInputElement).files?.[0] ?? null;
}
function validateUpload(): string {
  if (!selectedFile.value) return "Selecione um arquivo.";
  if (selectedFile.value.size > 10 * 1024 * 1024) return "O arquivo deve ter no máximo 10 MB.";
  if (
    !["application/pdf", "image/jpeg", "image/png", "text/plain"].includes(selectedFile.value.type)
  )
    return "Tipo de arquivo não suportado. Use PDF, JPG, PNG ou TXT.";
  if (!uploadClientId.value) return "Selecione um cliente para vincular o documento.";
  return "";
}
async function uploadDocument(): Promise<void> {
  formError.value = validateUpload();
  if (formError.value || !auth.accessToken || !selectedFile.value) return;
  isUploading.value = true;
  try {
    const created = await documentsApi.upload(auth.accessToken, {
      file: selectedFile.value,
      client_id: uploadClientId.value,
      visibility: uploadVisibility.value,
    });
    documents.value = [created, ...documents.value];
    isUploadOpen.value = false;
    selectedFile.value = null;
  } catch {
    formError.value = "Não foi possível fazer o upload do documento.";
  } finally {
    isUploading.value = false;
  }
}
async function deleteDocument(document: DocumentItem): Promise<void> {
  if (
    !auth.accessToken ||
    !(await confirmAction(
      "Excluir documento?",
      `"${document.file_name}" será removido. Esta ação não pode ser desfeita.`,
      "Excluir documento",
    ))
  )
    return;
  isDeleting.value = document.id;
  try {
    await documentsApi.remove(auth.accessToken, document.id);
    documents.value = documents.value.filter((item) => item.id !== document.id);
    if (selectedDocument.value?.id === document.id) closeDocument();
    showSuccess("Documento excluído");
  } catch {
    errorMessage.value = "Não foi possível excluir o documento.";
    showError("Exclusão não realizada", errorMessage.value);
  } finally {
    isDeleting.value = null;
  }
}
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    if (isUploadOpen.value) isUploadOpen.value = false;
    else closeDocument();
  }
}
onMounted(loadDocuments);
onMounted(() => window.addEventListener("keydown", handleKeydown));
onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
  closeDocument();
});
</script>

<template>
  <section class="documents-page">
    <header class="documents-topbar">
      <label class="top-search"
        ><span class="material-symbols-outlined">search</span
        ><input
          v-model="search"
          aria-label="Buscar documentos"
          placeholder="Buscar documentos, processos, clientes..."
      /></label>
      <div class="top-actions">
        <button class="icon-button" type="button" aria-label="Notificações">
          <span class="material-symbols-outlined">notifications</span></button
        ><button class="icon-button" type="button" aria-label="Ajuda">
          <span class="material-symbols-outlined">help_outline</span></button
        ><button class="avatar-button" type="button">RS</button>
      </div>
    </header>
    <main class="documents-content">
      <div class="page-heading">
        <div>
          <p class="eyebrow">Arquivos</p>
          <h1>Documentos</h1>
          <p class="description">
            Gerencie, armazene e organize o repositório documental do seu escritório com segurança.
          </p>
        </div>
        <div class="heading-actions">
          <button class="secondary-button" type="button">
            <span class="material-symbols-outlined">filter_list</span>Filtros</button
          ><button
            v-if="canManage"
            class="primary-button"
            type="button"
            @click="isUploadOpen = true"
          >
            <span class="material-symbols-outlined">upload</span>Fazer upload
          </button>
        </div>
      </div>
      <div class="repository">
        <div class="repository-header">
          <div>
            <span class="material-symbols-outlined">folder_open</span>
            <h2>Repositório geral</h2>
          </div>
          <span>{{ filteredDocuments.length }} documento(s)</span>
        </div>
        <div class="controls">
          <select v-model="visibilityFilter" aria-label="Filtrar documentos">
            <option value="ALL">Todas as visibilidades</option>
            <option value="INTERNAL">Internos</option>
            <option value="CLIENT">Visíveis ao cliente</option></select
          ><span>{{ filteredDocuments.length }} resultado(s)</span>
        </div>
        <p v-if="isLoading" class="state-message">Carregando documentos...</p>
        <p v-else-if="errorMessage" class="state-message form-error" role="alert">
          {{ errorMessage }}
        </p>
        <div v-else class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Nome do arquivo</th>
                <th>Categoria</th>
                <th>Processo/Cliente</th>
                <th>Data de upload</th>
                <th>Tamanho</th>
                <th class="actions-heading">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="document in filteredDocuments" :key="document.id">
                <td>
                  <button class="document-name" type="button" @click="openDocument(document)">
                    <span
                      class="file-icon"
                      :class="document.mime_type === 'application/pdf' ? 'pdf' : 'generic'"
                      ><span class="material-symbols-outlined">{{ fileIcon(document) }}</span></span
                    ><span>{{ document.file_name }}</span>
                  </button>
                </td>
                <td>
                  <span class="tag">{{ document.mime_type.split("/").pop()?.toUpperCase() }}</span>
                </td>
                <td class="muted-cell">{{ clientName(document.client_id) }}</td>
                <td class="muted-cell">{{ fileDate(document.uploaded_at) }}</td>
                <td class="muted-cell">{{ fileSize(document.size_bytes) }}</td>
                <td class="row-actions">
                  <button
                    type="button"
                    aria-label="Visualizar documento"
                    title="Visualizar"
                    @click="openDocument(document)"
                  >
                    <span class="material-symbols-outlined">visibility</span></button
                  ><button
                    type="button"
                    aria-label="Baixar documento"
                    title="Baixar"
                    @click="downloadDocument(document)"
                  >
                    <span class="material-symbols-outlined">download</span></button
                  ><button
                    v-if="canManage"
                    type="button"
                    aria-label="Excluir documento"
                    title="Excluir"
                    :disabled="isDeleting === document.id"
                    @click="deleteDocument(document)"
                  >
                    <span class="material-symbols-outlined">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="!filteredDocuments.length && !isLoading && !errorMessage" class="empty-state">
          Nenhum documento encontrado.
        </p>
        <div v-if="filteredDocuments.length" class="table-footer">
          Mostrando {{ filteredDocuments.length }} documento(s)
        </div>
      </div>
    </main>

    <div
      v-if="selectedDocument"
      class="modal-backdrop"
      role="presentation"
      @click.self="closeDocument"
    >
      <section
        class="document-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-details-title"
      >
        <header class="modal-header">
          <div class="modal-title">
            <span class="file-icon pdf"
              ><span class="material-symbols-outlined">{{ fileIcon(selectedDocument) }}</span></span
            >
            <div>
              <h2 id="document-details-title">{{ selectedDocument.file_name }}</h2>
              <p>Visualização de documento</p>
            </div>
          </div>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar modal"
            @click="closeDocument"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div class="modal-main">
          <div class="preview-area">
            <iframe
              v-if="previewUrl && selectedDocument.mime_type === 'application/pdf'"
              :src="previewUrl"
              title="Pré-visualização do PDF"
            ></iframe
            ><img
              v-else-if="previewUrl && selectedDocument.mime_type.startsWith('image/')"
              :src="previewUrl"
              :alt="selectedDocument.file_name"
            />
            <pre v-else-if="previewUrl && selectedDocument.mime_type === 'text/plain'">
Pré-visualização disponível para download.</pre>
            <div v-else class="preview-placeholder">
              <span class="material-symbols-outlined">description</span>
              <p>Preparando pré-visualização...</p>
            </div>
          </div>
          <aside class="metadata">
            <h3>Informações do arquivo</h3>
            <dl>
              <div>
                <dt>Tipo de arquivo</dt>
                <dd>{{ selectedDocument.mime_type }}</dd>
              </div>
              <div>
                <dt>Tamanho</dt>
                <dd>{{ fileSize(selectedDocument.size_bytes) }}</dd>
              </div>
              <div>
                <dt>Data de upload</dt>
                <dd>{{ fileDate(selectedDocument.uploaded_at) }}</dd>
              </div>
              <div>
                <dt>Cliente vinculado</dt>
                <dd>{{ clientName(selectedDocument.client_id) }}</dd>
              </div>
              <div>
                <dt>Processo vinculado</dt>
                <dd>{{ selectedDocument.case_id || "Não informado" }}</dd>
              </div>
              <div>
                <dt>Visibilidade</dt>
                <dd>{{ selectedDocument.visibility === "CLIENT" ? "Cliente" : "Interno" }}</dd>
              </div>
            </dl>
          </aside>
        </div>
        <footer class="modal-footer">
          <button
            v-if="canManage"
            class="danger-button"
            type="button"
            @click="deleteDocument(selectedDocument)"
          >
            <span class="material-symbols-outlined">delete</span>Excluir
          </button>
          <div>
            <button class="secondary-button" type="button" @click="closeDocument">Fechar</button
            ><button
              class="primary-button mx-2"
              type="button"
              @click="downloadDocument(selectedDocument)"
            >
              <span class="material-symbols-outlined">download</span>Baixar arquivo
            </button>
          </div>
        </footer>
      </section>
    </div>

    <div
      v-if="isUploadOpen && canManage"
      class="modal-backdrop"
      role="presentation"
      @click.self="isUploadOpen = false"
    >
      <section class="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
        <header class="modal-header">
          <h2 id="upload-title">Fazer upload</h2>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar upload"
            @click="isUploadOpen = false"
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <form class="upload-form" @submit.prevent="uploadDocument">
          <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
          <label
            >Arquivo<input
              type="file"
              accept="application/pdf,image/jpeg,image/png,text/plain"
              required
              @change="chooseFile" /></label
          ><label
            >Cliente<select v-model="uploadClientId" required>
              <option value="" disabled>Selecione um cliente</option>
              <option v-for="client in clients" :key="client.id" :value="client.id">
                {{ client.name }}
              </option>
            </select></label
          ><label
            >Visibilidade<select v-model="uploadVisibility">
              <option value="INTERNAL">Interno</option>
              <option value="CLIENT">Visível ao cliente</option>
            </select></label
          >
          <footer class="modal-footer">
            <button class="secondary-button" type="button" @click="isUploadOpen = false">
              Cancelar</button
            ><button class="primary-button" type="submit" :disabled="isUploading">
              {{ isUploading ? "Enviando..." : "Enviar arquivo" }}
            </button>
          </footer>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.documents-page {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope, sans-serif;
}
.documents-topbar {
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
  width: 320px;
  border: 0;
  outline: 0;
  padding: 9px 0;
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
.documents-content {
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
dt,
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
  max-width: 680px;
  margin: 10px 0 0;
  color: #44474b;
}
.heading-actions {
  display: flex;
  gap: 10px;
}
.primary-button,
.secondary-button,
.danger-button {
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
  color: #fff;
  border-color: #7b5647;
}
.secondary-button {
  background: #fff;
  color: #121c26;
}
.danger-button {
  background: transparent;
  border: 0;
  color: #ba1a1a;
}
.repository {
  overflow: hidden;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
}
.repository-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: #fcf9f2;
  border-bottom: 1px solid #c4c6cb;
  color: #44474b;
}
.repository-header > div {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #7b5647;
}
.repository-header h2 {
  font:
    600 12px "Work Sans",
    sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  border-bottom: 1px solid #e5e2db;
  color: #44474b;
  font-size: 14px;
}
.controls select {
  padding: 8px 12px;
  border: 1px solid #c4c6cb;
  border-radius: 4px;
  background: #fff;
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  min-width: 850px;
  border-collapse: collapse;
  text-align: left;
}
th {
  padding: 16px 24px;
  color: #44474b;
  background: #f6f3ec;
  border-bottom: 1px solid #c4c6cb;
}
td {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(196, 198, 203, 0.4);
  font-size: 14px;
}
.document-name {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 0;
  padding: 0;
  background: transparent;
  color: #121c26;
  cursor: pointer;
  font:
    500 14px Manrope,
    sans-serif;
  text-align: left;
}
.document-name:hover {
  color: #7b5647;
}
.file-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 4px;
  background: #e5e2db;
  color: #44474b;
  flex-shrink: 0;
}
.file-icon.pdf {
  background: #ffdad6;
  color: #ba1a1a;
}
.tag {
  padding: 4px 9px;
  border: 1px solid #c4c6cb;
  border-radius: 999px;
  color: #44474b;
  font:
    600 11px "Work Sans",
    sans-serif;
}
.muted-cell {
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
  padding: 18px 24px;
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
  backdrop-filter: blur(5px);
}
.document-modal {
  width: min(1024px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
  box-shadow: 0 24px 60px rgba(18, 28, 38, 0.22);
}
.modal-header,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
  background: #fcf9f2;
  border-bottom: 1px solid #d7c3b0;
}
.modal-footer {
  border-top: 1px solid #d7c3b0;
  border-bottom: 0;
}
.modal-title {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.modal-title h2 {
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 22px;
  white-space: nowrap;
}
.modal-title p {
  margin: 4px 0 0;
  color: #44474b;
  font-size: 13px;
}
.modal-main {
  display: flex;
  flex: 1;
  min-height: 500px;
  overflow: hidden;
  background: #f6f3ec;
}
.preview-area {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 24px;
  border-right: 1px solid #d7c3b0;
}
.preview-area iframe {
  width: 100%;
  height: 600px;
  border: 1px solid #d7c3b0;
  background: #fff;
}
.preview-area img {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  background: #fff;
}
.preview-area pre {
  width: 100%;
  min-height: 300px;
  padding: 32px;
  background: #fff;
  white-space: pre-wrap;
}
.preview-placeholder {
  text-align: center;
  color: #7b5647;
}
.preview-placeholder .material-symbols-outlined {
  font-size: 96px;
  opacity: 0.35;
}
.metadata {
  width: 320px;
  overflow-y: auto;
  padding: 24px;
  background: #fff;
}
.metadata h3 {
  padding-bottom: 10px;
  border-bottom: 1px solid #e5e2db;
  font:
    600 12px "Work Sans",
    sans-serif;
  color: #44474b;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.metadata dl {
  display: grid;
  gap: 20px;
}
.metadata dt {
  margin-bottom: 5px;
  color: #44474b;
  font-size: 10px;
}
.metadata dd {
  margin: 0;
  color: #1c1c18;
  line-height: 1.4;
  word-break: break-word;
}
.upload-modal {
  width: min(620px, 100%);
  overflow: hidden;
  background: #fcf9f2;
  border: 1px solid #d7c3b0;
  border-radius: 8px;
}
.upload-form {
  display: grid;
  gap: 16px;
  padding: 24px;
}
.upload-form label {
  display: grid;
  gap: 7px;
  color: #44474b;
  font:
    600 12px "Work Sans",
    sans-serif;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.upload-form input,
.upload-form select {
  padding: 11px;
  border: 1px solid #c4c6cb;
  border-radius: 4px;
  background: #fff;
  font:
    14px Manrope,
    sans-serif;
}
.upload-form .modal-footer {
  margin: 8px -24px -24px;
}
@media (max-width: 800px) {
  .documents-content {
    padding: 28px 20px;
  }
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .heading-actions {
    width: 100%;
  }
  .modal-main {
    flex-direction: column;
  }
  .metadata {
    width: auto;
  }
  .preview-area {
    min-height: 300px;
    border-right: 0;
    border-bottom: 1px solid #d7c3b0;
  }
}
@media (max-width: 560px) {
  .documents-topbar {
    padding: 0 16px;
  }
  .top-search input {
    width: 190px;
  }
  .documents-content {
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
  .modal-header,
  .modal-footer,
  .upload-form {
    padding: 16px;
  }
  .modal-title h2 {
    font-size: 17px;
  }
  .upload-form .modal-footer {
    margin: 8px -16px -16px;
  }
}
</style>

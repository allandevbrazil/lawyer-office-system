<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { adminApi, type WikiItem } from "@/services/api";
import { confirmAction, showError, showSuccess } from "@/services/alerts";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
const articles = ref<WikiItem[]>([]);
const search = ref("");
const selected = ref<WikiItem | null>(null);
const editing = ref<WikiItem | null>(null);
const open = ref(false);
const error = ref("");
const formError = ref("");
const form = ref({ title: "", slug: "", category: "", content_markdown: "", status: "DRAFT" });
const filtered = computed(() =>
  articles.value.filter(
    (a) =>
      !search.value ||
      `${a.title} ${a.category ?? ""} ${a.content_markdown}`
        .toLowerCase()
        .includes(search.value.toLowerCase()),
  ),
);
function create(): void {
  editing.value = null;
  form.value = { title: "", slug: "", category: "", content_markdown: "", status: "DRAFT" };
  formError.value = "";
  open.value = true;
}
function edit(a: WikiItem): void {
  selected.value = null;
  editing.value = a;
  form.value = {
    title: a.title,
    slug: a.slug ?? "",
    category: a.category ?? "",
    content_markdown: a.content_markdown,
    status: a.status,
  };
  open.value = true;
}
async function load(): Promise<void> {
  if (!auth.accessToken) return;
  try {
    articles.value = await adminApi.wiki(auth.accessToken);
  } catch {
    error.value = "Não foi possível carregar a Wiki.";
  }
}
async function save(): Promise<void> {
  if (form.value.title.length < 3 || !form.value.content_markdown)
    return void (formError.value = "Preencha título e conteúdo.");
  if (!/^[a-z0-9-]+$/.test(form.value.slug)) return void (formError.value = "Slug inválido.");
  if (!auth.accessToken) return;
  try {
    const item = editing.value
      ? await adminApi.updateWiki(auth.accessToken, editing.value.id, form.value)
      : await adminApi.createWiki(auth.accessToken, form.value);
    articles.value = editing.value
      ? articles.value.map((a) => (a.id === item.id ? item : a))
      : [item, ...articles.value];
    open.value = false;
  } catch {
    formError.value = "Não foi possível salvar o artigo.";
  }
}
async function remove(a: WikiItem): Promise<void> {
  if (
    !auth.accessToken ||
    !(await confirmAction(
      "Excluir artigo?",
      `${a.title} será removido. Esta ação não pode ser desfeita.`,
      "Excluir artigo",
    ))
  )
    return;
  try {
    await adminApi.removeWiki(auth.accessToken, a.id);
    articles.value = articles.value.filter((x) => x.id !== a.id);
    selected.value = null;
    showSuccess("Artigo excluído");
  } catch {
    error.value = "Não foi possível excluir o artigo.";
    showError("Exclusão não realizada", error.value);
  }
}
onMounted(load);
</script>
<template>
  <section class="wiki">
    <header>
      <input
        v-model="search"
        placeholder="Buscar na base de conhecimento..."
        aria-label="Buscar artigos"
      /><span>RS</span>
    </header>
    <main>
      <div class="hero">
        <p>Conhecimento</p>
        <h1>Base de conhecimento</h1>
        <small>Procedimentos, modelos e referências do escritório.</small>
        <div class="search">
          <input v-model="search" placeholder="Buscar artigos..." /><button>Buscar</button>
        </div>
      </div>
      <div class="toolbar">
        <h2>Artigos Wiki</h2>
        <button class="primary" @click="create">＋ Novo artigo</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="cards">
        <article v-for="a in filtered" :key="a.id" @click="selected = a">
          <span>{{ a.category || "Geral" }}</span>
          <h3>{{ a.title }}</h3>
          <p>{{ a.content_markdown.slice(0, 180) }}...</p>
          <small>{{ a.status }}</small>
          <footer>
            <button @click.stop="edit(a)">Editar</button
            ><button @click.stop="remove(a)">Excluir</button>
          </footer>
        </article>
      </div>
    </main>
    <div v-if="selected" class="backdrop">
      <article class="article-modal">
        <header>
          <div>
            <p>{{ selected.category || "Geral" }}</p>
            <h2>{{ selected.title }}</h2>
          </div>
          <button @click="selected = null">×</button>
        </header>
        <div class="content">{{ selected.content_markdown }}</div>
        <footer>
          <button class="secondary" @click="selected = null">Fechar</button
          ><button class="primary" @click="edit(selected)">Editar artigo</button>
        </footer>
      </article>
    </div>
    <div v-if="open" class="backdrop">
      <form class="article-modal form" @submit.prevent="save">
        <header>
          <h2>{{ editing ? "Editar artigo" : "Novo artigo" }}</h2>
          <button type="button" @click="open = false">×</button>
        </header>
        <p v-if="formError" class="error">{{ formError }}</p>
        <label>Título<input v-model="form.title" maxlength="240" required /></label
        ><label>Slug<input v-model="form.slug" required /></label
        ><label>Categoria<input v-model="form.category" /></label
        ><label
          >Status<select v-model="form.status">
            <option value="DRAFT">Rascunho</option>
            <option value="PUBLISHED">Publicado</option>
            <option value="ARCHIVED">Arquivado</option>
          </select></label
        ><label
          >Conteúdo Markdown<textarea v-model="form.content_markdown" rows="12" required></textarea>
        </label>
        <footer>
          <button type="button" class="secondary" @click="open = false">Cancelar</button
          ><button class="primary">Salvar</button>
        </footer>
      </form>
    </div>
  </section>
</template>
<style scoped>
.wiki {
  min-height: 100vh;
  background: #fcf9f2;
  color: #1c1c18;
  font-family: Manrope;
}
.wiki > header {
  height: 64px;
  border-bottom: 1px solid #c4c6cb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px 0 48px;
}
.wiki > header input {
  border: 0;
  background: transparent;
  padding: 10px;
  width: 300px;
}
.wiki > header span {
  background: #121c26;
  color: #fff;
  border-radius: 50%;
  padding: 9px;
  font-size: 11px;
}
.hero {
  text-align: center;
  padding: 48px 24px 34px;
}
.hero > p {
  color: #7b5647;
  text-transform: uppercase;
  font-size: 12px;
}
.hero h1 {
  font: 48px "Libre Caslon Text";
  margin: 8px;
}
.hero small {
  color: #44474b;
}
.search {
  display: flex;
  max-width: 620px;
  margin: 26px auto 0;
  padding: 8px;
  background: #fff;
  border: 1px solid #d7c3b0;
}
.search input {
  flex: 1;
  border: 0;
  padding: 10px;
}
.search button,
.primary {
  background: #7b5647;
  color: #fff;
  border: 0;
  border-radius: 4px;
  padding: 10px 16px;
  cursor: pointer;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  max-width: 1100px;
  margin: auto;
  padding: 0 24px 18px;
}
.cards {
  max-width: 1100px;
  margin: auto;
  padding: 0 24px 40px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}
.cards article {
  background: #fff;
  border: 1px solid #d7c3b0;
  border-radius: 7px;
  padding: 22px;
  cursor: pointer;
}
.cards article > span {
  color: #7b5647;
  font-size: 12px;
  text-transform: uppercase;
}
.cards h3 {
  font: 20px "Libre Caslon Text";
}
.cards p {
  color: #44474b;
  line-height: 1.5;
}
.cards footer {
  display: flex;
  gap: 10px;
}
.cards footer button {
  border: 0;
  background: transparent;
  color: #7b5647;
  cursor: pointer;
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
.article-modal {
  width: min(820px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: #fcf9f2;
  border: 1px solid #d7c3b0;
}
.article-modal header,
.article-modal footer {
  padding: 18px 24px;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #d7c3b0;
}
.article-modal header button {
  border: 0;
  background: transparent;
  font-size: 24px;
}
.article-modal footer {
  justify-content: flex-end;
  border-top: 1px solid #d7c3b0;
}
.content {
  padding: 30px;
  white-space: pre-wrap;
  line-height: 1.7;
}
.form {
  padding: 24px;
  display: grid;
  gap: 14px;
}
.form header,
.form footer {
  margin: 0 -24px;
}
.form label {
  display: grid;
  gap: 6px;
}
.form input,
.form textarea,
.form select {
  padding: 10px;
  border: 1px solid #c4c6cb;
}
.secondary {
  padding: 10px 16px;
  border: 1px solid #d7c3b0;
  background: #fff;
  border-radius: 4px;
}
.error {
  color: #ba1a1a;
}
</style>

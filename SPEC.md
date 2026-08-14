# Especificacao: ERP de Backoffice para Escritórios de Advocacia (MVP)

**Status:** Rascunho para aprovacao da etapa `/spec`  
**Versao:** 0.1  
**Data:** 2026-08-12

## 1. Objetivo

Construir um ERP web de backoffice para centralizar operacao, processos, clientes, documentos, faturamento e conhecimento de um escritorio de advocacia.

O MVP sera um monorepo com dois aplicativos independentes:

- `backend`: API REST em Python 3.12+ com FastAPI e PostgreSQL.
- `frontend`: SPA em Vue 3 + TypeScript estrito.

### Perfis de usuario

- **Master:** administrador do escritorio, com acesso total e configuracoes globais.
- **Funcionario:** advogado, paralegal ou operacional, com acesso operacional a todos os registros da propria firma.
- **Cliente:** usuario externo, somente leitura e isolado aos proprios dados/compartilhamentos.

### Criterios de sucesso do MVP

- Um cliente convidado consegue concluir cadastro, autenticar, recuperar senha e encerrar sessao.
- O backend aplica autenticacao JWT e RBAC no servidor; esconder links no frontend nao e controle de seguranca.
- Um Master consegue administrar clientes, funcionarios, processos, documentos, faturas, wiki e configuracoes.
- Funcionarios visualizam e operam todos os registros da propria firma, sem administrar usuarios.
- Clientes nunca conseguem consultar dados de outro cliente nem modulos administrativos.
- A SPA possui layout responsivo, sidebar dinamica, estados de carregamento/erro/vazio e telas utilizaveis para os oito modulos.
- API, testes, build e configuracoes de deploy sao reproduziveis por comandos documentados.

## 2. Premissas e decisoes provisórias

1. O sistema e uma aplicacao web SPA; nao ha aplicativo mobile no MVP.
2. PostgreSQL e o banco principal em desenvolvimento e producao.
3. JWT bearer com access token curto e refresh token rotativo. O refresh token sera armazenado em cookie `HttpOnly`, `Secure` em producao e `SameSite=Lax`.
4. O primeiro Master sera criado por seed usando variaveis de ambiente obrigatorias (`INITIAL_MASTER_EMAIL` e `INITIAL_MASTER_PASSWORD`), nunca por cadastro publico.
5. O cadastro publico nao cria contas. Clientes de terceiros entram somente por convite enviado por um Master ou Funcionario autorizado; o convite cria um token temporario para concluir o cadastro.
6. E-mail de recuperacao e convites usarao um adapter de email. A implementacao inicial recomendada e Resend Free; desenvolvimento podera usar adapter de console.
7. Upload de documentos usara um adapter de storage. A implementacao inicial recomendada e Supabase Storage Free; desenvolvimento podera usar filesystem local. O banco guarda metadados, nao o binario.
8. Valores monetarios serao armazenados em `NUMERIC(12,2)` e transportados como string decimal nos contratos JSON para evitar perda de precisao.
9. Datas serao ISO-8601 em UTC. O frontend converte para o fuso configurado do escritorio.
10. Exclusao de dados sera logica quando houver historico, usando `deleted_at`.
11. Multi-tenancy no MVP sera modelado por `firm_id`, mesmo que a primeira instalacao use um escritorio.
12. Funcionarios podem consultar e operar registros de toda a propria firma, mas nao podem adicionar, remover, convidar ou alterar outros usuarios.
13. O MVP nao inclui integracao com tribunais, gateways de pagamento, assinatura digital, emissao fiscal oficial ou envio automatico de peticoes.
14. A fatura do MVP sera operacional, com layout HTML/PDF e numeracao interna; nao representa nota fiscal nem cobranca automatica.
15. O ambiente de demonstracao podera ser resetado semanalmente por comando protegido e documentado, preservando o Master inicial. Nenhum reset automatico sera permitido em producao.

## 3. Stack e infraestrutura

### Backend

- Python 3.12+
- FastAPI, Uvicorn
- SQLAlchemy 2.x async com `asyncpg`
- Alembic
- Pydantic 2 + pydantic-settings
- `pwdlib`/Argon2id preferencialmente; se a compatibilidade exigir, Passlib/Bcrypt
- JWT assinado com segredo configurado por ambiente
- Pytest, httpx e pytest-asyncio

### Frontend

- Vue 3, Vite, TypeScript estrito
- Vue Router
- Pinia + Pinia ORM
- Axios
- Tailwind CSS (design system interno com tokens)
- Vitest e Vue Test Utils
- Playwright para smoke/e2e

### Operacao

- PostgreSQL local via `docker-compose.yml`
- Backend com Dockerfile multi-stage
- Frontend com Dockerfile multi-stage para build e servidor estatico
- NeonDB em producao
- Render para API
- Vercel para SPA

## 4. Estrutura planejada do repositorio

```text
/
├── backend/
│   ├── app/
│   │   ├── api/             # routers e dependencias HTTP
│   │   ├── core/            # settings, seguranca, autorizacao, erros
│   │   ├── db/              # engine, sessoes, base, Alembic
│   │   ├── models/          # entidades SQLAlchemy
│   │   ├── schemas/         # DTOs Pydantic de entrada/saida
│   │   ├── services/        # casos de uso e regras de negocio
│   │   └── main.py
│   ├── tests/               # unitarios e integracao
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/      # componentes atomicos e compostos
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── services/        # Axios e gateways de API
│   │   ├── stores/           # Pinia e Pinia ORM
│   │   ├── types/
│   │   ├── views/            # publicas e privadas
│   │   └── App.vue
│   ├── tests/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml
├── vercel.json
└── SPEC.md
```

## 5. Modelo relacional

Todas as tabelas de negocio possuem `id` UUID, `created_at`, `updated_at` e `firm_id` quando aplicavel. Foreign keys usam `ON DELETE RESTRICT` para preservar historico, salvo relacionamentos explicitamente opcionais.

### Entidades principais

- **User:** `id`, `firm_id`, `email` unico por escritorio, `password_hash`, `full_name`, `role` (`MASTER|FUNCIONARIO|CLIENTE`), `status` (`PENDING|ACTIVE|SUSPENDED|INVITED`), `phone`, `last_login_at`, timestamps, `deleted_at`.
- **FirmConfig:** `id`, `firm_id` unico, `legal_name`, `trade_name`, `tax_id`, `email`, `phone`, `address_json`, `logo_url`, `timezone`, `currency`, `settings_json`.
- **Client:** `id`, `firm_id`, `user_id` opcional/unico, `type` (`PF|PJ`), `name`, `document_number` criptografado/mascarado, `email`, `phone`, `address_json`, `notes`, `status`.
- **Case:** `id`, `firm_id`, `client_id`, `case_number` (CNJ quando houver), `title`, `description`, `court`, `jurisdiction`, `case_type`, `status` (`ACTIVE|SUSPENDED|ARCHIVED`), `priority`, `responsible_user_id`, `opened_at`, `closed_at`.
- **CaseParty:** `id`, `case_id`, `name`, `role`, `document_number` opcional, `contact_json`.
- **CaseEvent:** `id`, `case_id`, `author_user_id`, `event_type`, `title`, `description`, `occurred_at`, `visibility` (`INTERNAL|CLIENT`), `metadata_json`.
- **Service:** `id`, `firm_id`, `client_id`, `case_id` opcional, `description`, `service_type`, `unit_price`, `quantity`, `status` (`OPEN|BILLED|CANCELLED`).
- **Invoice:** `id`, `firm_id`, `client_id`, `case_id` opcional, `number`, `description`, `subtotal`, `discount`, `total`, `due_date`, `paid_at`, `status` (`PENDING|PAID|OVERDUE|CANCELLED`), `issued_at`.
- **InvoiceItem:** `id`, `invoice_id`, `service_id` opcional, `description`, `quantity`, `unit_price`, `amount`.
- **Document:** `id`, `firm_id`, `client_id` opcional, `case_id` opcional, `uploaded_by`, `file_name`, `storage_key`, `mime_type`, `size_bytes`, `visibility` (`INTERNAL|CLIENT`), `folder`, `checksum`, `uploaded_at`.
- **WikiArticle:** `id`, `firm_id`, `author_user_id`, `title`, `slug`, `content_markdown`, `category`, `status` (`DRAFT|PUBLISHED|ARCHIVED`), `published_at`.
- **Activity:** `id`, `firm_id`, `actor_user_id`, `entity_type`, `entity_id`, `action`, `description`, `metadata_json`, `created_at`.
- **PasswordResetToken:** `id`, `user_id`, `token_hash`, `expires_at`, `used_at`, `created_at`.
- **RefreshToken:** `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at`.

### Relacionamentos e regras

- `FirmConfig` 1:1 `firm_id`; uma firma possui muitos `User`, `Client`, `Case`, `Service`, `Invoice`, `Document`, `WikiArticle` e `Activity`.
- `Client` 1:N `Case`, `Invoice`, `Service`; `Client.user_id` vincula o login externo sem obrigar todos os clientes a ter acesso.
- `Case` N:1 `Client`, N:1 `User` responsavel, 1:N `CaseParty`, `CaseEvent`, `Document` e `Service`.
- `Invoice` 1:N `InvoiceItem`; fatura pode referenciar um processo.
- Documento deve ter ao menos um contexto (`client_id` ou `case_id`) e nunca pode apontar para outra `firm_id`.
- Indices: `(firm_id, status)`, `(firm_id, client_id)`, `(firm_id, responsible_user_id)`, `case_number`, `due_date`, `slug` por firma.

## 6. Autorizacao e isolamento

A autorizacao sera aplicada em dependencias FastAPI e nos services, com escopo calculado a partir do usuario autenticado.

- **Master:** qualquer registro da propria `firm_id`; pode gerenciar usuarios, configuracoes e publicar wiki.
- **Funcionario:** pode consultar e operar registros da propria `firm_id`, sem restricao por responsavel ou atribuicao. Pode criar/editar clientes, processos, servicos, faturas, documentos e artigos conforme as permissoes do modulo. Nao pode adicionar, remover, convidar, suspender ou alterar dados de outros usuarios e nao acessa configuracoes globais.
- **Cliente:** somente leitura. `Client.user_id == current_user.id`; processos, faturas e documentos vinculados ao proprio cliente. Documentos exigem `visibility=CLIENT`; eventos exigem `visibility=CLIENT`. Nao acessa funcionarios, wiki interna, configuracoes ou dados financeiros de terceiros.

Qualquer tentativa de acesso fora do escopo retorna `404` para recursos por identificador, evitando vazamento de existencia; `403` fica reservado a recurso permitido no escopo, mas proibido para a role.

## 7. Contrato HTTP da API

Prefixo: `/api/v1`. JSON usa `snake_case`. Listagens usam `page`, `page_size`, `sort`, `search` e filtros de dominio.

### Formato comum

```json
{
  "data": {},
  "meta": {"page": 1, "page_size": 20, "total": 0}
}
```

Erros:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados invalidos",
    "details": [{"field": "email", "message": "Email invalido"}],
    "request_id": "uuid"
  }
}
```

### Auth e sessao

- `POST /auth/register`: conclui cadastro de cliente convidado; body `invite_token`, `email`, `password`, `full_name`, `phone`. Retorna `201` com usuario `ACTIVE` ou `PENDING`, conforme a politica de ativacao.
- `POST /auth/token`: OAuth2 form `username` (email) e `password`; retorna `access_token`, `token_type`, `expires_in`, `user`.
- `POST /auth/refresh`: rotaciona refresh cookie e retorna novo access token.
- `POST /auth/logout`: revoga refresh token; retorna `204`.
- `GET /auth/me`: retorna perfil e permissoes efetivas.
- `POST /auth/forgot-password`: sempre retorna `202`, sem revelar se o email existe.
- `POST /auth/reset-password`: body `token`, `new_password`; retorna `204`.

### Dashboard e atividades

- `GET /dashboard/summary`: metricas filtradas pela role e pela `firm_id`: `billing_total`, `active_cases`, `pending_invoices`, `recent_activities`.
- `GET /dashboard/cash-flow?from=&to=`: serie agregada de recebimentos e vencimentos.
- `GET /activities`: feed paginado de atividades permitidas.

### Processos

- `GET /cases`: lista com `status`, `client_id`, `responsible_user_id`, `search`.
- `POST /cases`: cria processo (Master/Funcionario autorizado).
- `GET /cases/{case_id}`: detalhe com partes, eventos e documentos visiveis.
- `PATCH /cases/{case_id}`: atualiza dados e status.
- `DELETE /cases/{case_id}`: arquivamento logico (Master/Funcionario autorizado).
- `POST /cases/{case_id}/events`: adiciona movimentacao; cliente nao cria.

### Faturas e servicos

- `GET /services`, `POST /services`, `PATCH /services/{service_id}`: gestao de servicos dentro da propria `firm_id`.
- `GET /invoices`: lista com `status`, `client_id`, `due_from`, `due_to`.
- `POST /invoices`: emite fatura e itens; Master/Funcionario autorizado.
- `GET /invoices/{invoice_id}`: detalhe formatavel para visualizacao.
- `PATCH /invoices/{invoice_id}`: altera status/dados conforme regras.
- `GET /invoices/{invoice_id}/pdf`: gera resposta `application/pdf` ou URL assinada.

### Clientes, convites e funcionarios

- `GET /clients`, `POST /clients`, `GET /clients/{client_id}`, `PATCH /clients/{client_id}`.
- `GET /clients/{client_id}/timeline`: historico de atividades e relacionamentos permitidos.
- `POST /client-invitations`: Master ou Funcionario envia convite para um cliente terceiro.
- `POST /client-invitations/accept`: aceita convite e define credenciais; o token e de uso unico e expira.
- `GET /staff`: Master e Funcionario podem consultar a equipe, sem dados sensiveis.
- `POST /staff/invitations`: somente Master convida funcionario.
- `PATCH /staff/{user_id}`: somente Master altera role/status/dados.
- Nao existe endpoint de criacao, remocao ou alteracao de usuarios para Funcionario.

### Documentos

- `GET /documents`: filtros `client_id`, `case_id`, `visibility`, `folder`, `search`.
- `POST /documents`: multipart upload; valida MIME, tamanho e contexto.
- `GET /documents/{document_id}`: metadados.
- `GET /documents/{document_id}/download`: stream ou URL assinada apos autorizacao.
- `PATCH /documents/{document_id}`: renomeia, move pasta ou altera visibilidade conforme role.
- `DELETE /documents/{document_id}`: remove logicamente (Master/autor autorizado).

### Wiki

- `GET /wiki/articles`: lista artigos publicados para funcionarios; Master ve rascunhos.
- `POST /wiki/articles`, `GET /wiki/articles/{article_id}`, `PATCH /wiki/articles/{article_id}`, `DELETE /wiki/articles/{article_id}`: Master ou autor funcionario autorizado; cliente sem acesso no MVP.

### Configuracoes

- `GET /settings/firm`: Master; dados publicos minimos podem ser usados na tela de login.
- `PATCH /settings/firm`: Master; atualiza dados fiscais, branding e preferencias.
- `POST /settings/firm/logo`: Master; upload e atualizacao atomica de `logo_url`.
- `GET /settings/permissions`: retorna matriz efetiva para renderizacao do frontend.

### Status e documentacao

- `GET /health`: liveness sem autenticacao.
- `GET /ready`: readiness com verificacao de banco/storage.
- Swagger em `/docs`; ReDoc em `/redoc`; OpenAPI em `/openapi.json`.

Todos os endpoints protegidos devem declarar no OpenAPI autenticacao, role esperada, exemplos de request/response e codigos `401`, `403`, `404`, `422` e `500` quando aplicavel.

## 8. DTOs e contratos essenciais

Cada recurso tera schemas separados: `Create`, `Update`, `Response`, `ListItem` e `ListResponse`. Nunca retornar `password_hash`, tokens, `storage_key` interno ou dados fiscais fora da autorizacao.

Exemplo resumido de `UserResponse`:

```json
{
  "id": "uuid",
  "email": "cliente@example.com",
  "full_name": "Nome do Cliente",
  "role": "CLIENTE",
  "status": "ACTIVE",
  "permissions": ["dashboard:read", "cases:read:own"]
}
```

Validacoes obrigatorias: senha com minimo de 12 caracteres e politica configuravel; email normalizado; UUIDs validos; status enumerado; valores monetarios nao negativos; datas coerentes; upload com limite de tamanho e allowlist de MIME.

## 9. Interface e rotas do frontend

### Rotas publicas

- `/login`: email, senha, lembrar sessao, mensagens de erro sem enumerar usuarios, link para cadastro e recuperacao.
- `/cadastro?invite=`: tela acessivel somente com convite valido; nome, email, telefone, senha, confirmacao e aceite de termos. Sem convite, orienta o terceiro a solicitar um convite ao escritorio.
- `/esqueci-senha`: email e confirmacao neutra de envio.
- `/redefinir-senha?token=`: nova senha e confirmacao; token invalido/expirado com fluxo para solicitar outro.

### Shell privado

`/app` usa `AppLayout` com sidebar responsiva, logo dinamica, seletor/identificacao do escritorio, perfil, logout e breadcrumb. Menu e rotas sao filtrados por permissoes recebidas do backend; guards tambem bloqueiam acesso direto.

- `/app/dashboard`: cards de metricas, grafico de fluxo de caixa, atividades recentes e atalhos conforme role.
- `/app/processos`: DataTable com busca/status/responsavel/cliente; modal ou pagina de criacao; detalhe com resumo, historico, partes e documentos.
- `/app/processos/:id`: detalhe com abas `Resumo`, `Movimentacoes`, `Partes`, `Documentos`; cliente ve apenas conteudo compartilhado.
- `/app/faturas`: DataTable com status, vencimento, cliente e total; acao emitir para equipe; visualizacao e PDF; cliente somente leitura das proprias.
- `/app/faturas/:id`: fatura formatada, itens, totais, status e linha do tempo.
- `/app/clientes`: busca, filtros PF/PJ/status, cadastro/edicao e historico; indisponivel para Cliente.
- `/app/clientes/:id`: dados de contato, processos, faturas e documentos conforme autorizacao.
- `/app/documentos`: upload com contexto, tabela/lista, filtros e download; cliente ve somente compartilhados.
- `/app/funcionarios`: equipe, convites de funcionarios, role/status e responsaveis; Master administra, Funcionario consulta sem alterar usuarios.
- `/app/wiki`: busca por titulo/categoria, leitura e editor Markdown para autorizados; somente equipe.
- `/app/configuracoes`: perfil do escritorio, dados fiscais, timezone/moeda, upload de logo e preferencias; somente Master.

Componentes reutilizaveis previstos: `DataTable`, `FilterBar`, `MetricCard`, `StatusBadge`, `EmptyState`, `LoadingState`, `ErrorState`, `ConfirmDialog`, `FormField`, `FileUploader`, `AppSidebar`, `PageHeader` e `Pagination`.

Acessibilidade minima: HTML semantico, foco visivel, labels associados, navegacao por teclado, contraste WCAG AA, feedback de erro em campo e estados de loading que nao mudam dimensoes bruscamente.

## 10. Matriz RBAC de UI e API

| Modulo | Master | Funcionario | Cliente |
|---|---|---|---|
| Dashboard | leitura total | leitura total da firma | leitura propria |
| Processos | CRUD total | CRUD total da firma | leitura propria |
| Faturas | CRUD total | CRUD total da firma | leitura propria |
| Clientes | CRUD total | CRUD total da firma | sem acesso |
| Documentos | CRUD total | CRUD total da firma | leitura compartilhados |
| Funcionarios | CRUD e convites | leitura sem dados sensiveis | sem acesso |
| Wiki | CRUD/publicacao | leitura e contribuicao autorizada | sem acesso |
| Configuracoes | leitura/edicao | sem acesso | sem acesso |

A matriz visual e apenas uma projecao de permissoes. A API revalida `firm_id`, ownership, atribuicao e visibilidade em toda operacao.

## 11. Estrategia de testes

- **Backend unitario:** regras de autorizacao, services, validadores, calculo de totais e tokens.
- **Backend integracao:** login/refresh/logout, cadastro pendente, reset de senha, CRUDs principais, filtros e isolamento entre clientes; banco PostgreSQL de teste.
- **Frontend unitario:** stores, guards, services Axios, componentes de tabela/formulario e estados de permissao.
- **Frontend build/typecheck:** Vite build e `vue-tsc --noEmit`.
- **E2E/smoke:** login, redirecionamento por role, sidebar, listagem/detalhe e bloqueio de rota restrita em Chromium desktop/mobile.
- **Contrato:** OpenAPI gerado e schemas verificados contra exemplos.
- **Seguranca:** testes de acesso cross-tenant/cross-client, tokens expirados/revogados, upload proibido e ausencia de segredos no bundle.

Meta inicial: cobertura de 80% nos services/regras criticas; 100% dos fluxos de autenticacao e isolamento de dados.

## 12. Comandos previstos

```bash
# Infra local
 docker compose up -d db

# Backend
 cd backend
 python -m venv .venv
 pip install -e ".[dev]"
 alembic upgrade head
 uvicorn app.main:app --reload
 pytest -q

# Frontend
 cd frontend
 npm ci
 npm run dev
 npm run typecheck
 npm run test:unit
 npm run build
 npm run test:e2e
```

Os scripts finais e versoes exatas serao definidos no `/build` conforme dependencias instaladas.

## 13. Limites de engenharia

- **Sempre:** validar entrada no boundary, aplicar autorizacao no backend, usar queries parametrizadas/ORM, registrar auditoria de mutacoes, testar isolamento, manter migrations versionadas, rodar typecheck/testes/build antes de considerar uma etapa concluida.
- **Perguntar antes:** alterar modelo relacional depois da aprovacao, adicionar integracao externa paga, mudar politica de roles, alterar CI/CD, incluir dados sensiveis em logs ou mudar o provedor de storage.
- **Nunca:** commitar secrets, expor hashes/tokens, confiar apenas na sidebar para seguranca, retornar dados de outro tenant/cliente, fazer upload sem validacao, remover testes para mascarar falhas ou executar `git reset --hard`.

## 14. Deploy e observabilidade (escopo de preparacao)

- **NeonDB:** `DATABASE_URL` com SSL e pool adequado; migrations executadas no release do backend. O banco permanece sem custo dentro da cota gratuita do projeto de portfolio.
- **Supabase Storage Free:** bucket privado para documentos, URLs assinadas e limite configuravel; usar `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` apenas no backend. A chave nunca vai para o frontend nem para o repositorio.
- **Resend Free:** envio de convites e recuperacao de senha por adapter; usar `RESEND_API_KEY` somente no backend e dominio/remetente verificado quando necessario. O adapter de console permanece disponivel para desenvolvimento sem chaves.
- **Render:** Web Service com build/install de dependencias, comando de migration no deploy e start com Uvicorn/Gunicorn; secrets somente no painel do Render.
- **Vercel:** build da pasta `frontend`, `VITE_LAWFIRM_API_URL` apontando para a API Render e rewrite SPA para `index.html`.
- CORS restrito ao dominio Vercel configurado; health checks em `/health` e `/ready`.
- Logs estruturados sem PII desnecessaria, `request_id`, metricas de latencia/erro e alertas de readiness.

### Reset do ambiente de demonstracao

- O reset sera uma operacao explicita, idempotente e protegida por `APP_ENV=demo`.
- O comando apaga dados de negocio, documentos do bucket demo e tokens expirados, recria dados seed e preserva o Master definido por `INITIAL_MASTER_EMAIL`/`INITIAL_MASTER_PASSWORD`.
- O reset semanal podera ser executado manualmente ou por GitHub Actions agendada, desde que a credencial usada seja exclusiva do ambiente demo.
- O backend deve recusar o comando se `APP_ENV=production`; nao havera job destrutivo apontando para NeonDB de producao.
- Limites gratuitos e quotas dos provedores devem ser monitorados; reset nao substitui politica de backup.

## 15. Questoes abertas para aprovacao

1. Qual sera o nome, identidade visual, dominio e timezone padrao do escritorio?
2. Quais campos e categorias de processos sao obrigatorios para o escritorio?
3. O cliente precisa visualizar eventos/movimentacoes em tempo real ou atualizacao sob demanda e suficiente?
4. Ha requisitos LGPD especificos para retencao, exportacao e exclusao de dados?

### Decisoes confirmadas nesta revisao

- Master inicial: seed por variavel de ambiente.
- Cliente: cadastro somente por convite de terceiro.
- Funcionario: acesso a todos os registros da firma, sem gestao de usuarios.
- Storage inicial: Supabase Storage Free, com adapter substituivel.
- Email inicial: Resend Free, com adapter de console local.
- Faturas: operacionais, sem emissao fiscal.
- Reset: semanal somente no ambiente demo, preservando o Master.

## 16. Gate da etapa `/spec`

A etapa sera considerada aprovada quando o responsavel confirmar:

- modelo e relacionamentos das entidades;
- escopo das telas e rotas;
- matriz de permissoes e regra de isolamento;
- contratos de autenticacao e recursos;
- premissas e respostas das questoes abertas prioritarias;
- criterios de sucesso e estrategia de testes.

Somente apos essa aprovacao sera criado `tasks/plan.md` e `tasks/todo.md` na etapa `/plan`.

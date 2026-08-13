# Plano de Implementacao: ERP Backoffice LawFirm MVP

**Base:** [SPEC.md](../SPEC.md)  
**Status:** Proposta para aprovacao da etapa `/plan`  
**Versao:** 0.1  
**Data:** 2026-08-12

## Visao geral

Construir o ERP como monorepo com `backend/` e `frontend/`, entregando primeiro uma fundacao executavel, depois fatias completas de autenticacao, operacao juridica/financeira, interface e preparacao para deploy. O backend sera a autoridade de seguranca e dados; o frontend consumira contratos tipados e refletira permissoes sem substituir a autorizacao da API.

## Decisoes de arquitetura

- **Clean Architecture pragmatica:** routers/adapters HTTP, schemas de contrato, services de caso de uso, repositorios/SQLAlchemy e modelos separados por responsabilidade.
- **Multi-tenancy desde o primeiro schema:** todas as consultas de negocio filtram `firm_id` derivado do usuario autenticado.
- **RBAC no servidor:** dependencias de autenticacao + policy/service layer; UI apenas oculta comandos indisponiveis.
- **JWT com refresh rotativo:** access token curto, refresh em cookie HttpOnly e tokens persistidos por hash para revogacao.
- **Adapters substituiveis:** email com Resend/console e storage com Supabase/filesystem, sem acoplar regras de negocio ao provedor.
- **API-first:** contratos Pydantic e OpenAPI serao estabilizados antes da implementacao equivalente no frontend.
- **Pinia ORM somente para entidades de tela:** estado de sessao e filtros ficam em stores Pinia simples; entidades normalizadas ficam nos models Pinia ORM.
- **Reset seguro:** comando destrutivo separado, permitido apenas com `APP_ENV=demo`, preservando o Master inicial.
- **Comandos raiz:** um `Makefile` ou scripts documentados poderao encapsular comandos, mas os comandos individuais continuam funcionando dentro de cada app.

## Grafo de dependencias

```text
Infra/configuracao
    -> banco, migrations e modelo de identidade
        -> autenticacao, convite e policies
            -> contratos e services de dominio
                -> routers e OpenAPI
                    -> cliente Axios, tipos e stores
                        -> layout, guards e telas
                            -> testes E2E, review e deploy
```

## Plano por blocos

### Bloco 1: Infraestrutura e fundacao executavel

#### Task 1: Criar esqueleto do monorepo

**Aceitacao:** `backend/` e `frontend/` possuem manifests minimos; `.gitignore`, `.env.example` e README de comandos existem; nenhum segredo e versionado.  
**Verificacao:** instalar dependencias sem erro; executar os comandos de health/build placeholder definidos nos manifests.  
**Dependencias:** nenhuma.  
**Arquivos provaveis:** `backend/pyproject.toml`, `frontend/package.json`, `.gitignore`, `.env.example`, `README.md`.  
**Escopo:** M (5 arquivos).

#### Task 2: Configurar PostgreSQL e containers

**Aceitacao:** `docker compose up -d db` sobe PostgreSQL com healthcheck, volume nomeado e credenciais por ambiente; Dockerfiles de backend/frontend usam stages separados.  
**Verificacao:** `docker compose config` e healthcheck do banco passam.  
**Dependencias:** Task 1.  
**Arquivos provaveis:** `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.dockerignore`.  
**Escopo:** S (4 arquivos).

#### Task 3: Inicializar app FastAPI, Vue e ferramentas

**Aceitacao:** backend responde `/health` e `/ready`; frontend inicia com Vite; lint/typecheck/test runner possuem scripts; CORS vem de configuracao.  
**Verificacao:** `uvicorn app.main:app`, `npm run dev`, `pytest`, `npm run typecheck` e `npm run build` executam.  
**Dependencias:** Tasks 1-2.  
**Arquivos provaveis:** `backend/app/main.py`, `backend/app/core/config.py`, `frontend/src/main.ts`, `frontend/vite.config.ts`, `frontend/package.json`.  
**Escopo:** M (5 arquivos).

### Checkpoint 1: Fundacao

- [ ] Compose valida e banco esta acessivel.
- [ ] Backend inicia e expoe health/readiness.
- [ ] Frontend inicia, tipa e gera build.
- [ ] Nenhuma credencial real aparece no repositorio.

### Bloco 2: Backend identidade, autenticacao e autorizacao

#### Task 4: Criar base SQLAlchemy, Alembic e entidades de identidade

**Aceitacao:** engine async, sessao, base declarativa e migration inicial existem para `User`, `FirmConfig`, `Client`, `RefreshToken` e `PasswordResetToken`; indices e constraints principais estao definidos.  
**Verificacao:** `alembic upgrade head`, downgrade/upgrade em banco limpo e teste de constraints.  
**Dependencias:** Tasks 1-3.  
**Arquivos provaveis:** `backend/app/db/*`, `backend/app/models/user.py`, `backend/app/models/firm.py`, `backend/app/models/client.py`, `backend/alembic/versions/*`.  
**Escopo:** M (5 areas de arquivos).

#### Task 5: Implementar seguranca, seed Master e sessao JWT

**Aceitacao:** senha e armazenada com hash forte; access token valida issuer/audience/expiry; refresh token e rotacionado e revogavel; seed exige `INITIAL_MASTER_EMAIL` e `INITIAL_MASTER_PASSWORD`; logout invalida refresh.  
**Verificacao:** testes unitarios de hash/token/rotacao e teste de seed idempotente.  
**Dependencias:** Task 4.  
**Arquivos provaveis:** `backend/app/core/security.py`, `backend/app/core/dependencies.py`, `backend/app/services/auth_service.py`, `backend/app/db/seed.py`, `backend/app/schemas/auth.py`.  
**Escopo:** M (5 arquivos).

#### Task 6: Entregar login, refresh, logout e perfil

**Aceitacao:** endpoints `/auth/token`, `/auth/refresh`, `/auth/logout` e `/auth/me` seguem o contrato, documentam responses e nao retornam hashes/tokens persistidos.  
**Verificacao:** teste de integracao com cliente valido, senha invalida, token expirado, refresh reutilizado e logout.  
**Dependencias:** Task 5.  
**Arquivos provaveis:** `backend/app/api/auth.py`, `backend/app/schemas/user.py`, `backend/app/services/auth_service.py`, `backend/tests/integration/test_auth.py`.  
**Escopo:** S (4 arquivos).

#### Task 7: Implementar convites de clientes e recuperacao de senha

**Aceitacao:** Master/Funcionario envia convite; terceiro conclui cadastro somente com token unico e expiravel; forgot-password responde neutro; reset invalida tokens anteriores; email usa adapter Resend/console.  
**Verificacao:** integracao cobrindo convite aceito, expirado, reutilizado, email inexistente e reset.  
**Dependencias:** Tasks 5-6.  
**Arquivos provaveis:** `backend/app/models/invitation.py`, `backend/app/services/invitation_service.py`, `backend/app/services/email_service.py`, `backend/app/api/auth.py`, `backend/tests/integration/test_invitation_and_reset.py`.  
**Escopo:** M (5 arquivos).

#### Task 8: Implementar policies RBAC e isolamento por firma

**Aceitacao:** Master acessa a propria firma; Funcionario opera dados da propria firma mas nao usuarios; Cliente acessa somente `Client.user_id` proprio e visibilidade CLIENT; IDs fora do escopo retornam 404.  
**Verificacao:** matriz de testes cross-firm/cross-client para cada policy e teste de ausencia de bypass via query params.  
**Dependencias:** Tasks 4-7.  
**Arquivos provaveis:** `backend/app/core/permissions.py`, `backend/app/services/access_service.py`, `backend/app/api/dependencies.py`, `backend/tests/unit/test_permissions.py`, `backend/tests/integration/test_isolation.py`.  
**Escopo:** M (5 arquivos).

### Checkpoint 2: Identidade segura

- [ ] Auth completa passa integracao.
- [ ] Convites substituem cadastro aberto.
- [ ] RBAC e isolamento sao testados no backend.
- [ ] OpenAPI documenta autenticacao e erros.

### Bloco 3: Domínio de negócio e API

#### Task 9: Implementar clientes, processos, partes e movimentacoes

**Aceitacao:** migrations, models, schemas, services e routers de clientes/processos suportam listagem filtrada, CRUD autorizado, partes e eventos com visibilidade.  
**Verificacao:** testes de CRUD, filtros, status, auditoria e visibilidade para cada role.  
**Dependencias:** Task 8.  
**Arquivos provaveis:** `backend/app/models/case.py`, `backend/app/schemas/case.py`, `backend/app/services/case_service.py`, `backend/app/api/cases.py`, `backend/tests/integration/test_cases.py`.  
**Escopo:** M (5 areas de arquivos).

#### Task 10: Implementar serviços, faturas e dashboard

**Aceitacao:** totais monetarios sao calculados no backend; faturas operacionais possuem itens/status/PDF; dashboard agrega apenas dados autorizados.  
**Verificacao:** testes de arredondamento, transicoes de status, filtros por vencimento, PDF e metricas por role.  
**Dependencias:** Task 9.  
**Arquivos provaveis:** `backend/app/models/billing.py`, `backend/app/schemas/billing.py`, `backend/app/services/billing_service.py`, `backend/app/api/billing.py`, `backend/tests/integration/test_billing.py`.  
**Escopo:** M (5 areas de arquivos).

#### Task 11: Implementar documentos com storage adapter

**Aceitacao:** upload valida MIME/tamanho/contexto, grava metadados, gera download autorizado e usa filesystem local ou Supabase por configuracao; cliente so ve compartilhados.  
**Verificacao:** testes de upload permitido/proibido, contexto cross-firm, URL/download e delecao logica.  
**Dependencias:** Task 9.  
**Arquivos provaveis:** `backend/app/models/document.py`, `backend/app/services/storage_service.py`, `backend/app/services/document_service.py`, `backend/app/api/documents.py`, `backend/tests/integration/test_documents.py`.  
**Escopo:** M (5 arquivos).

#### Task 12: Implementar wiki, funcionarios, configuracoes e atividades

**Aceitacao:** wiki publica/rascunho segue role; equipe pode ser consultada sem dados sensiveis; apenas Master altera usuarios/configuracao/logo; mutacoes geram Activity.  
**Verificacao:** testes de role, auditoria, branding e respostas sem campos privados.  
**Dependencias:** Task 8-11.  
**Arquivos provaveis:** `backend/app/models/content.py`, `backend/app/schemas/admin.py`, `backend/app/services/admin_service.py`, `backend/app/api/admin.py`, `backend/tests/integration/test_admin_modules.py`.  
**Escopo:** M (5 areas de arquivos).

### Checkpoint 3: API de negócio

- [ ] CRUDs principais passam integracao.
- [ ] Queries respeitam `firm_id` e visibilidade.
- [ ] OpenAPI possui exemplos, filtros e codigos de erro.
- [ ] Testes de segurança cobrem Cliente contra dados de terceiros.

### Bloco 4: Frontend base e autenticação

#### Task 13: Configurar design system, Axios, tipos e stores

**Aceitacao:** tokens visuais, Axios com base URL/interceptors, tipos de contrato e stores de auth/permissoes existem; Pinia ORM registra entidades sem duplicar chamadas de API.  
**Verificacao:** `vue-tsc --noEmit`, testes dos interceptors e stores.  
**Dependencias:** Task 6 e contratos dos Tasks 9-12.  
**Arquivos provaveis:** `frontend/src/services/api.ts`, `frontend/src/types/api.ts`, `frontend/src/stores/auth.ts`, `frontend/src/stores/models.ts`, `frontend/src/assets/styles.css`.  
**Escopo:** M (5 arquivos).

#### Task 14: Implementar rotas publicas e fluxo de auth

**Aceitacao:** login, cadastro por convite, forgot/reset, loading/erro e logout funcionam; guards redirecionam por autenticacao e role; sessao e restaurada por refresh.  
**Verificacao:** testes Vue dos formularios/guards e smoke E2E dos quatro fluxos.  
**Dependencias:** Task 13.  
**Arquivos provaveis:** `frontend/src/router/index.ts`, `frontend/src/views/auth/*`, `frontend/src/components/forms/*`, `frontend/src/stores/auth.ts`, `frontend/tests/auth.spec.ts`.  
**Escopo:** M (5 areas de arquivos).

#### Task 15: Criar AppLayout, sidebar e componentes de estado

**Aceitacao:** layout responsivo possui logo dinamica, menu filtrado por permissoes, foco/teclado, breadcrumb, perfil/logout e estados loading/error/empty reutilizaveis.  
**Verificacao:** testes de render por role e smoke visual desktop/mobile.  
**Dependencias:** Tasks 13-14.  
**Arquivos provaveis:** `frontend/src/layouts/AppLayout.vue`, `frontend/src/components/AppSidebar.vue`, `frontend/src/components/ui/*`, `frontend/src/views/app/ForbiddenView.vue`, `frontend/tests/layout.spec.ts`.  
**Escopo:** M (5 areas de arquivos).

### Checkpoint 4: Shell frontend

- [ ] Fluxos de auth funcionam contra API local.
- [ ] Guards nao permitem acesso direto indevido.
- [ ] Sidebar varia por Master, Funcionario e Cliente.
- [ ] Layout nao quebra em viewport mobile.

### Bloco 5: Telas privadas e integração

#### Task 16: Implementar dashboard e telas de processos

**Aceitacao:** dashboard usa metricas reais; processos possuem DataTable/filtros/detalhe/abas/eventos e respeitam comandos por role.  
**Verificacao:** testes de componentes e E2E listagem -> detalhe -> evento, incluindo Cliente somente leitura.  
**Dependencias:** Tasks 9, 13-15.  
**Arquivos provaveis:** `frontend/src/views/app/DashboardView.vue`, `frontend/src/views/app/CasesView.vue`, `frontend/src/views/app/CaseDetailView.vue`, `frontend/src/components/DataTable.vue`, `frontend/tests/cases.spec.ts`.  
**Escopo:** M (5 arquivos).

#### Task 17: Implementar faturas, clientes e documentos

**Aceitacao:** telas listam, filtram e exibem detalhes; equipe cria/edita; Cliente visualiza somente seus dados; upload mostra progresso/erro e download autorizado.  
**Verificacao:** testes de stores/components e E2E dos fluxos de fatura, cliente e documento.  
**Dependencias:** Tasks 10-11, 16.  
**Arquivos provaveis:** `frontend/src/views/app/InvoicesView.vue`, `frontend/src/views/app/ClientsView.vue`, `frontend/src/views/app/DocumentsView.vue`, `frontend/src/components/FileUploader.vue`, `frontend/tests/business-modules.spec.ts`.  
**Escopo:** M (5 arquivos).

#### Task 18: Implementar funcionarios, wiki e configuracoes

**Aceitacao:** Master gerencia equipe/configuracao/logo; Funcionario consulta equipe e usa wiki; Cliente nao recebe links nem acesso direto; logo atualiza sidebar.  
**Verificacao:** E2E por role, upload de logo, editor/publicacao wiki e teste de rota protegida.  
**Dependencias:** Tasks 12, 16-17.  
**Arquivos provaveis:** `frontend/src/views/app/StaffView.vue`, `frontend/src/views/app/WikiView.vue`, `frontend/src/views/app/SettingsView.vue`, `frontend/src/components/Logo.vue`, `frontend/tests/admin-modules.spec.ts`.  
**Escopo:** M (5 arquivos).

### Checkpoint 5: MVP funcional

- [ ] Oito modulos possuem tela ou estado explicitamente autorizado.
- [ ] Fluxo Master, Funcionario e Cliente passa smoke E2E.
- [ ] Typecheck, unit tests e build passam.
- [ ] Testes de cross-client e cross-firm continuam verdes.

### Bloco 6: Qualidade, reset e shipping

#### Task 19: Implementar testes automatizados completos e contrato OpenAPI

**Aceitacao:** cobertura critica atinge 80%, auth/isolamento atingem 100%, testes de contrato validam exemplos e Playwright cobre desktop/mobile.  
**Verificacao:** `pytest --cov`, `npm run test:unit`, `npm run test:e2e` e validacao do OpenAPI.  
**Dependencias:** Tasks 1-18.  
**Arquivos provaveis:** `backend/tests/*`, `frontend/tests/*`, `frontend/playwright.config.ts`, `scripts/validate_openapi.*`.  
**Escopo:** M (5 areas de arquivos).

#### Task 20: Adicionar reset demo, observabilidade e hardening

**Aceitacao:** reset aborta em producao, preserva Master e limpa storage demo; logs possuem request id sem secrets/PII; headers, CORS e limites de upload estao configurados.  
**Verificacao:** teste do comando em demo/producao, scan de secrets e testes de seguranca.  
**Dependencias:** Tasks 8, 11-12.  
**Arquivos provaveis:** `backend/app/cli/reset_demo.py`, `backend/app/core/logging.py`, `backend/app/core/config.py`, `.github/workflows/demo-reset.yml`, `backend/tests/integration/test_demo_reset.py`.  
**Escopo:** M (5 arquivos).

#### Task 21: Preparar Render, Vercel e documentacao operacional

**Aceitacao:** `render.yaml`, `vercel.json`, Dockerfiles, healthchecks, migrations de release e README de deploy documentam variaveis sem valores reais.  
**Verificacao:** validar YAML/JSON, build das imagens, smoke dos healthchecks e checklist manual de deploy.  
**Dependencias:** Tasks 2-3, 19-20.  
**Arquivos provaveis:** `render.yaml`, `vercel.json`, `README.md`, `backend/Dockerfile`, `frontend/Dockerfile`.  
**Escopo:** S (5 arquivos).

### Checkpoint 6: Pronto para `/test`, `/review` e `/ship`

- [ ] Build backend/frontend reproduzivel.
- [ ] Suite automatizada e testes de seguranca passam.
- [ ] Configuracoes de deploy nao possuem secrets.
- [ ] Revisao arquitetural confirma limites e isolamento.
- [ ] Somente apos aprovacao do usuario o deploy sera executado.

## Oportunidades de paralelizacao

- Apos Tasks 6-8 estabilizarem os contratos de auth/policies, testes de contrato e tipos frontend podem ser preparados em paralelo.
- Tasks 9, 10 e 11 podem ser desenvolvidas em paralelo somente depois da migration/base de identidade e do contrato de autorizacao.
- Tasks 16, 17 e 18 podem ser desenvolvidas em paralelo apos AppLayout e services/tipos comuns.
- Migrations compartilhadas, contratos OpenAPI e configuracao de deploy devem permanecer sequenciais.

## Riscos e mitigacoes

| Risco | Impacto | Mitigacao |
|---|---|---|
| Storage/email gratuito atingir quota | Medio | adapters, limite de upload, adapter console, monitoramento e reset demo |
| Vazamento cross-client ou cross-firm | Alto | filtros obrigatorios por `firm_id`, policies centralizadas e testes negativos |
| Refresh token roubado/reutilizado | Alto | cookie HttpOnly, hash persistido, rotacao e revogacao por familia |
| Escopo crescer para ERP completo | Alto | manter faturamento operacional e integrações fora do MVP |
| Frontend divergir do OpenAPI | Medio | tipos derivados/conferidos, testes de contrato e CI |
| Reset atingir producao | Critico | bloqueio por `APP_ENV`, credencial separada e sem workflow apontando para prod |
| Documentos conterem dados sensiveis | Alto | bucket privado, URLs assinadas, logs sem PII e controles LGPD pendentes |

## Questoes que permanecem abertas

- Nome, identidade visual, dominio e timezone do escritorio.
- Campos e categorias obrigatorios de processos.
- Atualizacao em tempo real ou sob demanda para movimentacoes do cliente.
- Requisitos especificos de retencao, exportacao e exclusao sob LGPD.

## Definition of Done do plano

- Cada task possui criterios de aceitacao, verificacao, dependencias e escopo.
- Cada checkpoint deixa o sistema executavel e testado.
- Nenhuma task individual deve ultrapassar aproximadamente cinco arquivos principais.
- Mudancas no modelo ou contrato exigem atualizar `SPEC.md` antes da implementacao.
- O usuario aprova este plano antes do `/build`.

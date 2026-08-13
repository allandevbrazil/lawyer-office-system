# Checklist de Execucao: ERP LawFirm MVP

**Plano:** [plan.md](plan.md)  
**Especificacao:** [../SPEC.md](../SPEC.md)  
**Status:** `/build` em execucao automatica com validacao por task

## Bloco 1: Infraestrutura e fundacao

- [x] Task 1: Criar esqueleto do monorepo
- [x] Task 2: Configurar PostgreSQL e containers
- [x] Task 3: Inicializar FastAPI, Vue e ferramentas
- [x] Checkpoint 1: Fundacao validada

## Bloco 2: Identidade, autenticacao e autorizacao

- [x] Task 4: Criar base SQLAlchemy, Alembic e entidades de identidade
- [x] Task 5: Implementar seguranca, seed Master e sessao JWT
- [x] Task 6: Entregar login, refresh, logout e perfil
- [x] Task 7: Implementar convites de clientes e recuperacao de senha
- [x] Task 8: Implementar policies RBAC e isolamento por firma
- [x] Checkpoint 2: Identidade segura validada

## Bloco 3: Dominio de negocio e API

- [x] Task 9: Implementar clientes, processos, partes e movimentacoes
- [x] Task 10: Implementar servicos, faturas e dashboard
- [x] Task 11: Implementar documentos com storage adapter
- [x] Task 12: Implementar wiki, funcionarios, configuracoes e atividades
- [x] Checkpoint 3: API de negocio validada

## Bloco 4: Frontend base e autenticacao

- [x] Task 13: Configurar design system, Axios, tipos e stores
- [x] Task 14: Implementar rotas publicas e fluxo de auth
- [x] Task 15: Criar AppLayout, sidebar e componentes de estado
- [x] Checkpoint 4: Shell frontend validado

## Bloco 5: Telas privadas e integracao

- [x] Task 16: Implementar dashboard e telas de processos
- [x] Task 17: Implementar faturas, clientes e documentos
- [x] Task 18: Implementar funcionarios, wiki e configuracoes
- [x] Checkpoint 5: MVP funcional validado

## Bloco 6: Qualidade, reset e shipping

- [x] Task 19: Implementar testes automatizados completos e contrato OpenAPI
- [x] Task 20: Adicionar reset demo, observabilidade e hardening
- [x] Task 21: Preparar Render, Vercel e documentacao operacional
- [x] Checkpoint 6: Pronto para `/test`, `/review` e `/ship`

## Gates de processo

- [ ] `/spec` aprovada e mantida atualizada
- [ ] `/plan` aprovado pelo usuario
- [ ] Cada task validada antes da proxima
- [ ] `/test` executado com backend, frontend e E2E (backend/frontend automatizados concluídos; E2E Playwright pendente)
- [x] `/review` concluido sem falhas criticas
- [ ] `/ship` autorizado explicitamente pelo usuario

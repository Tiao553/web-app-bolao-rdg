# Bolão Copa RDG

Sistema de bolão para Copa do Mundo 2026.

## Stack

- **Frontend**: Next.js 15 + React 19 + TypeScript
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Email**: Resend
- **Deploy**: Vercel

## Quick Start

### Pré-requisitos

- Docker + Docker Compose
- Node.js 20+
- Python 3.12+

### Variáveis de Ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env.local
```

Configure suas variáveis:

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | URL de conexão PostgreSQL |
| `RESEND_API_KEY` | API Key do Resend (começa com `re_`) |
| `EMAIL_FROM` | Email remetente (ex: `Bolão RDG <noreply@seudominio.com>`) |
| `FRONTEND_URL` | URL do frontend para links de recuperação |

### Rodar com Docker

```bash
docker compose up -d
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Rodar Local (Desenvolvimento)

**Backend:**

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd app
npm install
npm run dev
```

## Estrutura

```
├── app/                    # Frontend Next.js
│   ├── src/
│   │   ├── app/           # Rotas (App Router)
│   │   ├── components/    # Componentes React
│   │   └── lib/           # Utilitários
│   └── package.json
├── backend/                # API FastAPI
│   ├── app/
│   │   ├── api/           # Rotas da API
│   │   ├── core/          # Configurações
│   │   ├── models/        # Modelos SQLAlchemy
│   │   ├── services/      # Lógica de negócio
│   │   └── main.py
│   └── pyproject.toml
├── database/               # Migrations e Seeds
│   └── migrations/
├── docs/                   # Documentação de produto
└── docker-compose.yml
```

## Funcionalidades

### Usuário

- ✅ Cadastro com aprovação admin
- ✅ Login/Logout
- ✅ Recuperação de senha por email
- ✅ Palpite de campeão e artilheiro
- ✅ Palpites por fase/jogo
- ✅ Ranking
- ✅ Chaveamento
- ✅ Área Explore (após fechamento)

### Administrador

- ✅ Dashboard administrativo
- ✅ Gestão de usuários (aprovar/rejeitar/bloquear)
- ✅ Gestão de partidas
- ✅ Gestão de jogadores
- ✅ Override manual de resultados
- ✅ Integração com API Football e Google Sheets
- ✅ Configuração de janela de palpites
- ✅ Bloqueio de fases

## Scripts

```bash
# Rodar migrations
docker compose exec backend alembic upgrade head

# Rodar testes backend
cd backend && uv run pytest

# Rodar lint backend
cd backend && uv run ruff check .
```

## Email (Resend)

1. Crie conta em https://resend.com
2. Gere API Key em https://resend.com/api-keys
3. Configure domínio em https://resend.com/domains (ou use `onboarding@resend.dev` para testes)

### Modo Desenvolvimento

Se `RESEND_API_KEY` não estiver configurado, o sistema loga o link de reset no console:

```
============================================================
[DEV] Email para: usuario@email.com
[DEV] Assunto: Recuperação de senha — Bolão Copa RDG
[DEV] Link de reset: http://localhost:3000/reset-password?token=xxx
============================================================
```

## Deploy

### Vercel (Backend + Frontend)

1. Conecte o repositório na Vercel
2. Configure as variáveis de ambiente
3. Deploy automático a cada push

### Variáveis Vercel

```bash
# Backend
DATABASE_URL=postgresql+psycopg://...
RESEND_API_KEY=re_xxx
EMAIL_FROM=Bolão RDG <noreply@seudominio.com>
FRONTEND_URL=https://seu-app.vercel.app

# Frontend
API_BASE_URL=https://seu-backend.vercel.app
```

## Licença

MIT

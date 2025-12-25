# PIX WhatsApp Automation

Sistema de Automação e Controle de Pagamentos PIX via WhatsApp com integração Mercado Pago.

## Visão Geral

Automatiza cobranças mensais via PIX utilizando:
- WhatsApp (API oficial da Meta)
- Geração de PIX dinâmico pelo Mercado Pago
- Confirmação via webhook
- Persistência em banco de dados
- Controle operacional por Google Sheets

## Tecnologias

- **Backend**: Python 3.11 + FastAPI
- **Banco de Dados**: PostgreSQL
- **WhatsApp**: Meta Cloud API
- **Pagamentos**: Mercado Pago PIX
- **Planilha**: Google Sheets API
- **Infraestrutura**: Docker + Docker Compose

## Estrutura do Projeto

```
pix/
├── src/
│   ├── api/              # Endpoints da API
│   ├── core/             # Configurações, middleware, logging
│   ├── models/           # Modelos do banco de dados
│   ├── schemas/          # Schemas Pydantic
│   ├── services/         # Lógica de negócio
│   ├── utils/            # Utilitários
│   └── main.py           # Aplicação FastAPI
├── tests/
│   ├── unit/             # Testes unitários
│   └── integration/      # Testes de integração
├── scripts/              # Scripts auxiliares
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Conta Meta Developer (WhatsApp Cloud API)
- Conta Mercado Pago Developer
- Conta Google Cloud (Sheets API)

## Instalação

### 1. Clone o repositório

```bash
git clone <repository-url>
cd pix
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

- **WhatsApp**: Obtenha em https://developers.facebook.com/apps
- **Mercado Pago**: Obtenha em https://www.mercadopago.com.br/developers/panel/app
- **Google Sheets**: Obtenha em https://console.cloud.google.com/apis/credentials

### 3. Opção A: Executar com Docker (Recomendado)

```bash
# Build e start dos containers
docker-compose up --build

# Em modo detached
docker-compose up -d

# Ver logs
docker-compose logs -f app
```

A aplicação estará disponível em: `http://localhost:8000`

### 4. Opção B: Executar localmente

#### Instalar dependências

Com Poetry:
```bash
poetry install
poetry shell
```

Ou com pip:
```bash
pip install -r requirements.txt
```

#### Executar banco de dados
```bash
docker-compose up -d db
```

#### Executar aplicação
```bash
python -m src.main
# ou
uvicorn src.main:app --reload
```

## Configuração de Credenciais

### WhatsApp Cloud API

1. Acesse: https://developers.facebook.com/apps
2. Crie um app com produto WhatsApp
3. Configure webhook URL: `https://seu-dominio.com/webhooks/whatsapp`
4. Obtenha:
   - Phone Number ID
   - Access Token
   - Verify Token (crie um aleatório)

### Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Crie uma aplicação
3. Configure webhook URL: `https://seu-dominio.com/webhooks/mercadopago`
4. Obtenha:
   - Access Token
   - Public Key

### Google Sheets

Veja o guia completo em: [docs/GOOGLE_SHEETS_SETUP.md](docs/GOOGLE_SHEETS_SETUP.md)

Resumo:
1. Crie um projeto no Google Cloud Console
2. Habilite a Google Sheets API
3. Crie um Service Account e baixe o JSON
4. Crie uma planilha e compartilhe com o service account
5. Execute: `python scripts/setup_sheets.py`

## Uso

### Health Check

```bash
curl http://localhost:8000/health
```

### Documentação da API

Acesse: `http://localhost:8000/docs` (Swagger UI)

### Logs

Os logs são estruturados e incluem `request_id` para rastreabilidade:

```json
{
  "event": "incoming_request",
  "request_id": "req_2025_03_08_a1b2c3",
  "method": "POST",
  "url": "/pix/create",
  "timestamp": "2025-03-08T10:30:00Z"
}
```

## Desenvolvimento

### Testes

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/
pytest tests/integration/
```

### Formatação de código

```bash
# Black
black src/ tests/

# Ruff
ruff check src/ tests/
ruff check --fix src/ tests/
```

### Type checking

```bash
mypy src/
```

## Regras de Negócio

- Pagamento exclusivamente mensal
- Valores fixos:
  - R$ 70 — individual
  - R$ 90 — 2 pessoas
  - R$ 100 — 4 pessoas
- Um PIX por interação
- Validade do PIX: 6 horas
- Pagamento válido somente com status `approved`
- Um pagamento por mês por apartamento

## Request ID

Todas as requisições geram um `request_id` único:

Formato: `req_YYYY_MM_DD_<hash>`

O `request_id` é propagado para:
- Headers de resposta (`X-Request-ID`)
- Logs
- Banco de dados
- Google Sheets
- Webhooks processados

## Padrão de Resposta

Todas as respostas seguem o formato:

```json
{
  "request_id": "req_2025_03_08_a1b2c3",
  "success": true,
  "action": "create_pix",
  "data": {},
  "error": null,
  "timestamp": "2025-03-08T10:30:00Z"
}
```

## Roadmap

- [x] ÉPICO 1 — Infraestrutura Base
- [x] ÉPICO 2 — Modelos de Banco de Dados
- [x] ÉPICO 3 — Bot WhatsApp
- [x] ÉPICO 4 — Geração de PIX
- [x] ÉPICO 5 — Webhooks Mercado Pago
- [x] ÉPICO 6 — Google Sheets
- [ ] ÉPICO 7 — Notificações
- [ ] ÉPICO 8 — Observabilidade Avançada

## Referências

- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Mercado Pago PIX](https://www.mercadopago.com.br/developers/pt/docs/checkout-bricks/payment-brick/payment-submission/pix)
- [Webhooks Mercado Pago](https://www.mercadopago.com.br/developers/pt/docs/notifications/webhooks)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Sheets API](https://developers.google.com/sheets/api)

## Licença

MIT

## Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

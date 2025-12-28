# Migração de FastAPI para n8n

## Visão Geral da Migração

Este documento descreve a transformação do sistema de automação PIX de uma aplicação FastAPI (Python) para workflows n8n.

## Por que n8n?

- **Visual workflow builder**: Facilita manutenção e entendimento
- **Sem código**: Reduz bugs e complexidade
- **Integração nativa**: WhatsApp, Google Sheets, PostgreSQL built-in
- **Webhooks**: Suporte nativo para WhatsApp e Mercado Pago
- **Escalabilidade**: Queue-based execution
- **Observabilidade**: Logs e execuções visuais

## Mapeamento de Funcionalidades

### FastAPI → n8n

| FastAPI Component | n8n Equivalent |
|------------------|----------------|
| `src/main.py` + FastAPI | n8n Web Service |
| `src/api/whatsapp.py` | WhatsApp Trigger Node |
| `src/services/conversation_handler.py` | Switch + Set Nodes (State Machine) |
| `src/services/mercadopago_service.py` | HTTP Request Node |
| `src/api/mercadopago.py` | Webhook Trigger Node |
| `src/services/webhook_processor.py` | Function + Postgres Nodes |
| `src/services/whatsapp.py` | WhatsApp Node |
| Google Sheets service | Google Sheets Node |
| PostgreSQL Models | Postgres Node |
| Middleware request_id | n8n execution ID |
| Logs estruturados | n8n Execution logs |

## Arquitetura n8n

### Workflows Principais

#### 1. **WhatsApp Bot Workflow** (Conversação)
```
WhatsApp Trigger
    ↓
Extract Phone & Message
    ↓
Get/Create Conversation State (Postgres)
    ↓
Switch (Current Step)
    ├─ START → Send Welcome → Update State (COLLECT_NAME)
    ├─ COLLECT_NAME → Validate → Store Name → Next (COLLECT_CONDO)
    ├─ COLLECT_CONDO → Store Condo → Next (COLLECT_BLOCK)
    ├─ COLLECT_BLOCK → Store Block → Next (COLLECT_APARTMENT)
    ├─ COLLECT_APARTMENT → Store Apartment → Next (SELECT_PLAN)
    └─ SELECT_PLAN → Validate Plan → Trigger PIX Workflow
```

**Nodes principais:**
- WhatsApp Trigger (receber mensagens)
- Postgres (ler/gravar estado da conversação)
- Switch (máquina de estados)
- WhatsApp (enviar mensagens)
- HTTP Request (chamar workflow PIX)

#### 2. **PIX Generation Workflow** (Geração de PIX)
```
Webhook Trigger (chamada interna)
    ↓
Extract Data (phone, name, condo, block, apartment, amount)
    ↓
Create/Update Client (Postgres)
    ↓
Generate External Reference (PIX|YYYY-MM|VALOR|TELEFONE|APARTAMENTO)
    ↓
Create PIX Payment (HTTP → Mercado Pago API)
    ↓
Extract PIX Code & QR Code
    ↓
Fork:
    ├─ Save Payment to Postgres (status: pending)
    ├─ Add Row to Google Sheets
    └─ Send PIX to WhatsApp
```

**Nodes principais:**
- Webhook Trigger
- Postgres (criar/atualizar cliente e payment)
- Function (gerar external_reference)
- HTTP Request (Mercado Pago API)
- Google Sheets (adicionar linha)
- WhatsApp (enviar PIX)

#### 3. **Mercado Pago Webhook Workflow** (Confirmação de Pagamento)
```
Webhook Trigger (Mercado Pago)
    ↓
Extract payment_id & notification_id
    ↓
Check Idempotency (Postgres - processed_webhooks)
    ↓
IF already_processed → Return 200
    ↓
Get Payment Details (HTTP → Mercado Pago API)
    ↓
Find Payment in DB (Postgres)
    ↓
Switch (Payment Status)
    ├─ approved → Update DB → Update Sheets → Send Confirmation WhatsApp
    ├─ cancelled → Update DB
    ├─ rejected → Update DB
    └─ pending → Update DB
    ↓
Mark as Processed (Postgres)
    ↓
Return 200 OK
```

**Nodes principais:**
- Webhook Trigger
- Postgres (buscar payment, verificar idempotência)
- HTTP Request (Mercado Pago API)
- Switch (status do pagamento)
- Google Sheets (atualizar status)
- WhatsApp (confirmação)

### Tabelas PostgreSQL

As mesmas tabelas do sistema FastAPI:

**clients**
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    condo VARCHAR(255),
    block VARCHAR(50),
    apartment VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**payments**
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    client_id INTEGER REFERENCES clients(id),
    month_ref VARCHAR(7) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    mp_payment_id VARCHAR(100),
    external_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP
);
```

**conversation_states**
```sql
CREATE TABLE conversation_states (
    phone VARCHAR(20) PRIMARY KEY,
    step VARCHAR(50) NOT NULL,
    data JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**processed_webhooks**
```sql
CREATE TABLE processed_webhooks (
    webhook_key VARCHAR(255) PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT NOW()
);
```

## Vantagens da Migração

### 1. Manutenibilidade
- Interface visual facilita entendimento
- Mudanças rápidas sem redeploy de código
- Debug visual de execuções

### 2. Redução de Código
- ~2000 linhas Python → 3 workflows visuais
- Sem necessidade de testes unitários (lógica visual)
- Integração nativa com APIs

### 3. Observabilidade
- Execuções registradas automaticamente
- Logs estruturados por node
- Visualização de fluxo de dados

### 4. Escalabilidade
- Queue-based execution
- Horizontal scaling no Render
- Rate limiting built-in

### 5. Flexibilidade
- Adicionar novos passos sem código
- A/B testing de workflows
- Versioning automático

## Desvantagens

### 1. Vendor Lock-in
- Dependência do n8n
- Migração futura mais complexa

### 2. Limitações de Lógica
- Lógica complexa requer Function nodes (JavaScript)
- Menos flexibilidade que Python puro

### 3. Debugging
- Mais difícil para lógica complexa
- Stack traces menos claras

## Comparação de Custos

### FastAPI (self-hosted)
- Server: $7-15/mês (Render/Railway)
- Database: $7/mês (PostgreSQL)
- **Total: ~$14-22/mês**

### n8n (Render)
- Web Service: Free ou $7/mês
- Database: Free (90 dias) ou $7/mês
- **Total: Free ou ~$14/mês**

### n8n Cloud (alternativa)
- Starter: $20/mês (2500 execuções)
- Pro: $50/mês (10000 execuções)

## Roadmap de Migração

- [x] Análise da aplicação FastAPI
- [x] Mapeamento de funcionalidades
- [x] Criação do render.yaml
- [x] Documentação de deploy
- [ ] Deploy no Render
- [ ] Criação de workflows via MCP
- [ ] Testes end-to-end
- [ ] Migração de dados (se necessário)
- [ ] Configuração de webhooks externos
- [ ] Monitoramento e ajustes

## Próximos Passos

1. Fazer push do código para GitHub
2. Deploy no Render via Blueprint
3. Configurar variáveis de ambiente
4. Criar workflows via MCP n8n-mcp
5. Testar fluxos completos
6. Desativar aplicação FastAPI antiga

## Referências

- [n8n Documentation](https://docs.n8n.io)
- [Render n8n Deploy Guide](https://render.com/docs/deploy-n8n)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Mercado Pago API](https://www.mercadopago.com.br/developers/pt/docs)

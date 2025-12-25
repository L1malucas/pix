# API Endpoints Documentation

Documentação completa de todos os endpoints disponíveis na API.

## Base URL

```
http://localhost:8000  (desenvolvimento)
https://sua-url.com    (produção)
```

## Autenticação

Atualmente não há autenticação. Em produção, considere adicionar:
- API Keys para endpoints de criação de PIX
- Validação de assinatura para webhooks
- Rate limiting

---

## Health & Info

### GET /health

Health check do sistema.

**Response:**
```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": true,
  "action": "health_check",
  "data": {
    "status": "healthy",
    "app_name": "pix-whatsapp-automation",
    "environment": "development"
  },
  "error": null,
  "timestamp": "2025-12-25T10:30:00Z"
}
```

### GET /

Informações da API.

**Response:**
```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": true,
  "action": "root",
  "data": {
    "message": "PIX WhatsApp Automation API",
    "version": "0.1.0",
    "docs": "http://localhost:8000/docs"
  },
  "error": null,
  "timestamp": "2025-12-25T10:30:00Z"
}
```

---

## PIX

### POST /pix/create

Cria um PIX de pagamento.

**Request:**
```json
{
  "phone": "5511988887777",
  "name": "João Silva",
  "condo": "Residencial Jardim",
  "block": "A",
  "apartment": "101",
  "plan_value": 70.00,
  "month_ref": "2025-01"  // opcional, usa mês atual se omitido
}
```

**Response (200 OK):**
```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": true,
  "action": "create_pix",
  "data": {
    "client_id": 1,
    "payment_id": 1,
    "mp_payment_id": "123456789",
    "pix_code": "00020126580014br.gov.bcb.pix...",
    "qr_code_base64": "iVBORw0KGgo...",
    "amount": 70.0,
    "expiration_hours": 6,
    "external_reference": "PIX|2025-01|70.00|5511988887777|101",
    "month_ref": "2025-01"
  },
  "error": null,
  "timestamp": "2025-12-25T10:30:00Z"
}
```

**Response (400 Bad Request - Pagamento já existe):**
```json
{
  "detail": "Client already has an approved payment for 2025-01"
}
```

**Response (500 Internal Server Error):**
```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": false,
  "action": "create_pix",
  "data": null,
  "error": {
    "code": "PIX_CREATION_FAILED",
    "message": "Failed to generate PIX code from Mercado Pago",
    "source": "pix_service"
  },
  "timestamp": "2025-12-25T10:30:00Z"
}
```

---

## WhatsApp Webhooks

### GET /webhooks/whatsapp/

Verificação do webhook (chamado pelo Meta).

**Query Parameters:**
- `hub.mode` - Deve ser "subscribe"
- `hub.challenge` - String de desafio a retornar
- `hub.verify_token` - Token de verificação configurado

**Response:**
```
test123  (retorna o hub.challenge)
```

**Error (403 Forbidden):**
```json
{
  "detail": "Invalid verify token"
}
```

### POST /webhooks/whatsapp/

Recebe mensagens do WhatsApp.

**Request (exemplo):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "123456789",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "5511999999999",
          "phone_number_id": "123456789"
        },
        "contacts": [{
          "profile": {"name": "João Silva"},
          "wa_id": "5511988887777"
        }],
        "messages": [{
          "from": "5511988887777",
          "id": "wamid.test123",
          "timestamp": "1234567890",
          "type": "text",
          "text": {"body": "Olá"}
        }]
      },
      "field": "messages"
    }]
  }]
}
```

**Response:**
```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": true,
  "action": "webhook_received",
  "data": {
    "messages_processed": 1,
    "total_messages": 1
  },
  "error": null,
  "timestamp": "2025-12-25T10:30:00Z"
}
```

---

## Mercado Pago Webhooks

### GET /webhooks/mercadopago/test

Testa conectividade do webhook.

**Response:**
```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": true,
  "action": "webhook_test",
  "data": {
    "message": "Mercado Pago webhook endpoint is accessible",
    "endpoint": "/webhooks/mercadopago/"
  },
  "error": null,
  "timestamp": "2025-12-25T10:30:00Z"
}
```

### POST /webhooks/mercadopago/

Recebe notificações de pagamento do Mercado Pago.

**Request (exemplo):**
```json
{
  "action": "payment.updated",
  "api_version": "v1",
  "data": {
    "id": "123456789"
  },
  "date_created": "2025-01-15T10:30:00Z",
  "id": 987654321,
  "live_mode": false,
  "type": "payment",
  "user_id": "123456"
}
```

**Response:**
```
OK  (sempre retorna 200 OK)
```

**Nota**: Este endpoint sempre retorna 200 OK, mesmo em caso de erro, para evitar que o Mercado Pago fique reenviando o webhook indefinidamente.

---

## Padrão de Resposta

Todos os endpoints (exceto webhooks) seguem o padrão:

```json
{
  "request_id": "req_YYYY_MM_DD_<hash>",
  "success": true|false,
  "action": "nome_da_acao",
  "data": {},
  "error": {
    "code": "ERROR_CODE",
    "message": "Mensagem de erro",
    "source": "fonte_do_erro"
  },
  "timestamp": "ISO-8601"
}
```

## Headers

### Request ID

Todas as requisições recebem um `request_id` único para rastreabilidade:

```
X-Request-ID: req_2025_12_25_abc123
```

Este ID é:
- Gerado automaticamente
- Incluído nos logs
- Propagado para serviços externos
- Retornado no header de resposta

---

## Rate Limiting

Atualmente não implementado. Em produção, adicionar:

```python
# Limite por IP
- 100 requisições/minuto para /pix/create
- 1000 requisições/minuto para webhooks
```

---

## Erros Comuns

### 400 Bad Request
- Dados inválidos no request
- Campos obrigatórios ausentes
- Formato de dados incorreto

### 403 Forbidden
- Token de verificação inválido (WhatsApp webhook)

### 404 Not Found
- Endpoint não existe

### 500 Internal Server Error
- Erro no Mercado Pago
- Erro no WhatsApp API
- Erro de banco de dados

---

## Swagger UI

Documentação interativa disponível em:

```
http://localhost:8000/docs
```

Permite testar todos os endpoints diretamente pelo navegador.

---

## cURL Examples

### Criar PIX

```bash
curl -X POST http://localhost:8000/pix/create \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511988887777",
    "name": "João Silva",
    "condo": "Residencial Jardim",
    "block": "A",
    "apartment": "101",
    "plan_value": 70.00
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Testar Webhook MP

```bash
curl http://localhost:8000/webhooks/mercadopago/test
```

### Verificar Webhook WhatsApp

```bash
curl "http://localhost:8000/webhooks/whatsapp/?hub.mode=subscribe&hub.challenge=test&hub.verify_token=seu_token"
```

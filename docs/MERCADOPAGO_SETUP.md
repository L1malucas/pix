# Mercado Pago Webhook Setup Guide

Este guia explica como configurar webhooks do Mercado Pago para receber notificações de pagamento.

## 1. Configurar Webhook no Mercado Pago

### 1.1. Acessar Dashboard

1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Selecione sua aplicação
3. Navegue até **Webhooks**

### 1.2. Configurar URL do Webhook

**URL de Notificação:**
```
https://sua-url.com/webhooks/mercadopago/
```

**Eventos para assinar:**
- ✅ `payment` (obrigatório)

### 1.3. Testar Conectividade

Antes de configurar, teste se a URL está acessível:

```bash
curl https://sua-url.com/webhooks/mercadopago/test
```

Deve retornar:
```json
{
  "request_id": "req_...",
  "success": true,
  "action": "webhook_test",
  "data": {
    "message": "Mercado Pago webhook endpoint is accessible",
    "endpoint": "/webhooks/mercadopago/"
  }
}
```

## 2. Configurar Ambiente Local (ngrok)

Para testar localmente, use ngrok:

```bash
# Iniciar ngrok
ngrok http 8000

# Copie a URL HTTPS (ex: https://abc123.ngrok.io)
# Configure no Mercado Pago: https://abc123.ngrok.io/webhooks/mercadopago/
```

## 3. Fluxo de Processamento

### 3.1. Webhook Recebido

```
Mercado Pago → POST /webhooks/mercadopago/
```

Payload:
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

### 3.2. Processamento

1. **Validação**: Verifica tipo do evento (payment)
2. **Idempotência**: Checa se já foi processado
3. **Busca Pagamento MP**: GET /v1/payments/{id}
4. **Atualiza DB**: Atualiza status do payment
5. **Notifica Cliente**: Envia mensagem WhatsApp
6. **Retorna 200 OK**: Confirma processamento

### 3.3. Estados de Pagamento

| Status MP | Status DB | Ação |
|-----------|-----------|------|
| `approved` | `approved` | Confirma pagamento + notifica cliente |
| `pending` | `pending` | Mantém como pendente |
| `cancelled` | `cancelled` | Marca como cancelado |
| `rejected` | `rejected` | Marca como rejeitado |

## 4. Idempotência

O sistema garante que cada webhook é processado apenas uma vez:

```python
webhook_key = f"{notification_id}_{mp_payment_id}"
# Armazenado em memória (usar Redis em produção)
```

## 5. Mensagem de Confirmação

Quando pagamento é aprovado, cliente recebe via WhatsApp:

```
✅ Pagamento confirmado!

💰 Valor: R$ 70,00
📅 Referência: 2025-01
🏢 Residencial Jardim - Bloco A - Apto 101

Obrigado pelo pagamento! Seu recibo está registrado no sistema.

ID do pagamento: 123456789
```

## 6. Logs

Todos os eventos são logados:

```bash
docker-compose logs -f app | grep mercadopago
```

Exemplos de logs:
```
mercadopago_webhook_received
mercadopago_payment_status
payment_approved
payment_confirmation_sent
webhook_processed_successfully
```

## 7. Testar Webhook Manualmente

### 7.1. Simular Webhook do Mercado Pago

```bash
curl -X POST http://localhost:8000/webhooks/mercadopago/ \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

Nota: Isso irá buscar o pagamento real no Mercado Pago usando o ID fornecido.

### 7.2. Testar com Payload de Exemplo

```bash
curl -X POST http://localhost:8000/webhooks/mercadopago/ \
  -H "Content-Type: application/json" \
  -d @tests/test_mp_webhook.json
```

## 8. Monitoramento

### 8.1. Verificar Pagamentos Processados

```bash
docker-compose exec db psql -U postgres -d pix_automation \
  -c "SELECT id, request_id, status, mp_payment_id, amount, paid_at FROM payments ORDER BY created_at DESC LIMIT 10;"
```

### 8.2. Verificar Webhooks no Mercado Pago

Acesse o Dashboard → Webhooks → Histórico de notificações

Você verá:
- ✅ 200 OK - Webhook processado
- ❌ 4xx/5xx - Erro (MP tentará reenviar)

## 9. Tratamento de Erros

### 9.1. Pagamento Não Encontrado

Se o payment não existir no banco:
- Log: `payment_not_found_in_database`
- Retorno: 200 OK (evita retry)

### 9.2. Webhook Já Processado

Se o webhook já foi processado:
- Log: `webhook_already_processed`
- Retorno: 200 OK imediatamente

### 9.3. Erro no Processamento

Em caso de erro:
- Log: `webhook_processing_failed`
- Retorno: 200 OK (evita retry infinito)

**Nota**: Retornamos 200 OK mesmo com erro para evitar que o Mercado Pago fique reenviando webhooks indefinidamente.

## 10. Segurança

### 10.1. Validação de Assinatura (Futuro)

O Mercado Pago envia header `x-signature` para validar autenticidade:

```python
# TODO: Implementar validação de assinatura
# x_signature = Header("x-signature")
# validate_signature(payload, x_signature)
```

### 10.2. IP Whitelist (Opcional)

IPs do Mercado Pago (produção):
```
209.225.49.0/24
216.33.197.0/24
216.33.196.0/24
```

## 11. Troubleshooting

### Webhook não está chegando?

1. **Verifique URL**: Deve ser HTTPS em produção
2. **Teste conectividade**: `curl https://sua-url.com/webhooks/mercadopago/test`
3. **Verifique firewall**: Libere IPs do Mercado Pago
4. **Confira logs**: `docker-compose logs -f app`

### Pagamento não atualizou?

1. **Verifique logs**: Busque pelo `mp_payment_id`
2. **Confira banco**: `SELECT * FROM payments WHERE mp_payment_id = '123456789'`
3. **Veja status no MP**: Dashboard → Pagamentos

### Cliente não recebeu confirmação?

1. **Verifique logs**: Busque `payment_confirmation_sent`
2. **Confira credenciais WhatsApp**: `.env` → `WHATSAPP_ACCESS_TOKEN`
3. **Teste envio manual**: Use endpoint `/pix/create` diretamente

## 12. Referências

- [Mercado Pago Webhooks Docs](https://www.mercadopago.com.br/developers/pt/docs/notifications/webhooks)
- [Payment API Reference](https://www.mercadopago.com.br/developers/pt/reference/payments/_payments_id/get)
- [Webhook Events](https://www.mercadopago.com.br/developers/pt/docs/notifications/webhooks/events)

# Quick Start Guide

Guia rápido para colocar o sistema PIX WhatsApp em funcionamento.

## 🚀 Setup Rápido (5 minutos)

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <repository-url>
cd pix

# Configure variáveis de ambiente
cp .env.example .env
```

### 2. Edite o .env

Apenas 3 configurações essenciais para começar:

```bash
# WhatsApp (obtenha em https://developers.facebook.com/apps)
WHATSAPP_PHONE_NUMBER_ID=seu_phone_id
WHATSAPP_ACCESS_TOKEN=seu_token

# Mercado Pago (obtenha em https://mercadopago.com.br/developers)
MERCADOPAGO_ACCESS_TOKEN=seu_token_mp
```

### 3. Inicie o Sistema

```bash
# Inicie todos os containers
docker-compose up -d

# Aguarde ~10 segundos para os containers iniciarem
docker-compose logs -f app
```

### 4. Verifique

```bash
# Health check
curl http://localhost:8000/health

# Deve retornar:
# {"success": true, "data": {"status": "healthy"}}
```

## ✅ Pronto!

Agora você pode:
- Receber mensagens no WhatsApp
- Gerar PIX automaticamente
- Receber webhooks do Mercado Pago

## 📋 Próximos Passos

### Configurar Google Sheets (Opcional, mas recomendado)

Para ter controle operacional em planilha:

```bash
# 1. Siga o guia completo
cat docs/GOOGLE_SHEETS_SETUP.md

# 2. Após configurar, execute:
docker-compose exec app python scripts/setup_sheets.py
```

### Configurar Webhooks

#### WhatsApp Webhook

1. No Meta Developer Dashboard:
   - URL: `https://seu-dominio.com/webhooks/whatsapp/`
   - Verify Token: (o que você colocou no .env)

2. Teste:
```bash
curl "http://localhost:8000/webhooks/whatsapp/?hub.mode=subscribe&hub.challenge=test&hub.verify_token=seu_token"
```

#### Mercado Pago Webhook

1. No Mercado Pago Dashboard:
   - URL: `https://seu-dominio.com/webhooks/mercadopago/`
   - Eventos: payment

2. Teste conectividade:
```bash
curl http://localhost:8000/webhooks/mercadopago/test
```

## 🧪 Testar o Fluxo

### 1. Criar PIX Manualmente

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

Resposta esperada:
```json
{
  "success": true,
  "data": {
    "pix_code": "00020126...",
    "mp_payment_id": "123456789",
    "amount": 70.0
  }
}
```

### 2. Verificar no Banco

```bash
docker-compose exec db psql -U postgres -d pix_automation \
  -c "SELECT id, request_id, status, amount FROM payments;"
```

### 3. Verificar Logs

```bash
# Logs gerais
docker-compose logs -f app

# Filtrar por evento
docker-compose logs -f app | grep "pix_generated"
docker-compose logs -f app | grep "payment_approved"
```

## 📚 Documentação Adicional

- **API Endpoints**: [docs/API_ENDPOINTS.md](API_ENDPOINTS.md)
- **Setup WhatsApp**: [docs/WHATSAPP_SETUP.md](WHATSAPP_SETUP.md) (se existir)
- **Setup Mercado Pago**: [docs/MERCADOPAGO_SETUP.md](MERCADOPAGO_SETUP.md)
- **Setup Google Sheets**: [docs/GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

## 🐛 Troubleshooting Comum

### Erro: "Connection refused" no banco

```bash
# Reinicie os containers
docker-compose down
docker-compose up -d

# Aguarde o PostgreSQL inicializar completamente
docker-compose logs db | grep "ready to accept connections"
```

### Erro: "Invalid token" no WhatsApp

1. Verifique se o token no .env está correto
2. Tokens expiram — gere um novo no Meta Dashboard
3. Reinicie o container: `docker-compose restart app`

### Erro: "PIX code not generated"

1. Verifique o token do Mercado Pago
2. Veja os logs: `docker-compose logs app | grep mercadopago`
3. Confirme que sua conta MP está ativa para PIX

### Containers não sobem

```bash
# Limpe tudo e reconstrua
docker-compose down -v
docker-compose up --build
```

## 🔑 Ambiente de Desenvolvimento vs Produção

### Desenvolvimento (Local)

- Use ngrok para expor webhooks: `ngrok http 8000`
- Use tokens de teste do Mercado Pago
- Debug = true no .env

### Produção

- Configure HTTPS obrigatório
- Use tokens de produção
- Configure Sentry para monitoramento
- Use Redis para cache de webhooks (atualmente em memória)
- Backup automático do banco de dados

## 📊 Comandos Úteis

```bash
# Ver todos os containers
docker-compose ps

# Reiniciar apenas a aplicação
docker-compose restart app

# Ver uso de recursos
docker stats

# Acessar bash do container
docker-compose exec app bash

# Ver últimos 100 logs
docker-compose logs --tail=100 app

# Seguir logs em tempo real
docker-compose logs -f app

# Executar migrations
docker-compose exec app alembic upgrade head

# Criar nova migration
docker-compose exec app alembic revision --autogenerate -m "mensagem"

# Acessar PostgreSQL
docker-compose exec db psql -U postgres -d pix_automation
```

## 🎯 Fluxo Completo do Sistema

```
1. Cliente → WhatsApp Message
              ↓
2. Webhook → Conversation Handler → Extrai dados
              ↓
3. PIX Handler → Cria cliente no DB
              ↓
4. PIX Handler → Gera PIX no Mercado Pago
              ↓
5. PIX Handler → Salva payment no DB
              ↓
6. PIX Handler → Registra na Google Sheets (se configurado)
              ↓
7. PIX Handler → Envia código PIX via WhatsApp
              ↓
8. Cliente → Paga o PIX
              ↓
9. Mercado Pago → Webhook de confirmação
              ↓
10. Webhook Processor → Atualiza status no DB
              ↓
11. Webhook Processor → Atualiza Google Sheets
              ↓
12. Webhook Processor → Envia confirmação via WhatsApp
```

## 🆘 Precisa de Ajuda?

1. Verifique os logs: `docker-compose logs -f app`
2. Consulte a documentação em `docs/`
3. Teste os endpoints em: `http://localhost:8000/docs`
4. Abra uma issue no repositório

---

**Dica**: Comece testando manualmente com `curl` antes de conectar WhatsApp e webhooks. Isso facilita o debug!

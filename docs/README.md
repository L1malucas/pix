# Documentação do Sistema PIX WhatsApp Automation

Documentação completa do sistema de automação de cobranças via PIX integrado ao WhatsApp.

## 📖 Índice

### Guias de Setup

1. **[Quick Start Guide](QUICK_START.md)** ⚡
   - Setup em 5 minutos
   - Configuração mínima para começar
   - Testes básicos
   - Troubleshooting comum

2. **[Google Sheets Setup](GOOGLE_SHEETS_SETUP.md)** 📊
   - Criar projeto Google Cloud
   - Configurar Service Account
   - Autenticação e permissões
   - Inicializar planilha
   - Troubleshooting

3. **[Mercado Pago Setup](MERCADOPAGO_SETUP.md)** 💰
   - Configurar aplicação
   - Webhooks de pagamento
   - Fluxo de processamento
   - Testes e monitoramento
   - Idempotência

### Referências Técnicas

4. **[API Endpoints](API_ENDPOINTS.md)** 🔌
   - Documentação completa de endpoints
   - Exemplos de request/response
   - Códigos de erro
   - Headers e autenticação
   - Exemplos com cURL

## 🚀 Por Onde Começar?

### Primeiro Acesso

1. Leia o [Quick Start Guide](QUICK_START.md)
2. Configure as credenciais básicas (WhatsApp + Mercado Pago)
3. Teste o fluxo com `curl`
4. Configure Google Sheets (opcional)

### Ambiente de Produção

1. Siga o [Quick Start Guide](QUICK_START.md) - seção Produção
2. Configure [Mercado Pago Webhooks](MERCADOPAGO_SETUP.md)
3. Configure [Google Sheets](GOOGLE_SHEETS_SETUP.md) para controle operacional
4. Revise [API Endpoints](API_ENDPOINTS.md) para monitoramento

## 📋 Estrutura da Documentação

```
docs/
├── README.md                    # Este arquivo - índice geral
├── QUICK_START.md               # Guia rápido de início
├── API_ENDPOINTS.md             # Documentação de endpoints
├── MERCADOPAGO_SETUP.md         # Setup Mercado Pago e webhooks
└── GOOGLE_SHEETS_SETUP.md       # Setup Google Sheets
```

## 🎯 Casos de Uso Comuns

### Operação Diária

**"Quero verificar pagamentos do dia"**
- Abra a Google Sheets (se configurado)
- Ou consulte: `GET /payments?date=today` (se implementado)
- Ou acesse o banco: `SELECT * FROM payments WHERE DATE(created_at) = CURRENT_DATE`

**"Cliente não recebeu o PIX"**
1. Busque nos logs: `docker-compose logs app | grep "phone_number"`
2. Verifique status no banco: `SELECT * FROM payments WHERE client_id = X`
3. Reenvie via endpoint: `POST /pix/create`

**"Webhook não atualizou o pagamento"**
1. Veja [MERCADOPAGO_SETUP.md](MERCADOPAGO_SETUP.md) - seção Troubleshooting
2. Verifique logs: `docker-compose logs app | grep webhook`
3. Confirme status no Mercado Pago Dashboard

### Desenvolvimento

**"Quero adicionar um novo endpoint"**
1. Crie em `src/api/`
2. Adicione schema em `src/schemas/`
3. Use service layer em `src/services/`
4. Documente em [API_ENDPOINTS.md](API_ENDPOINTS.md)

**"Quero alterar o fluxo de conversa"**
1. Edite `src/services/conversation_handler.py`
2. Ajuste estados e transições
3. Teste localmente
4. Deploy gradual

**"Quero adicionar nova integração"**
1. Crie service em `src/services/`
2. Configure credenciais em `.env`
3. Adicione documentação em `docs/`
4. Implemente testes

## 🔍 Busca Rápida

### Por Funcionalidade

| Funcionalidade | Arquivo |
|----------------|---------|
| Criar PIX | [API_ENDPOINTS.md](API_ENDPOINTS.md#post-pixcreate) |
| Webhook WhatsApp | [API_ENDPOINTS.md](API_ENDPOINTS.md#whatsapp-webhooks) |
| Webhook Mercado Pago | [MERCADOPAGO_SETUP.md](MERCADOPAGO_SETUP.md) |
| Google Sheets | [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) |
| Health Check | [API_ENDPOINTS.md](API_ENDPOINTS.md#get-health) |

### Por Problema

| Problema | Solução |
|----------|---------|
| Containers não sobem | [QUICK_START.md](QUICK_START.md#troubleshooting-comum) |
| PIX não gera | [QUICK_START.md](QUICK_START.md#erro-pix-code-not-generated) |
| Webhook não chega | [MERCADOPAGO_SETUP.md](MERCADOPAGO_SETUP.md#troubleshooting) |
| Sheets não atualiza | [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md#troubleshooting) |
| Token inválido | [QUICK_START.md](QUICK_START.md#erro-invalid-token-no-whatsapp) |

## 📚 Conceitos Importantes

### Request ID

Todas as requisições têm um `request_id` único:
- Formato: `req_YYYY_MM_DD_<hash>`
- Propagado por todo o sistema
- Essencial para debug e auditoria
- Ver mais em [API_ENDPOINTS.md](API_ENDPOINTS.md#headers)

### Idempotência

Webhooks são processados apenas uma vez:
- Cache em memória (produção: usar Redis)
- Chave: `{notification_id}_{mp_payment_id}`
- Ver detalhes em [MERCADOPAGO_SETUP.md](MERCADOPAGO_SETUP.md#idempotência)

### External Reference

Identificador único do pagamento:
- Formato: `PIX|YYYY-MM|VALOR|TELEFONE|APARTAMENTO`
- Exemplo: `PIX|2025-01|70.00|5511988887777|101`
- Usado para reconciliação

### Padrão de Resposta

```json
{
  "request_id": "req_2025_12_25_abc123",
  "success": true,
  "action": "create_pix",
  "data": {},
  "error": null,
  "timestamp": "2025-12-25T10:30:00Z"
}
```

## 🛠️ Ferramentas Úteis

### Logs Estruturados

```bash
# Ver todos os logs
docker-compose logs -f app

# Filtrar por evento
docker-compose logs app | grep "payment_approved"

# Buscar por request_id
docker-compose logs app | grep "req_2025_12_25_abc123"
```

### Banco de Dados

```bash
# Acessar PostgreSQL
docker-compose exec db psql -U postgres -d pix_automation

# Consultas úteis
SELECT * FROM payments ORDER BY created_at DESC LIMIT 10;
SELECT COUNT(*) FROM payments WHERE status = 'approved';
SELECT SUM(amount) FROM payments WHERE status = 'approved';
```

### API Interativa

Acesse: http://localhost:8000/docs

- Swagger UI completo
- Teste endpoints diretamente
- Veja schemas de request/response
- Gere exemplos de código

## 🔐 Segurança

### Credenciais

- **NUNCA** commite arquivos `.env` ou `credentials.json`
- Use variáveis de ambiente em produção
- Rotacione tokens periodicamente
- Use tokens de teste em desenvolvimento

### Webhooks

- Implemente validação de assinatura (futuro)
- Use HTTPS em produção
- Configure IP whitelist quando possível
- Ver [MERCADOPAGO_SETUP.md](MERCADOPAGO_SETUP.md#segurança)

### Dados Sensíveis

- Telefones e CPFs devem ser tratados com cuidado
- Logs não devem expor dados sensíveis completos
- Google Sheets: compartilhe apenas com pessoas autorizadas

## 📊 Monitoramento

### Métricas Importantes

1. **Taxa de sucesso de PIX**
   - Quantos PIX são gerados com sucesso
   - Monitorar erros na geração

2. **Taxa de conversão**
   - Quantos PIX são pagos
   - Tempo médio para pagamento

3. **Performance de webhooks**
   - Tempo de processamento
   - Taxa de sucesso
   - Webhooks duplicados

4. **Disponibilidade**
   - Uptime da API
   - Tempo de resposta

### Logs a Monitorar

- `pix_generation_failed`
- `webhook_processing_failed`
- `failed_to_send_confirmation`
- `failed_to_update_sheets`

## 🚀 Próximos Passos

### ÉPICO 7 - Notificações (Futuro)

- Lembretes de pagamento
- Alertas de vencimento
- Relatórios diários para admin

### ÉPICO 8 - Observabilidade (Futuro)

- Integração com Sentry
- Métricas com Prometheus
- Dashboards com Grafana
- Alertas automatizados

## 💡 Contribuindo com a Documentação

Ao adicionar novas features:

1. Atualize [API_ENDPOINTS.md](API_ENDPOINTS.md) se criar endpoints
2. Crie guias de setup em arquivos separados
3. Adicione seção de troubleshooting
4. Inclua exemplos práticos
5. Atualize este índice

## 📞 Suporte

1. Verifique esta documentação
2. Consulte os logs: `docker-compose logs -f app`
3. Teste endpoints em: http://localhost:8000/docs
4. Abra uma issue no repositório com:
   - Descrição do problema
   - Logs relevantes
   - Request ID (se aplicável)
   - Passos para reproduzir

---

**Última atualização**: 2025-12-25

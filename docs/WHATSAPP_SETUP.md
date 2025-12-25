# WhatsApp Cloud API Setup Guide

Este guia explica como configurar a integração com WhatsApp Cloud API.

## 1. Pré-requisitos

- Conta Meta Business
- Aplicativo Meta criado com produto WhatsApp
- Número de telefone verificado para WhatsApp Business
- URL pública HTTPS para webhook (ngrok, cloudflare tunnel, ou servidor público)

## 2. Configurar Aplicativo Meta

### 2.1. Criar Aplicativo

1. Acesse: https://developers.facebook.com/apps
2. Clique em "Criar App"
3. Escolha "Negócios" como tipo de app
4. Adicione o produto "WhatsApp"

### 2.2. Obter Credenciais

Navegue até WhatsApp > Início:

1. **Phone Number ID**: Copie o ID do número de telefone
2. **Access Token**: Gere um token de acesso temporário (ou permanente)
3. **Business Account ID**: Copie o ID da conta Business

Adicione estas credenciais no arquivo `.env`:

```bash
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id
WHATSAPP_ACCESS_TOKEN=seu_access_token
WHATSAPP_BUSINESS_ACCOUNT_ID=seu_business_account_id
WHATSAPP_VERIFY_TOKEN=crie_um_token_secreto_aleatorio
```

## 3. Configurar Webhook

### 3.1. Expor Aplicação Publicamente

Se estiver rodando localmente, use ngrok:

```bash
# Instalar ngrok
brew install ngrok

# Criar túnel HTTPS
ngrok http 8000
```

Copie a URL HTTPS fornecida (ex: `https://abc123.ngrok.io`)

### 3.2. Configurar Webhook no Meta

1. Acesse: WhatsApp > Configuração
2. Clique em "Configurar" em Webhooks
3. Configure:
   - **URL de retorno de chamada**: `https://sua-url.com/webhooks/whatsapp/`
   - **Verificar token**: O valor de `WHATSAPP_VERIFY_TOKEN` do seu `.env`
4. Clique em "Verificar e salvar"
5. Assine os seguintes campos:
   - `messages` (obrigatório)
   - `message_status` (opcional, para rastreamento)

## 4. Testar Integração

### 4.1. Verificar Webhook

```bash
curl "http://localhost:8000/webhooks/whatsapp/?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=seu_verify_token"
```

Deve retornar: `test123`

### 4.2. Testar Fluxo Completo

Execute o script de teste:

```bash
./scripts/test_conversation.sh
```

Ou teste manualmente enviando mensagens para o número WhatsApp Business configurado.

### 4.3. Verificar Logs

```bash
docker-compose logs -f app | grep whatsapp
```

## 5. Fluxo de Conversação

O bot segue este fluxo:

1. **START** → Mensagem de boas-vindas
2. **COLLECT_NAME** → Solicita nome completo
3. **COLLECT_CONDO** → Solicita nome do condomínio
4. **COLLECT_BLOCK** → Solicita bloco/torre
5. **COLLECT_APARTMENT** → Solicita número do apartamento
6. **SELECT_PLAN** → Oferece opções de plano (R$ 70, 90 ou 100)
7. **COMPLETED** → Gera PIX (será implementado no ÉPICO 4)

## 6. Mensagens do Bot

### Mensagem Inicial
```
Olá! Bem-vindo ao sistema de pagamentos PIX via WhatsApp.

Vou coletar algumas informações para gerar seu PIX de pagamento mensal.

Para começar, qual é o seu nome completo?
```

### Seleção de Plano
```
Perfeito! Agora selecione o plano desejado:

1️⃣ Individual - R$ 70,00
2️⃣ 2 pessoas - R$ 90,00
3️⃣ 4 pessoas - R$ 100,00

Digite o número do plano (1, 2 ou 3):
```

## 7. Estrutura de Estado

O estado da conversa é armazenado em memória (em produção, usar Redis):

```python
{
    "phone": "5511988887777",
    "step": "SELECT_PLAN",
    "data": {
        "name": "João Silva",
        "condo": "Residencial Jardim",
        "block": "A",
        "apartment": "101",
        "plan": "1",
        "amount": 70.0
    }
}
```

## 8. Endpoints Disponíveis

### GET /webhooks/whatsapp/
Verificação do webhook (chamado pelo Meta)

### POST /webhooks/whatsapp/
Recebe mensagens do WhatsApp

## 9. Próximos Passos

- [ ] Implementar geração de PIX (ÉPICO 4)
- [ ] Adicionar persistência de estado (Redis)
- [ ] Implementar templates de mensagem aprovados
- [ ] Adicionar suporte a mídia (imagens, documentos)
- [ ] Implementar rate limiting
- [ ] Adicionar monitoramento e alertas

## 10. Referências

- [WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Webhook Setup](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)
- [API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)

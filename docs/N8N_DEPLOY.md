# Deploy do n8n no Render

Este guia explica como fazer o deploy da automação PIX usando n8n no Render.

## Visão Geral

A aplicação FastAPI original será substituída por workflows n8n, mantendo todas as funcionalidades:
- Bot conversacional WhatsApp
- Geração de PIX via Mercado Pago
- Processamento de webhooks
- Persistência em PostgreSQL
- Integração com Google Sheets

## Pré-requisitos

1. Conta no Render (gratuita): https://render.com
2. Conta GitHub conectada ao Render
3. Credenciais configuradas:
   - WhatsApp Business Cloud API
   - Mercado Pago
   - Google Sheets API

## Passo 1: Preparar o Repositório

1. Faça commit do arquivo `render.yaml` no repositório:
```bash
git add render.yaml .env.n8n.example docs/N8N_DEPLOY.md
git commit -m "Add n8n Render deployment configuration"
git push origin main
```

## Passo 2: Deploy no Render

### Opção A: Via Blueprint (Recomendado)

1. Acesse o [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New" > "Blueprint"**
3. Conecte seu repositório GitHub
4. Selecione a branch `main`
5. Forneça um nome para o blueprint: `pix-automation-n8n`
6. Clique em **"Deploy Blueprint"**

O Render irá:
- Criar um Web Service com n8n
- Criar um banco PostgreSQL
- Configurar as variáveis de ambiente automaticamente

### Opção B: Manual

1. Acesse o [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New" > "Web Service"**
3. Selecione **"Existing Image"**
4. Image URL: `docker.io/n8nio/n8n:latest`
5. Configure:
   - Name: `pix-automation-n8n`
   - Instance Type: `Free`
   - Health Check Path: `/healthz`

## Passo 3: Configurar Variáveis de Ambiente

Após o deploy, configure as variáveis sensíveis no Render Dashboard:

1. Acesse seu Web Service no Render
2. Vá em **"Environment"**
3. Adicione/Edite as variáveis:

```bash
WEBHOOK_URL=https://pix-automation-n8n.onrender.com
N8N_EDITOR_BASE_URL=https://pix-automation-n8n.onrender.com

# WhatsApp
WHATSAPP_ACCESS_TOKEN=seu_token
WHATSAPP_PHONE_NUMBER_ID=seu_id
WHATSAPP_VERIFY_TOKEN=seu_verify_token

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN=seu_token

# Google Sheets
GOOGLE_SHEETS_CLIENT_EMAIL=email@projeto.iam.gserviceaccount.com
GOOGLE_SHEETS_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
GOOGLE_SHEETS_SPREADSHEET_ID=seu_spreadsheet_id
```

4. Clique em **"Save Changes"** e aguarde o redeploy automático

## Passo 4: Acessar n8n

1. Após o deploy, acesse: `https://pix-automation-n8n.onrender.com`
2. Na primeira vez, você será solicitado a criar uma conta admin do n8n
3. Configure email e senha para acessar o editor

## Passo 5: Configurar Credenciais no n8n

No editor do n8n, configure as credenciais para cada serviço:

### WhatsApp Business Cloud
1. Menu lateral > **Credentials** > **New**
2. Selecione **"WhatsApp Business Cloud API"**
3. Preencha:
   - Access Token: `{{$env.WHATSAPP_ACCESS_TOKEN}}`
   - Phone Number ID: `{{$env.WHATSAPP_PHONE_NUMBER_ID}}`

### Mercado Pago
1. **Credentials** > **New** > **"HTTP Request"** (ou custom credential)
2. Nome: "Mercado Pago"
3. Header Authentication:
   - Name: `Authorization`
   - Value: `Bearer {{$env.MERCADOPAGO_ACCESS_TOKEN}}`

### Google Sheets
1. **Credentials** > **New** > **"Google Sheets API"**
2. Selecione **"Service Account"**
3. Preencha:
   - Service Account Email: `{{$env.GOOGLE_SHEETS_CLIENT_EMAIL}}`
   - Private Key: `{{$env.GOOGLE_SHEETS_PRIVATE_KEY}}`

### PostgreSQL (interno)
1. **Credentials** > **New** > **"Postgres"**
2. As variáveis já estarão configuradas via `render.yaml`:
   - Host: `{{$env.DB_POSTGRESDB_HOST}}`
   - Port: `{{$env.DB_POSTGRESDB_PORT}}`
   - Database: `{{$env.DB_POSTGRESDB_DATABASE}}`
   - User: `{{$env.DB_POSTGRESDB_USER}}`
   - Password: `{{$env.DB_POSTGRESDB_PASSWORD}}`

## Passo 6: Importar Workflows

Os workflows serão criados via MCP após o deploy estar ativo.

Use o comando:
```bash
/mcp
```

E então use as ferramentas do n8n-mcp para criar os workflows automaticamente.

## Passo 7: Configurar Webhooks Externos

### WhatsApp
1. Acesse: https://developers.facebook.com/apps
2. Configure o Webhook URL: `https://pix-automation-n8n.onrender.com/webhook/whatsapp`
3. Verify Token: o valor configurado em `WHATSAPP_VERIFY_TOKEN`

### Mercado Pago
1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Configure Webhook URL: `https://pix-automation-n8n.onrender.com/webhook/mercadopago`

## Estrutura dos Workflows

O sistema terá 3 workflows principais:

### 1. Workflow WhatsApp Bot
- **Trigger**: WhatsApp Trigger
- **Função**: Conversação, coleta de dados
- **Output**: Chama workflow de PIX

### 2. Workflow Geração PIX
- **Trigger**: Webhook/Chamada interna
- **Função**: Criar cliente, gerar PIX no Mercado Pago
- **Output**: Envia PIX via WhatsApp, salva no DB e Sheets

### 3. Workflow Webhook Mercado Pago
- **Trigger**: Webhook
- **Função**: Processar confirmação de pagamento
- **Output**: Atualiza DB, Sheets e notifica cliente

## Monitoramento

- **Logs**: Render Dashboard > Logs
- **Execuções**: n8n Editor > Executions
- **Banco de Dados**: Render Dashboard > Database > Terminal

## Troubleshooting

### Aplicação não inicia
- Verifique os logs no Render Dashboard
- Confirme que todas as variáveis de ambiente estão configuradas
- Verifique o Health Check Path: `/healthz`

### Webhook não funciona
- Confirme que WEBHOOK_URL está correto
- Teste o endpoint: `https://seu-app.onrender.com/healthz`
- Verifique os logs de execução no n8n

### Erro de conexão com PostgreSQL
- As credenciais são configuradas automaticamente via `render.yaml`
- Verifique se o database foi criado junto com o web service

## Upgrade do Plano

O plano free do Render tem limitações:
- Database expira após 90 dias
- Web service pode entrar em sleep após inatividade

Para produção, considere:
- Web Service: `Standard` ($7/mês)
- Database: `Basic 256MB` ($7/mês)

Edite o `render.yaml` e altere os campos `plan` antes do deploy.

## Próximos Passos

1. ✅ Deploy realizado
2. ✅ Variáveis configuradas
3. ✅ Credenciais n8n criadas
4. 🔄 Criar workflows via MCP
5. 🔄 Testar fluxos completos
6. 🔄 Configurar webhooks externos

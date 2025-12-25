# Google Sheets Setup Guide

Este guia explica como configurar a integração com Google Sheets para rastreamento operacional de pagamentos.

## Visão Geral

O sistema registra automaticamente todos os pagamentos PIX em uma planilha Google Sheets para:
- Controle operacional em tempo real
- Backup e auditoria de transações
- Relatórios e análises sem acessar o banco de dados
- Visibilidade para equipe não-técnica

## Fluxo de Dados

```
PIX Criado → Adiciona linha na planilha (status: pending)
     ↓
Webhook MP → Atualiza status e data_pagamento (status: approved)
```

## 1. Criar Projeto no Google Cloud

### 1.1. Acesse o Console

1. Vá para: https://console.cloud.google.com/
2. Faça login com sua conta Google
3. Clique em **Select a project** → **New Project**

### 1.2. Configure o Projeto

- **Project name**: `pix-whatsapp-automation` (ou outro nome)
- **Location**: Deixe como está
- Clique em **Create**

## 2. Habilitar Google Sheets API

### 2.1. Ativar API

1. No menu lateral, vá em **APIs & Services** → **Library**
2. Pesquise por "Google Sheets API"
3. Clique em **Google Sheets API**
4. Clique em **Enable**

## 3. Criar Service Account

### 3.1. Criar Credenciais

1. Vá em **APIs & Services** → **Credentials**
2. Clique em **Create Credentials** → **Service Account**
3. Preencha:
   - **Service account name**: `sheets-automation`
   - **Service account ID**: `sheets-automation` (gerado automaticamente)
4. Clique em **Create and Continue**

### 3.2. Permissões (Opcional)

- Você pode pular esta etapa clicando em **Continue**
- Não é necessário dar permissões de projeto para este caso

### 3.3. Criar Chave JSON

1. Na lista de Service Accounts, clique no email do service account criado
2. Vá na aba **Keys**
3. Clique em **Add Key** → **Create new key**
4. Escolha **JSON**
5. Clique em **Create**
6. O arquivo JSON será baixado automaticamente

### 3.4. Salvar Credenciais

```bash
# Mova o arquivo baixado para o projeto
mv ~/Downloads/pix-whatsapp-automation-*.json /path/to/project/credentials/google_sheets_credentials.json
```

## 4. Criar Google Sheets

### 4.1. Criar Planilha

1. Acesse: https://sheets.google.com/
2. Clique em **Blank** para criar nova planilha
3. Nomeie a planilha: **PIX Payments Tracker** (ou outro nome)
4. Copie o **Spreadsheet ID** da URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```

### 4.2. Compartilhar com Service Account

**IMPORTANTE**: Este passo é essencial!

1. Clique em **Share** (no canto superior direito)
2. Cole o email do service account:
   - Você encontra no arquivo JSON baixado: campo `client_email`
   - Exemplo: `sheets-automation@pix-whatsapp-automation.iam.gserviceaccount.com`
3. Escolha permissão: **Editor**
4. **Desmarque** "Notify people"
5. Clique em **Share**

## 5. Configurar Variáveis de Ambiente

### 5.1. Editar .env

```bash
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/google_sheets_credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=seu_spreadsheet_id_aqui
GOOGLE_SHEETS_SHEET_NAME=Sheet1
```

### 5.2. Verificar Credenciais

```bash
# Verifique se o arquivo existe
ls -la credentials/google_sheets_credentials.json

# Deve mostrar algo como:
# -rw-r--r-- 1 user user 2345 Dec 25 10:00 credentials/google_sheets_credentials.json
```

## 6. Inicializar Planilha

### 6.1. Executar Script de Setup

```bash
# Com Docker
docker-compose exec app python scripts/setup_sheets.py

# Ou localmente (se tiver Python)
python scripts/setup_sheets.py
```

### 6.2. Resultado Esperado

```
🚀 Initializing Google Sheets...
✅ Credentials loaded successfully

📊 Spreadsheet ID: 1234567890abcdef
📋 Sheet name: Sheet1

✅ Headers created successfully
✅ Formatting applied successfully

============================================================
✨ Google Sheets setup completed!
============================================================

📊 Your spreadsheet is ready at:
   https://docs.google.com/spreadsheets/d/1234567890abcdef

📋 Columns configured:
   A. request_id
   B. nome
   C. telefone
   D. condominio
   E. bloco
   F. apartamento
   G. mes
   H. valor
   I. status
   J. data_criacao
   K. data_pagamento
   L. mp_payment_id

✅ Next steps:
   1. Verify the spreadsheet is accessible
   2. Test PIX creation to see data flowing in
   3. Monitor payment updates via webhooks
```

## 7. Estrutura da Planilha

### 7.1. Colunas

| Coluna | Nome | Tipo | Descrição |
|--------|------|------|-----------|
| A | request_id | String | ID único da requisição |
| B | nome | String | Nome do cliente |
| C | telefone | String | Telefone (ex: 5511988887777) |
| D | condominio | String | Nome do condomínio |
| E | bloco | String | Bloco/torre |
| F | apartamento | String | Número do apartamento |
| G | mes | String | Mês de referência (YYYY-MM) |
| H | valor | Number | Valor do pagamento |
| I | status | String | pending, approved, cancelled, rejected |
| J | data_criacao | DateTime | Data de criação do PIX |
| K | data_pagamento | DateTime | Data de confirmação (quando aprovado) |
| L | mp_payment_id | String | ID do pagamento no Mercado Pago |

### 7.2. Formatação

- **Linha 1**: Cabeçalhos (negrito, fundo cinza)
- **Linha 1**: Congelada (sempre visível ao rolar)
- **Colunas**: Larguras otimizadas para cada tipo de dado

## 8. Testar Integração

### 8.1. Criar PIX de Teste

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

### 8.2. Verificar Planilha

1. Abra a planilha no Google Sheets
2. Deve aparecer uma nova linha com:
   - Nome: João Silva
   - Telefone: 5511988887777
   - Status: pending
   - Data de criação: timestamp atual
   - Data de pagamento: (vazia)

### 8.3. Simular Webhook de Pagamento

```bash
# Substitua 123456789 pelo mp_payment_id real
curl -X POST http://localhost:8000/webhooks/mercadopago/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "payment.updated",
    "type": "payment",
    "data": {"id": "123456789"}
  }'
```

### 8.4. Verificar Atualização

1. Recarregue a planilha
2. A linha deve estar atualizada:
   - Status: approved
   - Data de pagamento: timestamp da aprovação

## 9. Monitoramento

### 9.1. Logs do Sistema

```bash
# Ver logs de Google Sheets
docker-compose logs -f app | grep sheets

# Exemplos de logs:
# appending_row_to_sheets
# row_appended_to_sheets
# updating_row_in_sheets
# row_updated_in_sheets
```

### 9.2. Métricas Úteis

Na planilha você pode:

```
# Total de pagamentos
=COUNTA(A:A) - 1

# Total de pagamentos aprovados
=COUNTIF(I:I, "approved")

# Total de pagamentos pendentes
=COUNTIF(I:I, "pending")

# Valor total arrecadado
=SUMIF(I:I, "approved", H:H)

# Ticket médio
=AVERAGE(H:H)
```

## 10. Troubleshooting

### Erro: "Credentials file not found"

```bash
# Verifique se o arquivo existe
ls -la credentials/google_sheets_credentials.json

# Verifique o caminho no .env
cat .env | grep GOOGLE_SHEETS_CREDENTIALS_FILE
```

**Solução**: Certifique-se de que o arquivo JSON está no caminho correto.

### Erro: "The caller does not have permission"

```
googleapiclient.errors.HttpError: <HttpError 403 when requesting...
```

**Causa**: Service account não tem acesso à planilha.

**Solução**:
1. Copie o email do service account (campo `client_email` no JSON)
2. Compartilhe a planilha com esse email (permissão: Editor)
3. Tente novamente

### Erro: "Spreadsheet not found"

```
googleapiclient.errors.HttpError: <HttpError 404 when requesting...
```

**Causa**: Spreadsheet ID incorreto ou não existe.

**Solução**:
1. Verifique o ID no .env
2. Confirme que o ID está correto na URL da planilha
3. Verifique se a planilha não foi deletada

### Planilha não atualiza

**Possíveis causas**:
1. Erro silencioso (não quebra o fluxo principal)
2. Credenciais expiradas
3. Service account sem permissão

**Solução**:
```bash
# Verifique os logs
docker-compose logs -f app | grep "sheets_error\|failed_to_register_in_sheets\|failed_to_update_sheets"

# Teste manualmente
docker-compose exec app python scripts/setup_sheets.py
```

## 11. Autenticação OAuth (Alternativa)

Se preferir usar OAuth em vez de Service Account:

### 11.1. Criar Credenciais OAuth

1. No Google Cloud Console: **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Nome: `pix-automation-oauth`
5. Baixe o JSON

### 11.2. Configurar

```bash
# Salve o arquivo
mv ~/Downloads/client_secret_*.json credentials/google_sheets_credentials.json
```

### 11.3. Primeiro Uso

Na primeira vez, um navegador abrirá para autorizar:
1. Escolha sua conta Google
2. Clique em **Allow**
3. Um arquivo `token.json` será criado automaticamente

**Nota**: OAuth é mais indicado para desenvolvimento. Em produção, use Service Account.

## 12. Segurança

### 12.1. Proteger Credenciais

```bash
# Adicione ao .gitignore
echo "credentials/*.json" >> .gitignore
echo "token.json" >> .gitignore

# Nunca commite credenciais
git status  # Verifique que não aparecem arquivos de credenciais
```

### 12.2. Rotação de Chaves

Periodicamente, gere novas chaves:
1. No Google Cloud Console, vá em Service Accounts
2. Desabilite a chave antiga
3. Crie nova chave
4. Atualize o arquivo JSON
5. Reinicie a aplicação

### 12.3. Princípio do Menor Privilégio

- Service account tem acesso **apenas** às planilhas compartilhadas
- Não dê permissões extras no Google Cloud Project
- Use credenciais diferentes para dev/staging/prod

## 13. Produção

### 13.1. Checklist de Deploy

- [ ] Service Account criado com email dedicado
- [ ] Credenciais em variáveis de ambiente seguras (não em arquivo)
- [ ] Planilha compartilhada apenas com service account
- [ ] Logs de erro configurados para alertas
- [ ] Backup automático da planilha (Google Sheets faz isso automaticamente)
- [ ] Monitoramento de quota da API (Google Sheets API tem limites)

### 13.2. Limites da API

Google Sheets API tem rate limits:
- **100 requests/100 seconds/user**
- **500 requests/100 seconds/project**

Para alto volume:
- Considere batching de updates
- Use Redis para cache
- Implemente retry com exponential backoff

### 13.3. Escalabilidade

Para milhares de pagamentos por dia:
- Considere usar Google BigQuery em vez de Sheets
- Ou mantenha Sheets apenas para resumos/dashboards
- Use banco de dados como source of truth

## 14. Referências

- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [Service Account Authentication](https://developers.google.com/identity/protocols/oauth2/service-account)
- [Python Quickstart](https://developers.google.com/sheets/api/quickstart/python)
- [API Limits](https://developers.google.com/sheets/api/limits)

## 15. Suporte

Dúvidas ou problemas:
1. Verifique os logs: `docker-compose logs -f app | grep sheets`
2. Teste o script de setup: `python scripts/setup_sheets.py`
3. Confira as credenciais e permissões
4. Consulte a documentação oficial do Google

---

**Próximo passo**: Execute `python scripts/setup_sheets.py` para inicializar sua planilha!

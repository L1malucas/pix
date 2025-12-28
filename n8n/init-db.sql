-- Inicialização do banco de dados PostgreSQL para n8n workflows
-- Este script deve ser executado após o deploy no Render

-- Tabela de clientes
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    condo VARCHAR(255),
    block VARCHAR(50),
    apartment VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);

-- Tabela de pagamentos
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    month_ref VARCHAR(7) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    mp_payment_id VARCHAR(100),
    external_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_request_id ON payments(request_id);
CREATE INDEX IF NOT EXISTS idx_payments_mp_payment_id ON payments(mp_payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_client_id ON payments(client_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_month_ref ON payments(month_ref);

-- Tabela de estados de conversação (para o bot WhatsApp)
CREATE TABLE IF NOT EXISTS conversation_states (
    phone VARCHAR(20) PRIMARY KEY,
    step VARCHAR(50) NOT NULL,
    data JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_states_step ON conversation_states(step);

-- Tabela de webhooks processados (idempotência)
CREATE TABLE IF NOT EXISTS processed_webhooks (
    webhook_key VARCHAR(255) PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Limpar webhooks antigos (mais de 7 dias)
CREATE INDEX IF NOT EXISTS idx_processed_webhooks_date ON processed_webhooks(processed_at);

-- Function para limpar webhooks antigos (executar periodicamente)
CREATE OR REPLACE FUNCTION clean_old_webhooks()
RETURNS void AS $$
BEGIN
    DELETE FROM processed_webhooks
    WHERE processed_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar updated_at em conversation_states
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
    BEFORE UPDATE ON conversation_states
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- View para relatório de pagamentos
CREATE OR REPLACE VIEW payments_report AS
SELECT
    p.id,
    p.request_id,
    c.name,
    c.phone,
    c.condo,
    c.block,
    c.apartment,
    p.month_ref,
    p.amount,
    p.status,
    p.mp_payment_id,
    p.created_at,
    p.paid_at
FROM payments p
INNER JOIN clients c ON p.client_id = c.id
ORDER BY p.created_at DESC;

-- View para monitorar conversações ativas
CREATE OR REPLACE VIEW active_conversations AS
SELECT
    phone,
    step,
    data,
    updated_at,
    NOW() - updated_at as idle_time
FROM conversation_states
WHERE updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;

-- Comentários nas tabelas
COMMENT ON TABLE clients IS 'Cadastro de clientes do sistema';
COMMENT ON TABLE payments IS 'Registro de pagamentos PIX';
COMMENT ON TABLE conversation_states IS 'Estados das conversações ativas no WhatsApp';
COMMENT ON TABLE processed_webhooks IS 'Registro de webhooks já processados (idempotência)';

COMMENT ON COLUMN payments.request_id IS 'ID único da requisição (formato: req_YYYY_MM_DD_hash)';
COMMENT ON COLUMN payments.external_reference IS 'Referência externa do Mercado Pago (formato: PIX|YYYY-MM|VALOR|TELEFONE|APARTAMENTO)';
COMMENT ON COLUMN conversation_states.data IS 'Dados coletados durante a conversação (JSON)';
COMMENT ON COLUMN conversation_states.step IS 'Passo atual na conversação (START, COLLECT_NAME, etc)';

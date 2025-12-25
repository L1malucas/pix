#!/bin/bash

# Test script for WhatsApp conversation flow

API_URL="http://localhost:8000/webhooks/whatsapp"
PHONE="5511988887777"

echo "🤖 Testing WhatsApp Conversation Flow"
echo "======================================"
echo ""

# Function to send message
send_message() {
    local message="$1"
    local msg_id="wamid_$(date +%s)"

    echo "📤 User: $message"

    curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"object\": \"whatsapp_business_account\",
            \"entry\": [{
                \"id\": \"123456789\",
                \"changes\": [{
                    \"value\": {
                        \"messaging_product\": \"whatsapp\",
                        \"metadata\": {
                            \"display_phone_number\": \"5511999999999\",
                            \"phone_number_id\": \"123456789\"
                        },
                        \"contacts\": [{
                            \"profile\": {\"name\": \"Test User\"},
                            \"wa_id\": \"$PHONE\"
                        }],
                        \"messages\": [{
                            \"from\": \"$PHONE\",
                            \"id\": \"$msg_id\",
                            \"timestamp\": \"$(date +%s)\",
                            \"type\": \"text\",
                            \"text\": {\"body\": \"$message\"}
                        }]
                    },
                    \"field\": \"messages\"
                }]
            }]
        }" | python3 -m json.tool

    echo ""
    echo "---"
    echo ""
    sleep 1
}

# Test conversation flow
echo "Step 1: Start conversation"
send_message "Olá"

echo "Step 2: Provide name"
send_message "João Silva"

echo "Step 3: Provide condominium"
send_message "Residencial Jardim"

echo "Step 4: Provide block"
send_message "A"

echo "Step 5: Provide apartment"
send_message "101"

echo "Step 6: Select plan"
send_message "1"

echo ""
echo "✅ Conversation flow test completed!"
echo ""
echo "Note: Check the logs for bot responses (messages would be sent via WhatsApp API)"
echo "In production, messages will be sent to the actual WhatsApp number."

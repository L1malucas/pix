"""Conversation handler for WhatsApp bot flow."""
from typing import Optional

from src.core.logging import get_logger
from src.schemas.whatsapp import ConversationState
from src.services.message_parser import MessageParser
from src.services.whatsapp import whatsapp_service

logger = get_logger(__name__)

# In-memory storage for conversation states (replace with Redis/DB in production)
conversation_states: dict[str, ConversationState] = {}


class ConversationHandler:
    """Handle conversation flow for WhatsApp bot."""

    # Conversation steps
    STEP_START = "START"
    STEP_COLLECT_NAME = "COLLECT_NAME"
    STEP_COLLECT_CONDO = "COLLECT_CONDO"
    STEP_COLLECT_BLOCK = "COLLECT_BLOCK"
    STEP_COLLECT_APARTMENT = "COLLECT_APARTMENT"
    STEP_SELECT_PLAN = "SELECT_PLAN"
    STEP_COMPLETED = "COMPLETED"

    def __init__(self) -> None:
        """Initialize conversation handler."""
        self.parser = MessageParser()

    def get_state(self, phone: str) -> ConversationState:
        """
        Get conversation state for a phone number.

        Args:
            phone: Phone number

        Returns:
            Conversation state
        """
        if phone not in conversation_states:
            conversation_states[phone] = ConversationState(phone=phone)
        return conversation_states[phone]

    def reset_state(self, phone: str) -> None:
        """
        Reset conversation state for a phone number.

        Args:
            phone: Phone number
        """
        if phone in conversation_states:
            del conversation_states[phone]

    async def handle_message(
        self,
        phone: str,
        message_text: str,
        message_id: str,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Handle incoming message and process conversation flow.

        Args:
            phone: Sender phone number
            message_text: Message text
            message_id: WhatsApp message ID
            request_id: Request ID for tracking

        Returns:
            Response data with next step and action
        """
        logger.info(
            "handling_conversation",
            request_id=request_id,
            phone=phone,
            message=message_text[:50],
        )

        # Get current state
        state = self.get_state(phone)

        # Mark message as read
        try:
            await whatsapp_service.mark_message_as_read(message_id, request_id)
        except Exception as e:
            logger.warning("failed_to_mark_read", error=str(e), request_id=request_id)

        # Process based on current step
        if state.step == self.STEP_START:
            return await self._handle_start(phone, message_text, state, request_id)

        elif state.step == self.STEP_COLLECT_NAME:
            return await self._handle_collect_name(phone, message_text, state, request_id)

        elif state.step == self.STEP_COLLECT_CONDO:
            return await self._handle_collect_condo(phone, message_text, state, request_id)

        elif state.step == self.STEP_COLLECT_BLOCK:
            return await self._handle_collect_block(phone, message_text, state, request_id)

        elif state.step == self.STEP_COLLECT_APARTMENT:
            return await self._handle_collect_apartment(phone, message_text, state, request_id)

        elif state.step == self.STEP_SELECT_PLAN:
            return await self._handle_select_plan(phone, message_text, state, request_id)

        else:
            # Unknown state, reset
            self.reset_state(phone)
            return await self._handle_start(phone, message_text, state, request_id)

    async def _handle_start(
        self,
        phone: str,
        message_text: str,
        state: ConversationState,
        request_id: Optional[str],
    ) -> dict:
        """Handle START step."""
        welcome_message = (
            "Olá! Bem-vindo ao sistema de pagamentos PIX via WhatsApp.\n\n"
            "Vou coletar algumas informações para gerar seu PIX de pagamento mensal.\n\n"
            "Para começar, qual é o seu nome completo?"
        )

        await whatsapp_service.send_text_message(phone, welcome_message, request_id)

        state.step = self.STEP_COLLECT_NAME
        return {"step": state.step, "action": "collect_name"}

    async def _handle_collect_name(
        self,
        phone: str,
        message_text: str,
        state: ConversationState,
        request_id: Optional[str],
    ) -> dict:
        """Handle COLLECT_NAME step."""
        if len(message_text) < 3:
            await whatsapp_service.send_text_message(
                phone,
                "Por favor, digite seu nome completo (mínimo 3 caracteres).",
                request_id,
            )
            return {"step": state.step, "action": "retry_name"}

        state.data["name"] = message_text
        state.step = self.STEP_COLLECT_CONDO

        await whatsapp_service.send_text_message(
            phone,
            f"Obrigado, {message_text}!\n\nAgora, qual é o nome do seu condomínio?",
            request_id,
        )

        return {"step": state.step, "action": "collect_condo"}

    async def _handle_collect_condo(
        self,
        phone: str,
        message_text: str,
        state: ConversationState,
        request_id: Optional[str],
    ) -> dict:
        """Handle COLLECT_CONDO step."""
        state.data["condo"] = message_text
        state.step = self.STEP_COLLECT_BLOCK

        await whatsapp_service.send_text_message(
            phone,
            "Qual é o bloco/torre do seu apartamento?",
            request_id,
        )

        return {"step": state.step, "action": "collect_block"}

    async def _handle_collect_block(
        self,
        phone: str,
        message_text: str,
        state: ConversationState,
        request_id: Optional[str],
    ) -> dict:
        """Handle COLLECT_BLOCK step."""
        state.data["block"] = message_text
        state.step = self.STEP_COLLECT_APARTMENT

        await whatsapp_service.send_text_message(
            phone,
            "Qual é o número do seu apartamento?",
            request_id,
        )

        return {"step": state.step, "action": "collect_apartment"}

    async def _handle_collect_apartment(
        self,
        phone: str,
        message_text: str,
        state: ConversationState,
        request_id: Optional[str],
    ) -> dict:
        """Handle COLLECT_APARTMENT step."""
        state.data["apartment"] = message_text
        state.step = self.STEP_SELECT_PLAN

        plan_message = (
            "Perfeito! Agora selecione o plano desejado:\n\n"
            "1️⃣ Individual - R$ 70,00\n"
            "2️⃣ 2 pessoas - R$ 90,00\n"
            "3️⃣ 4 pessoas - R$ 100,00\n\n"
            "Digite o número do plano (1, 2 ou 3):"
        )

        await whatsapp_service.send_text_message(phone, plan_message, request_id)

        return {"step": state.step, "action": "select_plan"}

    async def _handle_select_plan(
        self,
        phone: str,
        message_text: str,
        state: ConversationState,
        request_id: Optional[str],
    ) -> dict:
        """Handle SELECT_PLAN step."""
        if not self.parser.is_valid_plan_option(message_text):
            await whatsapp_service.send_text_message(
                phone,
                "Opção inválida. Por favor, digite 1, 2 ou 3 para selecionar o plano.",
                request_id,
            )
            return {"step": state.step, "action": "retry_plan"}

        plan_value = self.parser.get_plan_value(message_text)
        state.data["plan"] = message_text
        state.data["amount"] = plan_value
        state.step = self.STEP_COMPLETED

        # Return collected data for PIX generation
        return {
            "step": state.step,
            "action": "generate_pix",
            "data": {
                "phone": phone,
                "name": state.data["name"],
                "condo": state.data["condo"],
                "block": state.data["block"],
                "apartment": state.data["apartment"],
                "plan": state.data["plan"],
                "amount": plan_value,
            },
        }


# Global instance
conversation_handler = ConversationHandler()

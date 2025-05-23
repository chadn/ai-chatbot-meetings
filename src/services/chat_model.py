from typing import Any
from uuid import UUID
import pprint
import traceback
import logging
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from .tool_manager import ToolManager   
from .chat_history import ChatHistoryManager
from .calcom_service import CalComService
from config import AppConfig
from datetime import datetime

# Set up logger for this module
logger = logging.getLogger(__name__)

class ChatModelService:
    def __init__(self, config: AppConfig, chat_history: ChatHistoryManager) -> None:
        """
        Initialize ChatModelService with configuration.
        
        Args:
            config: Application configuration
            chat_history: Chat history manager instance
        """
        self.config = config
        self.chat_history = chat_history
        
        logger.info(f"Initializing ChatModelService with model: {config.openai.model_name}")
        
        try:
            # Initialize CalCom service
            calcom_service = CalComService(config.calcom)
            
            # Initialize tool manager with CalCom service
            self.tool_manager = ToolManager(calcom_service)
            
            # Create chat models
            self.chat_llm_no_tools = self.get_model()
            logger.debug(f"Chat LLM before bind_tools: {self.chat_llm_no_tools}")
            
            self.chat_llm = self.chat_llm_no_tools.bind_tools(self.tool_manager.working_tools)
            logger.info(f"Successfully bound tools: {len(self.tool_manager.working_tools)} tools")
            
        except Exception as e:
            logger.error(f"ChatModelService initialization failed: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            raise e

    def get_model(self) -> ChatOpenAI:
        """Get the appropriate model based on configuration."""
        model_name = self.config.openai.model_name

        if not hasattr(self, "_model_cache"):
            self._model_cache = {}

        if model_name not in self._model_cache:
            self._model_cache[model_name] = ChatOpenAI(
                model=model_name,
                openai_api_key=self.config.openai.api_key,
                max_tokens=self.config.openai.max_tokens,
                temperature=self.config.openai.temperature,
                callbacks=[MyCustomHandler()],
            )
        return self._model_cache[model_name]


    def get_system_message(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d %A")
        system_prompt = f"""
        Today is {today} and the conversation is in the timezone {self.config.calcom.timezone}.
        
        You are a helpful assistant capable of using external tool functions autonomously. 
        Tool responses will appear in this conversation as messages from "tool". 
        Use these responses to help the user as naturally and efficiently as possible.

        You have access to calendar management tools via the Cal.com API.
        
        Tasks and Instructions:
        
        1. Booking a Meeting
        
        When the user requests to book a meeting:
        
        - Ask what day(s) they prefer if they haven't already provided them.
        - Use the check_availability tool to retrieve available times.
        - Present the user with options including:
          - Date of the meeting, confirmed in this format: <YYYY-MM-DD DAY>
          - Preferred times for each date, in 12 hour format: <HH:MM AM/PM>
        
        - Ask for the reason for the meeting.
        - Confirm the attendee's name and email.
          - Use default values of:
            - Name: Chad Dev
            - Email: dev@chadnorwood.com
        
        - Once all details are collected, use the book_meeting tool to schedule the meeting.
        
        2. Viewing Scheduled Events
        
        If the user wants to see their scheduled events:
        
        - Ask for their email address.
        - Use the get_scheduled_bookings tool to retrieve the events.
        
        3. Checking Availability
        
        If the user asks for availability on a specific date:
        
        - Use the check_availability tool with the provided date.
        - Present available time slots for that day.
        
        Conversational Guidelines:
        
        - Keep the conversation natural and friendly.
        - Ask for one piece of information at a time.
        - Store and reuse user-provided information during the session.
        - Respond clearly and helpfully using the data returned by tools.
        """
        return ' '.join(system_prompt.split())

    def set_chat_history(self, chat_history: ChatHistoryManager, skip_system_message: bool = False) -> None:
        self.chat_history = chat_history
        if not skip_system_message:
            # should we check to see if a system message already exists? No, trust the boolean.
            self.chat_history.add_system_message(self.get_system_message())

    def generate_response_langchain(self, content: str = None) -> str:
        """Generate a chat response using the Langchain API.
        uses the chat_history and the chat_llm to generate a response.
        
        Updates the chat_history with the response, maybe multiple times.

        Args:
            content: Content of the message to generate a response for. If None, the last message in the chat_history is used.
        Returns:
            str: Generated response text
        """
        if content:
            self.chat_history.add_human_message(content)

        # this is how many turns we allow the AI to call tools.  3 for now while debugging, increase to 5 or 10 later.
        max_tool_turns = 3
        remaining_tool_turns = max_tool_turns
        while remaining_tool_turns > 0:
            remaining_tool_turns -= 1
            # response_ai_msg is a AI Message object, the response from AI to human.
            logger.debug(f"\nChat LLM remaining_tool_turns={remaining_tool_turns} chat_history.messages length={len(self.chat_history.messages)} ")
            response_ai_msg = self.chat_llm.invoke(self.chat_history.messages)
            tool_responses = []
            try:
                logger.debug("\nChat LLM response_ai_msg: ")
                pprint.pp(response_ai_msg)
                tool_responses = self.tool_manager.execute_tool_calls(response_ai_msg)
            except Exception as e:
                logger.error(f"\nExecute tool calls failed.\n{e}\n\n")
                raise e
            if (tool_responses and len(tool_responses) > 0):
                # add the AI message with tool_calls to the chat history before adding the response tool messages
                self.chat_history.add_ai_message(response_ai_msg)
                for toolmsg in tool_responses:
                    self.chat_history.add_tool_message(toolmsg)
            else:
                #max_tool_turns = 0
                break

        self.chat_history.add_ai_message(response_ai_msg)

        try:
            logger.debug(f"Chat LLM {len(self.chat_history.messages)} chat_history.messages: ")
            pprint.pp(self.chat_history.messages)
            print("\n", flush=True)
        except Exception:
            logger.debug("Chat LLM printing chat_history.messages failed")

        return response_ai_msg

# available callback functions listed here:
# https://python.langchain.com/api_reference/core/callbacks/langchain_core.callbacks.base.BaseCallbackHandler.html
# #langchain-core-callbacks-base-basecallbackhandler
class MyCustomHandler(BaseCallbackHandler):

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        logger.debug(f"MyCustomHandler: on_llm_new_token({token})")

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], *, run_id: UUID, 
                     parent_run_id: UUID | None = None, tags: list[str] | None = None, 
                     metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        # ATTENTION: This method is called for non-chat models (regular LLMs). 
        # If you're implementing a handler for a chat model, you should use on_chat_model_start instead.
        logger.debug("MyCustomHandler: on_llm_start")

    def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[BaseMessage]], *, run_id: UUID, 
                           parent_run_id: UUID | None = None, tags: list[str] | None = None, 
                           metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        # ATTENTION: This method is called for chat models. 
        # If you're implementing a handler for a non-chat model, you should use on_llm_start instead.
        logger.debug(f"MyCustomHandler: on_chat_model_start {len(messages)}.{len(messages[0])} messages: {messages}")



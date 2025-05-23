from datetime import datetime
from typing import List
import json
import logging
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

# Set up logger for this module
logger = logging.getLogger(__name__)

class ChatHistoryManager(StreamlitChatMessageHistory):
    def __init__(self) -> None:
        super().__init__(key="langchain_messages")
        logger.info("ChatHistoryManager initialization complete.")
    
    def add_human_message(self, content: str) -> None:
        timestamp = datetime.now().isoformat()
        message = HumanMessage(content=content, additional_kwargs={"created_at": timestamp})
        self.add_message(message)

    def add_ai_message(self, content: str | AIMessage) -> None:
        if isinstance(content, AIMessage):
            # If it's already an AIMessage, add timestamp if not present
            if not content.additional_kwargs.get("created_at"):
                content.additional_kwargs["created_at"] = datetime.now().isoformat()
            self.add_message(content)
        elif isinstance(content, str):
            timestamp = datetime.now().isoformat()
            message = AIMessage(content=content, additional_kwargs={"created_at": timestamp})
            self.add_message(message)
        else:
            raise ValueError(f"Invalid content type: {type(content)}")

    def add_tool_message(self, toolmsg: ToolMessage) -> None:
        # Add timestamp if not present
        if not toolmsg.additional_kwargs.get("created_at"):
            toolmsg.additional_kwargs["created_at"] = datetime.now().isoformat()
        self.add_message(toolmsg)

    def add_system_message(self, content: str) -> None:
        timestamp = datetime.now().isoformat()
        message = SystemMessage(content=content, additional_kwargs={"created_at": timestamp})
        self.add_message(message)

    def get_just_ai_human_message(self) -> List[BaseMessage]:
        """
        Get all  AI or Human messages from the chat history.
        Skip system, tool, and any messages without content.

        Returns:
            List[BaseMessage]: A list of BaseMessage objects
        """
        messages = []
        for msg in self.messages:
            if msg.type in ["ai", "human"]:
                if msg.content:
                    messages.append(BaseMessage(content=msg.content, type=msg.type))
        logger.info(f"get_just_ai_human_message() returning {len(messages)} of {len(self.messages)} messages")
        return messages

    
    def export_json(self) -> str:
        """Export chat history as JSON string."""
        try:
            # Convert LangChain messages to JSON-serializable format
            serializable_messages = []
            for msg in self.messages:
                message_dict = {
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": msg.additional_kwargs.get("created_at", datetime.now().isoformat())  # Add timestamp for reference
                }
                
                # Add additional fields if they exist
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    message_dict["tool_calls"] = msg.tool_calls
                if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                    message_dict["tool_call_id"] = msg.tool_call_id
                    
                serializable_messages.append(message_dict)
                
            return json.dumps(serializable_messages, indent=2)
        except Exception as e:
            logger.error(f"Error exporting chat history: {e}")
            return '[]'  # return empty list if error
        
    def import_json(self, json_str: str) -> None:
        """Import chat history from JSON string.
        
        Args:
            json_str: JSON string containing chat messages
            
        Raises:
            ValueError: If JSON format is invalid
        """
        try:
            messages = json.loads(json_str)
            if not isinstance(messages, list):
                raise ValueError("JSON must contain a list of messages")
                
            self.clear()
            for msg_data in messages:
                if not isinstance(msg_data, dict) or not all(key in msg_data for key in ['type', 'content']):
                    raise ValueError("Each message must be a dictionary with at least 'type' and 'content' keys")
                
                # Create appropriate message type based on the 'type' field
                msg_type = msg_data["type"]
                content = msg_data["content"]
                
                # Extract timestamp and prepare additional_kwargs
                timestamp = msg_data.get("timestamp")
                additional_kwargs = {"created_at": timestamp} if timestamp else {}
                
                if msg_type == "system":
                    message = SystemMessage(content=content, additional_kwargs=additional_kwargs)
                elif msg_type == "human":
                    message = HumanMessage(content=content, additional_kwargs=additional_kwargs)
                elif msg_type == "ai":
                    message = AIMessage(content=content, additional_kwargs=additional_kwargs)
                    # Restore tool_calls if they exist
                    if "tool_calls" in msg_data and msg_data["tool_calls"]:
                        message.tool_calls = msg_data["tool_calls"]
                elif msg_type == "tool":
                    # ToolMessage requires tool_call_id
                    tool_call_id = msg_data.get("tool_call_id", "unknown")
                    message = ToolMessage(content=content, tool_call_id=tool_call_id, additional_kwargs=additional_kwargs)
                else:
                    # Fallback to BaseMessage for unknown types
                    message = BaseMessage(content=content, type=msg_type, additional_kwargs=additional_kwargs)
                
                self.add_message(message)
                
            logger.info(f"Successfully imported {len(messages)} messages from JSON")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error importing chat history: {e}")
            raise ValueError(f"Error importing chat history: {e}")

from typing import List, Callable
import logging
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from .calcom_service import CalComService

# Set up logger for this module
logger = logging.getLogger(__name__)

class ToolManager:
    def __init__(self, calcom_service: CalComService) -> None:
        """
        Initialize ToolManager with CalCom service.
        
        Args:
            calcom_service: CalComService instance
        """
        self.calcom_service = calcom_service
        
        # Create tools with the service instance
        self.working_tools = [
            self._create_check_availability_tool(),
            self._create_book_meeting_tool(),
            self._create_get_scheduled_bookings_tool(),
        ]
        self.tool_node = ToolNode(self.working_tools)
        logger.info("ToolManager initialization complete.")

    def _create_check_availability_tool(self) -> Callable:
        """Create the check availability tool with the CalCom service."""
        calcom_service = self.calcom_service
        
        @tool
        def check_meeting_availability(start_date: str, end_date: str = None) -> str:
            """
            Check available meeting slots for a specific date range.
            
            Args:
                start_date: Start date in YYYY-MM-DD format
                end_date: End date in YYYY-MM-DD format (optional, defaults to start_date if not provided)
                
            Returns:
                String describing available time slots with event type IDs
            """
            try:
                return calcom_service.get_formatted_availability(start_date, end_date)
            except Exception as e:
                logger.error(f"Error checking availability: {e}")
                return f"Error checking availability: {str(e)}"
        
        return check_meeting_availability

    def _create_book_meeting_tool(self) -> Callable:
        """Create the book meeting tool with the CalCom service."""
        calcom_service = self.calcom_service
        
        @tool
        def book_meeting(start_time: str, name: str, email: str, event_type_id: int, reason: str = "") -> str:
            """
            Book a meeting at the specified time.
            
            Args:
                start_time: Meeting start time in ISO format (YYYY-MM-DDTHH:MM:SS)
                name: Attendee's full name
                email: Attendee's email address
                event_type_id: ID from check_meeting_availability tool
                reason: Optional reason for meeting, notes field in cal.com
                
            Returns:
                Confirmation message with meeting details
            """
            try:
                return calcom_service.create_booking_with_confirmation(
                    start_time=start_time,
                    name=name,
                    email=email,
                    event_type_id=event_type_id,
                    reason=reason
                )
            except Exception as e:
                logger.error(f"Error booking meeting: {e}")
                return f"Error booking meeting: {str(e)}"
        
        return book_meeting

    def _create_get_scheduled_bookings_tool(self) -> Callable:
        """Create the get scheduled events tool with the CalCom service."""
        calcom_service = self.calcom_service
        
        @tool
        def get_scheduled_bookings(email: str) -> str:
            """
            Get a list of scheduled booking events for a user by email.
            
            Args:
                email: The email address of the user, used as attendeeEmail in the API call
                
            Returns:
                A formatted string with the scheduled events
            """
            try:
                return calcom_service.get_formatted_scheduled_bookings(email)
            except Exception as e:
                logger.error(f"Error retrieving scheduled events: {e}")
                return f"Error retrieving scheduled events: {str(e)}"
        
        return get_scheduled_bookings

    def execute_tool_calls(self, response_ai_msg: AIMessage) -> List[ToolMessage]:
        """Execute tool calls from AI message and return tool responses."""
        # https://langchain-ai.github.io/langgraph/how-tos/tool-calling/#using-with-chat-models
        tool_responses = self.tool_node.invoke({"messages": [response_ai_msg]})
        logger.debug("execute_tool_calls() ai_message.tool_calls, tool_responses: ")
        logger.debug(f"Tool calls: {response_ai_msg.tool_calls}")
        logger.debug(f"Tool responses: {tool_responses}")
        return tool_responses['messages'] if tool_responses and 'messages' in tool_responses else []


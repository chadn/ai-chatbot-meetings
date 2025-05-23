# Architecture

This document provides a high-level overview of the AI Chatbot Meetings application architecture, design patterns, and key architectural decisions.

## Overview

The AI Chatbot for Meetings application is designed using a modular, service-oriented architecture that promotes separation of concerns, testability, and maintainability. The application integrates Streamlit for the UI, LangChain and OpenAI for AI interactions, and Cal.com for calendar management.

## Core Design Patterns

### 1. Service Layer Pattern

**Why this pattern**: Separates business logic from presentation layer and provides clear API boundaries between different concerns.

The application is organized into distinct service layers:

```python
# Core services structure
src/services/
├── chat_model.py        # AI model interactions
├── chat_history.py      # Chat state management
├── calcom_service.py    # External API integration
└── tool_manager.py      # Tool calling orchestration
```

**Benefits over alternatives**:

-   **vs. Monolithic approach**: Each service has single responsibility, easier to test and maintain
-   **vs. Direct API calls**: Abstraction layer allows for easier mocking, error handling, and API changes
-   **vs. Static functions**: Services maintain state and can be dependency-injected

**Example**:

```python
# CalComService encapsulates all Cal.com API interactions
class CalComService:
    def __init__(self, config: CalComConfig) -> None:
        self.config = config
        self.headers = {"Authorization": f"Bearer {config.api_key}"}

    def check_availability(self, start_date: str, end_date: str) -> Dict[str, List[Dict[str, Any]]]:
        # Handles API versioning, error handling, response transformation
```

### 2. Dependency Injection Pattern

**Why this pattern**: Promotes loose coupling, improves testability, and makes the system more flexible.

Services are injected rather than instantiated directly:

```python
# ToolManager receives CalComService as dependency
class ToolManager:
    def __init__(self, calcom_service: CalComService) -> None:
        self.calcom_service = calcom_service
        self.working_tools = [
            self._create_check_availability_tool(),
            self._create_book_meeting_tool(),
            self._create_get_scheduled_bookings_tool(),
        ]

# ChatModelService orchestrates multiple services
class ChatModelService:
    def __init__(self, config: AppConfig, chat_history: ChatHistoryManager) -> None:
        calcom_service = CalComService(config.calcom)
        self.tool_manager = ToolManager(calcom_service)
```

**Benefits**:

-   Easy to mock dependencies for unit testing
-   Configuration changes don't require code changes
-   Services can be swapped without affecting dependents

### 3. Configuration Pattern with Dataclasses

**Why this pattern**: Type-safe configuration management with validation and environment variable integration.

```python
@dataclass
class CalComConfig:
    api_key: str
    base_url: str = DEFAULT_CALCOM_BASE_URL
    timezone: str = DEFAULT_TIMEZONE

    @classmethod
    def from_env(cls) -> "CalComConfig":
        api_key = os.getenv("CALCOM_API_KEY")
        if not api_key:
            raise ValueError("CALCOM_API_KEY environment variable is required")

        timezone = os.getenv("DEFAULT_TIMEZONE", DEFAULT_TIMEZONE)
        # Validate timezone
        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone}")

        return cls(api_key=api_key, timezone=timezone)
```

**Benefits over alternatives**:

-   **vs. Environment variables everywhere**: Centralized, validated configuration
-   **vs. Dictionary-based config**: Type safety and IDE support
-   **vs. Hard-coded values**: Environment-specific configuration without code changes

### 4. Tool Calling Pattern with Decorators

**Why this pattern**: LangChain's tool calling system via `@tool` provides a clean way to expose Python functions to the AI model.

**Thin Wrapper Implementation**: The ToolManager uses a thin wrapper pattern where tools act as minimal interfaces between LangChain and business logic:

```python
@tool
def check_meeting_availability(start_date: str, end_date: str = None) -> str:
    """
    Check available meeting slots for a specific date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (optional)

    Returns:
        String describing available time slots
    """
    try:
        return calcom_service.get_formatted_availability(start_date, end_date)
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return f"Error checking availability: {str(e)}"
```

**Business Logic in Service Layer**: All data processing, formatting, and domain logic is handled in CalComService:

```python
# CalComService handles all Cal.com-specific logic
def get_formatted_availability(self, start_date: str, end_date: str = None) -> str:
    """Return human-readable availability with proper timezone conversion."""
    availability = self.check_availability(start_date, end_date)
    # Complex formatting logic lives here, not in tools
    return self._format_availability_response(availability)
```

**Benefits**:

-   **Automatic schema generation**: LangChain generates tool schemas for the AI model
-   **Clean separation**: Tools handle LangChain interface, services handle business logic
-   **Better testability**: Business logic can be unit tested independently of tool framework
-   **Reduced duplication**: Centralized formatting and data processing logic

### 5. State Management with Session Persistence

**Why this pattern**: Streamlit's session state combined with JSON serialization provides reliable chat persistence.

The chat history system implements sophisticated state management:

```python
class ChatHistoryManager(StreamlitChatMessageHistory):
    def export_json(self) -> str:
        """Export chat history as JSON string."""
        serializable_messages = []
        for msg in self.messages:
            message_dict = {
                "type": msg.type,
                "content": msg.content,
                "timestamp": msg.additional_kwargs.get("created_at", datetime.now().isoformat())
            }

            # Preserve tool calls for AI messages
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id

            serializable_messages.append(message_dict)

        return json.dumps(serializable_messages, indent=2)
```

## Key Architectural Decisions

### 1. Streamlit for UI Framework

**Decision**: Use Streamlit instead of React/Vue.js or Flask/FastAPI

**Reasoning**:

-   Rapid prototyping for AI applications
-   Built-in session state management
-   Native support for chat interfaces
-   Python-native (no context switching between languages)

**Trade-offs**:

-   Less customizable than custom web frameworks
-   Limited to Python ecosystem
-   Single-user sessions (acceptable for demo/prototype)

### 2. LangChain Framework Integration

**Decision**: Use LangChain instead of direct OpenAI API calls

**Reasoning**:

-   Standardized tool calling interface
-   Built-in conversation memory management
-   Abstraction over different LLM providers
-   Rich ecosystem of integrations

**Implementation**:

```python
# Tool binding and execution
self.chat_llm = self.chat_llm_no_tools.bind_tools(self.tool_manager.working_tools)
response_ai_msg = self.chat_llm.invoke(self.chat_history.messages)
tool_responses = self.tool_manager.execute_tool_calls(response_ai_msg)
```

### 3. Error Handling Strategy

**Decision**: Comprehensive error handling with graceful degradation

**Pattern**:

```python
try:
    response.raise_for_status()
    data = response.json()
    if "status" in data and data["status"] != "success":
        raise ValueError(f"API error: {data['status']}")
    return process_response(data)
except requests.HTTPError as e:
    error_message = f"HTTP error: {e}"
    try:
        error_json = response.json()
        if "message" in error_json:
            error_message = f"{error_message}, API error: {error_json['message']}"
    except Exception:
        pass
    raise requests.HTTPError(error_message, response=response)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise ValueError(f"Operation failed: {str(e)}")
```

**Benefits**:

-   Detailed error messages for debugging
-   Graceful fallbacks for users
-   Comprehensive logging for monitoring

## JSON Chat Message Format

### Schema Design

The chat message JSON format is designed for both human readability and programmatic processing:

```json
[
    {
        "type": "system",
        "content": "You are a helpful assistant...",
        "timestamp": "2025-01-15T10:30:00.123456"
    },
    {
        "type": "human",
        "content": "Book a meeting for tomorrow",
        "timestamp": "2025-01-15T10:30:05.789012"
    },
    {
        "type": "ai",
        "content": "",
        "timestamp": "2025-01-15T10:30:06.123456",
        "tool_calls": [
            {
                "name": "check_meeting_availability",
                "args": { "start_date": "2025-01-16" },
                "id": "call_abc123",
                "type": "tool_call"
            }
        ]
    },
    {
        "type": "tool",
        "content": "Available slots: 9:00 AM, 10:00 AM, 2:00 PM",
        "timestamp": "2025-01-15T10:30:07.456789",
        "tool_call_id": "call_abc123"
    },
    {
        "type": "ai",
        "content": "I found several available time slots for tomorrow...",
        "timestamp": "2025-01-15T10:30:08.789012"
    }
]
```

### Import/Export Implementation

**Export Process**:

1. Iterate through LangChain message objects
2. Extract core fields (type, content, timestamp)
3. Preserve tool-calling metadata
4. Serialize to human-readable JSON

**Import Process**:

1. Validate JSON schema
2. Reconstruct appropriate LangChain message types
3. Restore tool call relationships
4. Maintain conversation flow

**Benefits of this approach**:

-   **Portability**: Messages can be shared between sessions/users
-   **Debugging**: Human-readable format for troubleshooting
-   **Analytics**: Easy to analyze conversation patterns
-   **Backup**: Reliable persistence mechanism

### Message Type Handling

The system handles different message types with specific logic:

```python
def import_json(self, json_str: str) -> None:
    for msg_data in messages:
        msg_type = msg_data["type"]
        content = msg_data["content"]
        timestamp = msg_data.get("timestamp")

        if msg_type == "system":
            message = SystemMessage(content=content, additional_kwargs={"created_at": timestamp})
        elif msg_type == "ai":
            message = AIMessage(content=content, additional_kwargs={"created_at": timestamp})
            # Restore tool_calls for AI messages
            if "tool_calls" in msg_data:
                message.tool_calls = msg_data["tool_calls"]
        elif msg_type == "tool":
            # Tool messages require tool_call_id for proper linking
            tool_call_id = msg_data.get("tool_call_id", "unknown")
            message = ToolMessage(content=content, tool_call_id=tool_call_id)

        self.add_message(message)
```

## Performance Considerations

### 1. Model Caching

```python
def get_model(self) -> ChatOpenAI:
    if not hasattr(self, "_model_cache"):
        self._model_cache = {}

    if model_name not in self._model_cache:
        self._model_cache[model_name] = ChatOpenAI(...)
    return self._model_cache[model_name]
```

### 2. Tool Turn Limiting

```python
max_tool_turns = 3  # Prevent infinite tool calling loops
remaining_tool_turns = max_tool_turns
while remaining_tool_turns > 0 and tool_responses:
    # Process tool calls
```

### 3. Efficient Message Filtering

```python
def get_just_ai_human_message(self) -> List[BaseMessage]:
    """Filter messages for UI display, excluding system/tool messages"""
    return [msg for msg in self.messages
            if msg.type in ["ai", "human"] and msg.content]
```

## Testing Strategy

The architecture supports comprehensive testing through:

1. **Service Isolation**: Each service can be unit tested independently
2. **Dependency Injection**: Easy mocking of external dependencies
3. **Configuration Management**: Test-specific configurations
4. **Error Handling**: Explicit error cases can be tested

Example test structure:

```python
def test_chat_model_with_mock_dependencies():
    mock_calcom = Mock(spec=CalComService)
    mock_history = Mock(spec=ChatHistoryManager)

    service = ChatModelService(test_config, mock_history)
    # Test service behavior with controlled inputs
```

This architecture balances simplicity with extensibility, making it easy to add new features while maintaining code quality and testability.

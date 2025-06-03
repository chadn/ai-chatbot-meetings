"""
Main Streamlit application for the chatbot interface.

Config precedence: user input > environment variable > code default.
All session state keys are defined in SESSION_STATE_KEYS for maintainability.
"""
import streamlit as st
from datetime import datetime
from io import StringIO
from typing import Tuple
from dotenv import load_dotenv
import traceback
from services.chat_model import ChatModelService
from services.chat_history import ChatHistoryManager
from langchain_core.messages import BaseMessage
from streamlit_js_eval import streamlit_js_eval
from utils.logger import setup_logger
from config import AppConfig

# Set up logger for this module
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

# Set page config as the first Streamlit command
st.set_page_config(page_title="AI Chatbot Meetings", page_icon="🥾")
st.session_state.timezone = streamlit_js_eval(
        js_expressions='Intl.DateTimeFormat().resolvedOptions().timeZone', want_output = True, key = 'TZ2')

# Centralized session state keys for maintainability. Order matters.
SESSION_STATE_KEYS = [
    'timezone',
    'chat_history',
    'app_config',
    'debug_mode',
    'userlink',
    'chat_model',
    'selected_model',
]

def init_session_state() -> None:
    """Initialize Streamlit session state variables. Should be called once at app startup."""
    for key in SESSION_STATE_KEYS:
        if key not in st.session_state:
            # Set defaults for known keys
            if key == 'chat_history':
                st.session_state[key] = ChatHistoryManager(timezone=st.session_state.timezone)
            elif key == 'app_config':
                st.session_state[key] = AppConfig.from_env()
                st.session_state[key].calcom.timezone = st.session_state.timezone
            elif key == 'debug_mode':
                st.session_state[key] = st.session_state.app_config.debug_mode
            elif key == 'selected_model':
                st.session_state[key] = st.session_state.app_config.openai.model_name
            elif key == 'timezone2':
                st.session_state[key] = streamlit_js_eval(
                    js_expressions='Intl.DateTimeFormat().resolvedOptions().timeZone', want_output=True, key='TZ')
            elif key == 'userlink':
                st.session_state[key] = "cal.com/"
            else:
                st.session_state[key] = None

def dbg(msg: str) -> None:
    """Debug logging function."""
    if st.session_state.get('debug_mode', False):
        logger.info(msg)


def setup_page() -> None:
    """Set up the Streamlit page layout and sidebar."""
    st.title("🤖 AI Chatbot for Meetings")
    userlink = st.session_state.userlink
    st.markdown(f"I can help you schedule meetings based on [{userlink}](https://{userlink}) calendar availability!")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Help me to book a meeting for tomorrow**")
    with col2:
        st.info("**Show me the scheduled events**")


def init_api_keys() -> None:
    """Get API keys from config or user input. User input takes precedence over config/env/default.
    Updates st.session_state.app_config if user provides new keys.
    Returns:
        Tuple[str, str]: OpenAI API key and Cal.com API key
    """
    openai_api_key = st.session_state.app_config.openai.api_key
    calcom_api_key = st.session_state.app_config.calcom.api_key
    if not openai_api_key:
        openai_api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.", icon="🗝️")
            st.stop()
        # User input takes precedence
        st.session_state.app_config.openai.api_key = openai_api_key
    if not calcom_api_key:
        calcom_api_key = st.text_input("Cal.com API Key", type="password", help="Enter your Cal.com API key")
        if not calcom_api_key:
            st.info("Please add your Cal.com API key to continue. Will book on this user's calendar.", icon="🗝️")
            st.stop()
        st.session_state.app_config.calcom.api_key = calcom_api_key


@st.fragment
def download_messages() -> None:
    """Create a download button to save chat messages as JSON file."""
    dbg("Initializing download_messages()")        
    now = datetime.now()
    fn = f"ai_messages_{now.strftime('%Y-%m-%d')}_{int(now.timestamp())}.json"
    messages_json = st.session_state.chat_history.export_json()
    dbg(f"messages_json now {len(messages_json)} bytes, {len(st.session_state.chat_history.messages)} messages")
    st.markdown("Save chat messages by downloading.  \nClick twice to get latest (bug).")
    st.download_button(
        label="Download Messages as JSON",
        data=messages_json,
        on_click=lambda: dbg("Download button clicked"),
        file_name=fn,
        mime="application/json"
    )
    dbg(f"Initialized download_button {len(messages_json)} bytes for file_name={fn}")


def upload_messages() -> None:
    """Handle file upload to restore previous chat messages from JSON file."""
    dbg("Initializing upload_messages()")
    # uploader_key https://discuss.streamlit.io/t/how-to-remove-the-uploaded-file/70346/3
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 1
    uploaded_file = st.file_uploader(
        "Restore Saved Chat Messages.\nChoose a File",
        key=st.session_state.uploader_key,
        type="json")    
    if uploaded_file is not None:
        try:
            dbg(f"Uploaded {uploaded_file.size} bytes from {uploaded_file.name}")
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()
            st.session_state.chat_history.import_json(string_data)
            uploaded_file = None
            st.session_state.uploader_key += 1
        except Exception as e:
            st.error("Error parsing JSON file. Please ensure the file is in the correct format.", icon="🚨")
            st.exception(e)


def setup_sidebar() -> None:
    """Configure and display sidebar elements."""
    with st.sidebar:
        st.header("Settings")        
        model_options = st.session_state.app_config.openai.models_available
        st.session_state.selected_model = st.selectbox(
            "Select [OpenAI Model](https://platform.openai.com/docs/models)",
            model_options,
            index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
            help="Choose which OpenAI model to use for responses"
        )
        st.session_state.app_config.openai.model_name = st.session_state.selected_model
        st.session_state.debug_mode = st.checkbox(
            "Enable Debug Logging", 
            value=st.session_state.debug_mode,
            help="Show detailed logging information"
        )        
        try:
            st.subheader("Configuration")
            st.text(f"Current Model: {st.session_state.selected_model}")
            st.text(f"Timezone: {st.session_state.timezone}")
            st.text(f"Log Level: {st.session_state.app_config.log_level}")
        except Exception as e:
            st.error(f"Configuration error: {e}")
        
        st.divider()
        
        # File operations
        download_messages()
        upload_messages()

        st.divider()
        st.markdown("**View the code on GitHub: [chadn/ai-chatbot-meetings](https://github.com/chadn/ai-chatbot-meetings)**")



def render_message(message: BaseMessage) -> None:
    """Render a chat message in the Streamlit interface."""
    if hasattr(message, 'type'):
        if message.type == "human":
            with st.chat_message("user"):
                st.write(message.content)
        elif message.type == "ai":
            with st.chat_message("assistant"):
                st.write(message.content)
        elif message.type == "tool":
            # Don't display tool messages in the UI
            pass
        elif message.type == "system":
            # Don't display system messages in the UI
            pass
    else:
        # Fallback for messages without type
        with st.chat_message("assistant"):
            st.write(str(message))


def display_chat_history() -> None:
    """Display all messages in the chat history."""
    for msg in st.session_state.chat_history.get_just_ai_human_message():
        render_message(msg)


def handle_user_input(chat_model: ChatModelService) -> None:
    """Handle user input and generate AI responses."""
    if prompt := st.chat_input("What can I answer for you today?"):
        # Add user message to history and display it
        st.session_state.chat_history.add_human_message(prompt)
        render_message(st.session_state.chat_history.messages[-1])
        
        # Generate and display response
        try:
            chat_model.generate_response_langchain()
            dbg("generate_response_langchain returned")
            render_message(st.session_state.chat_history.messages[-1])
        except Exception as e:
            logger.error(f"generate_response_langchain failed. {type(e).__name__} Exception: {e}")
            logger.error("generate_response_langchain traceback:")
            logger.error(traceback.format_exc())
            st.error(f"Error generating response: {str(e)}", icon="🚨")


def main() -> None:
    """Main application function."""
    init_session_state()
    setup_page()
    setup_sidebar()
    init_api_keys()

    try:
        if st.session_state.chat_model and st.session_state.selected_model != st.session_state.chat_model.config.openai.model_name:
            st.session_state.chat_model = None
        if "chat_model" not in st.session_state or st.session_state.chat_model is None:
            dbg(f"Creating new chat_model with model_name={st.session_state.selected_model}")
            st.session_state.chat_model = ChatModelService(st.session_state.app_config, st.session_state.chat_history)
            st.session_state.chat_model.set_chat_history(st.session_state.chat_history)
            username = getattr(st.session_state.chat_model.calcom_service, "username", None)
            if username and username != "unknown":
                st.session_state.userlink = f"cal.com/{username}"
        
        display_chat_history()
        handle_user_input(st.session_state.chat_model)
    except Exception as e:
        logger.error(f"main() {type(e).__name__} Exception: {e}")
        logger.error("main() traceback:")
        logger.error(traceback.format_exc())
        st.error(f"Application error: {str(e)}", icon="🚨")

if __name__ == "__main__":
    main()

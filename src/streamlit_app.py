"""
Main Streamlit application for the chatbot interface.
"""
import os
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
from utils.utils import dbg_important
from config import get_config
from config.settings import OpenAIConfig, CalComConfig, AppConfig, OPENAI_MODELS_AVAILABLE

# Set up logger for this module
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

# Set page config as the first Streamlit command
st.set_page_config(page_title="AI Chatbot Meetings", page_icon="🥾")
st.session_state.timezone = streamlit_js_eval(
        js_expressions='Intl.DateTimeFormat().resolvedOptions().timeZone', want_output = True, key = 'TZ2')


def dbg(msg: str) -> None:
    """Debug logging function."""
    if st.session_state.get('dbg_print', False):
        logger.info(msg)

def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = ChatHistoryManager()
    
    # Debug settings
    if 'dbg_print' not in st.session_state:
        st.session_state.dbg_print = os.getenv('DEBUG_PRINT', 'false').lower() == 'true'
    
    # Model selection
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = os.getenv('OPENAI_MODEL_NAME')


def setup_page() -> None:
    """Set up the Streamlit page layout and sidebar."""
    st.title("🤖 AI Chatbot for Meetings")
    userlink = f"cal.com/{get_config().calcom.username}"
    st.markdown(f"I can help you schedule meetings based on [{userlink}](https://{userlink}) calendar availability!")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Help me to book a meeting for tomorrow**")
    with col2:
        st.info("**Show me the scheduled events**")


def get_api_keys() -> Tuple[str, str]:
    """Get API keys from environment or user input.
    
    Returns:
        Tuple[str, str]: OpenAI API key and Cal.com API key
    """
    from_env = []
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        from_env.append("OPENAI_API_KEY")
    else:        
        openai_api_key = st.text_input("OpenAI API Key", type="password", 
                            help="Enter your OpenAI API key")
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.", icon="🗝️")
            st.stop()
    
    calcom_api_key = os.getenv('CALCOM_API_KEY')
    if calcom_api_key:
        from_env.append("CALCOM_API_KEY")
    else:        
        calcom_api_key = st.text_input("Cal.com API Key", type="password", 
                            help="Enter your Cal.com API key")
        if not calcom_api_key:
            st.info("Please add your Cal.com API key to continue.", icon="🗝️")
            st.stop()

    if from_env:
        st.write(f"Using {', '.join(from_env)} from env variable")
    return openai_api_key, calcom_api_key


def get_chat_model(openai_api_key: str, calcom_api_key: str, timezone: str, model_name: str) -> ChatModelService:
    """Initialize the chat model service with dynamic configuration.
    
    Args:
        openai_api_key: OpenAI API key
        calcom_api_key: Cal.com API key
        timezone: Timezone
        model_name: Selected model name
        
    Returns:
        ChatModelService: Initialized chat model service
    """
    # Create dynamic configuration
    openai_config = OpenAIConfig(
        api_key=openai_api_key,
        model_name=model_name
    )
    calcom_config = CalComConfig(
        api_key=calcom_api_key,
        timezone=timezone
    )
    app_config = AppConfig(
        openai=openai_config,
        calcom=calcom_config
    )
    
    dbg(f"Using model: {model_name}")
    return ChatModelService(app_config, st.session_state.chat_history)


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
        
        # Model selection
        model_options = OPENAI_MODELS_AVAILABLE
        st.session_state.selected_model = st.selectbox(
            "Select [OpenAI Model](https://platform.openai.com/docs/models)",
            model_options,
            index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
            help="Choose which OpenAI model to use for responses"
        )
        
        # Debug toggle
        st.session_state.dbg_print = st.checkbox(
            "Enable Debug Logging", 
            value=st.session_state.dbg_print,
            help="Show detailed logging information"
        )
        
        # Configuration info
        try:
            config = get_config()
            st.subheader("Configuration")
            st.text(f"Current Model: {st.session_state.selected_model}")
            st.text(f"Timezone: {st.session_state.timezone}")
            st.text(f"Log Level: {config.log_level}")
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
    # Chat input
    dbg_important("handle_user_input starting")
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

    if "openai_api_key" not in st.session_state:
        (st.session_state.openai_api_key, st.session_state.calcom_api_key) = get_api_keys()
    
    if st.session_state.openai_api_key:
        try:
            # Check if we need to recreate the chat model due to model change
            if ("chat_model" not in st.session_state or 
                getattr(st.session_state.chat_model.config.openai, 'model_name', None) != st.session_state.selected_model):
                st.session_state.chat_model = get_chat_model(
                    st.session_state.openai_api_key, 
                    st.session_state.calcom_api_key, 
                    st.session_state.timezone,
                    st.session_state.selected_model
                )
                st.session_state.chat_model.set_chat_history(st.session_state.chat_history)
            
            display_chat_history()
            handle_user_input(st.session_state.chat_model)
        except Exception as e:
            logger.error(f"main() {type(e).__name__} Exception: {e}")
            logger.error("main() traceback:")
            logger.error(traceback.format_exc())
            st.error(f"Application error: {str(e)}", icon="🚨")

if __name__ == "__main__":
    main()





import streamlit as st
import boto3
import json
import uuid
from datetime import datetime

# Set up the page configuration
st.set_page_config(page_title="Bedrock Agent Chatbot", page_icon="🤖", layout="wide")

# Function to initialize session state variables
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if "bedrock_client" not in st.session_state:
        # Initialize AWS Bedrock client
        try:
            st.session_state.bedrock_client = boto3.client('bedrock-agent-runtime')
        except Exception as e:
            st.error(f"Error initializing Bedrock client: {str(e)}")
            st.session_state.bedrock_client = None

# Initialize session state
initialize_session_state()

# Sidebar for configuration
st.sidebar.title("Configuration")
agent_id = st.sidebar.text_input("Agent ID", help="Enter your Bedrock Agent ID")
agent_alias_id = st.sidebar.text_input("Agent Alias ID", help="Enter your Bedrock Agent Alias ID")

# Create a unique session ID if not already set
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Set up main interface
st.title("Bedrock Agent Chatbot")
st.markdown("Chat with your Amazon Bedrock Agent")

# Function to interact with Bedrock Agent
def query_bedrock_agent(user_input):
    if not agent_id or not agent_alias_id:
        return {"error": "Please provide Agent ID and Agent Alias ID in the sidebar."}
    
    if st.session_state.bedrock_client is None:
        return {"error": "Bedrock client not initialized. Check your AWS credentials."}
    
    try:
        response = st.session_state.bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=st.session_state.session_id,
            inputText=user_input
        )
        
        # Process the response
        response_text = ""
        for event in response.get('completion'):
            chunk = event.get('chunk')
            if chunk:
                response_text += chunk.get('bytes').decode('utf-8')
        
        return {"response": response_text}
        
    except Exception as e:
        return {"error": f"Error querying Bedrock Agent: {str(e)}"}

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display thinking indication
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.write("Thinking...")
        
        # Query Bedrock Agent
        agent_response = query_bedrock_agent(prompt)
        
        # Display response
        if "error" in agent_response:
            thinking_placeholder.error(agent_response["error"])
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {agent_response['error']}"})
        else:
            thinking_placeholder.write(agent_response["response"])
            st.session_state.messages.append({"role": "assistant", "content": agent_response["response"]})

# Add a button to clear the conversation
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.session_id = str(uuid.uuid4())
    st.experimental_rerun()

# AWS credentials configuration
st.sidebar.title("AWS Configuration")
st.sidebar.info(
    """
    This app requires valid AWS credentials to be configured on your system. 
    You can set these up via:
    - AWS CLI configuration
    - Environment variables
    - IAM roles (if running on AWS)
    
    Make sure the credentials have access to Bedrock and Bedrock Agent services.
    """
)

# Display current session information
st.sidebar.title("Session Info")
st.sidebar.text(f"Session ID: {st.session_state.session_id[:8]}...")
st.sidebar.text(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
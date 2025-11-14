"""
Simple Chatbot - Streamlit application for RAG queries.

Simplified version that works with simple_rag API.
Only includes conversation interface and chat functionality.
"""
import streamlit as st
from rag_client import get_rag_client
from ui_styles import get_custom_css, get_new_conversation_button_style
import utils

# --- Page Configuration ---
st.set_page_config(page_title="RAG Chatbot", layout="wide")

# Initialize session state
if 'conversation_id' not in st.session_state:
    st.session_state['conversation_id'] = None
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'selected_conversation' not in st.session_state:
    st.session_state['selected_conversation'] = None

# Initialize RAG client
rag_client = get_rag_client()

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("Conversations")

# Apply new conversation button style
st.sidebar.markdown(get_new_conversation_button_style(), unsafe_allow_html=True)

if st.sidebar.button("New Chat", use_container_width=True, type="primary"):
    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.session_state.selected_conversation = None
    st.rerun()

# Display conversation history
conversations = rag_client.list_conversations(limit=20)

if conversations:
    st.sidebar.markdown("---")
    
    for conversation in conversations:
        with st.sidebar.container():
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                is_selected = st.session_state.get('selected_conversation') == conversation["conversation_id"]
                
                title = conversation['title']
                if len(title) > 20:
                    display_title = title[:17] + "..."
                else:
                    display_title = title
                
                if st.button(
                    f"{display_title}", 
                    key=f"select_{conversation['conversation_id']}", 
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                    help=f"{title}" if len(title) > 20 else None
                ):
                    st.session_state.selected_conversation = conversation["conversation_id"]
                    st.session_state.conversation_id = conversation["conversation_id"]
                    messages = rag_client.get_messages(conversation["conversation_id"])
                    st.session_state.messages = []
                    for msg in messages:
                        message_data = {"role": msg["role"], "content": msg["content"]}
                        if msg.get("sources"):
                            message_data["sources"] = msg["sources"]
                        st.session_state.messages.append(message_data)
                    st.rerun()
            
            with col2:
                if st.button(
                    "🗑️", 
                    key=f"delete_{conversation['conversation_id']}", 
                    use_container_width=True,
                    help="Delete this conversation",
                    type="secondary"
                ):
                    try:
                        rag_client.delete_conversation(conversation["conversation_id"])
                        st.toast(f"🗑️ Deleted: '{conversation['title']}'")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting conversation: {e}")
        
        st.sidebar.markdown("")
else:
    st.sidebar.markdown("### 💬 No conversations yet")
    st.sidebar.markdown("Start a new conversation below!")

# --- Main UI ---
st.title("RAG Chatbot")

# Display chat messages from history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            sources = message["sources"]
            sources_container = st.container()
            with sources_container:
                st.markdown("---")
                st.markdown("**Sources:**")
                max_cols = 4
                cols = st.columns(max_cols)
                col_idx = 0
                for j, source in enumerate(sources):
                    doc = source if isinstance(source, dict) else {}
                    # New format: chunk_id, filename, chunk_text, document_id
                    chunk_id = doc.get("chunk_id") or f"Chunk {j+1}"
                    filename = doc.get("filename") or "Unknown"
                    chunk_text = doc.get("chunk_text") or ""
                    preview = chunk_text.strip()
                    if len(preview) > 150:
                        preview = preview[:150] + "..."
                    
                    # Display source as a button/link
                    with cols[col_idx]:
                        source_label = f"{filename}" if len(filename) <= 15 else f"{filename[:12]}..."
                        if st.button(
                            source_label,
                            key=f"msg_{i}_source_{j}",
                            help=f"**{filename}** ({chunk_id}):\n\n{preview}",
                            use_container_width=True
                        ):
                            # Could add functionality here later (e.g., show full source)
                            pass
                    col_idx = (col_idx + 1) % max_cols

# --- User Interaction ---
if prompt := st.chat_input("Ask a question..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Create conversation if this is the first message
    if st.session_state.conversation_id is None:
        with st.spinner("Creating conversation..."):
            title = rag_client.generate_conversation_title(prompt)
            st.session_state.conversation_id = rag_client.create_conversation(title)
    
    # Save user message to database
    rag_client.add_message(
        st.session_state.conversation_id, 
        "user", 
        prompt
    )
    
    with st.spinner("Thinking..."):
        try:
            assistant_response, sources = rag_client.ask(prompt, top_k=5, use_reranking=True)
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "sources": sources
            })
            
            # Save assistant response to database
            rag_client.add_message(
                st.session_state.conversation_id,
                "assistant", 
                assistant_response,
                sources
            )
            
            st.rerun()
        except Exception as e:
            st.error(f"Error connecting to the RAG API: {e}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Sorry, there was an error with the backend service.",
                "sources": []
            })
            st.rerun()

# Add disclaimer at the bottom
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9em; padding: 10px;'>"
    "The chatbot may make errors. Please verify important information."
    "</div>",
    unsafe_allow_html=True
)


import pandas as pd 
import streamlit as st 
import io 
import os 

# LlamaIndex imports 
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# --- Page Configuration ---
# Set the page title and a relevant icon. The layout "wide" is good for apps that display a lot of data.
st.set_page_config(
    page_title="Local Log Analyzer",
    layout="wide"
)

# --- Constants for LLM and Embedding Model ---
LLM_MODEL_NAME = "gemma3:latest"
EMBEDDING_MODEL_NAME = "nomic-embed-text"

# --- Application Title ---
st.title("Local Log Analyzer with Gemma 3")
st.write("Upload your log or CSV file, and then ask questions about it!")

# --- Session State Initialization ---
# This is crucial for keeping data persistent across user interactions (re-runs).
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "df" not in st.session_state:
    st.session_state.df = None # To store the pandas DataFrame
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None  # To store the chat engine

# --- Helper Function to Initialize LlamaIndex ---
@st.cache_resource(show_spinner="Initializing LlamaIndex and building file index...")
def initialize_llama_index(_df: pd.DataFrame, _uploaded_file_name_for_cache_key: str): 
    """Initializes LlamaIndex compenents (LLM, Embedding Model, Index, and Chat Engine) using the uploaded DataFrame.
    Using _uploaded_file_name_for_cache_key as a cache key to help Streamlit's cashing bust correctly on a new file

    Args:
        _df (pd.DataFrame):  The DataFrame containing the uploaded CSV data.
        _uploaded_file_name_for_cache_key (str):  The cache key for the uploaded file name. 
    """
    try: 
        # Get Ollama URL from the environment variable or use the default
        # The docker-compose.yml file sets OLLAMA_API_BASE_URL to htpp://localhost:11434
        # The port is mapped to 11435 on the docker container to not conflict with the Ollama CLI locally
        # As such, we will use 11435 as the default 
        ollama_base_url = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11435")
        st.write(f'Connecting to Ollama at {ollama_base_url}...')
        st.write(f'Using LLM: {LLM_MODEL_NAME} and Embedding Model: {EMBEDDING_MODEL_NAME}')

        # Initialize the LLM and Embedding Model from Ollama 
        llm = Ollama(model=LLM_MODEL_NAME, base_url=ollama_base_url, request_timeout=120)
        embed_model = OllamaEmbedding(model_name=EMBEDDING_MODEL_NAME, 
                                      base_url=ollama_base_url, 
                                      embed_batch_size=64)

        # Configure the LlamaIndex global settings 
        Settings.llm = llm
        Settings.embed_model = embed_model
        # Settings.chunk_size = 512  # Set chunk size for document processing
        # Settings.chunk_overlap = 50  # Set chunk overlap for document processing

        # Convert the DataFrame rows to LlamaIndex Documents
        docs = [] 
        for i, row in _df.astype(str).iterrows():
          # Create a text representation of each row 
          row_text = ", ".join([f"{col}: {val}" for col, val in row.items()])
          docs.append(Document(text=f"Row {i}: {row_text}")) # Add row index for context

        if not docs: 
            st.warning("The CSV file seems empty or could not be processed into documents.")
            return None 
        
        st.write(f"Created {len(docs)} documents from the uploaded CSV file for embedding.")
        # Create a VectorStoreIndex from the documents in memory 
        index = VectorStoreIndex.from_documents(docs, show_progress=True)

        # Create the chat engine 
        # "condense_plus_context" is good for maintaining conversational context with RAG 
        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            verbose=True
        )
        st.success("LlamaIndex chat engine initialized successfully!")
        return chat_engine
    except Exception as e:
        st.error(f"Error initializing LlamaIndex: {e}")
        return None



# --- Sidebar for File Upload ---
with st.sidebar:
    st.header("1. Upload Your CSV File")
    
    # Use the file_uploader widget.
    # "type" restricts the user to upload only specific file types.
    uploaded_file_obj = st.file_uploader(
        "Choose a CSV log file",
        type=["csv"]
    )

    if uploaded_file_obj: 
        new_file_uploaded = (st.session_state.uploaded_file_name != uploaded_file_obj.name)
        if new_file_uploaded: 
            st.session_state.uploaded_file_name = uploaded_file_obj.name 
            st.session_state.messages = [] # Reset chat messages on new file upload
            st.session_state.chat_engine = None # Reset chat engine on new file upload
            st.session_state.df = None # Reset DataFrame on new file upload

            with st.spinner("Processing uploaded log file..."): 
                try: 
                    st.session_state.df = pd.read_csv(uploaded_file_obj, nrows=100)
                    st.success(f"File '{uploaded_file_obj.name}' uploaded successfully!")

                    # Initialize LlamaIndex and chat engine after the df is loaded 
                    # Pass df and filename to ensure cache invalidation on new file upload 
                    st.session_state.chat_engine = initialize_llama_index(st.session_state.df.copy(), uploaded_file_obj.name)

                except Exception as e: 
                    st.error(f"Error reading or processing CSV file: {e }")
                    st.session_state.uploaded_file_name = None 
                    st.session_state.df = None 
                    st.session_state.chat_engine = None
        elif st.session_state.df is not None and st.session_state.chat_engine is None:
            # This case handles if the same file is re-processed after an error, or if app reloads and df is present 
            # but engine is not 
            with st.spinner("Re-initializing LlamaIndex chat engine..."):
                st.session_state.chat_engine = initialize_llama_index(st.session_state.df.copy(), st.session_state.uploaded_file_name)

# --- Main Chat Interface ---

# Display a message to the user if no file has been uploaded yet.
if st.session_state.df is None:
    st.info("Please upload a file in the sidebar to begin.")
else:
    # This is where the main logic for LlamaIndex and chat will go.
    # For now, we'll just display the name of the file and the header. 
        # --- Display a preview of the DataFrame ---
    st.header("CSV Preview (First 10 Rows)")
    st.dataframe(st.session_state.df.head(10))
    
    st.divider()
    
    st.header(f"Chat about: `{st.session_state.uploaded_file_name}`")

    # Display existing messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input 
    if prompt := st.chat_input("Ask a question about your file..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        
        if st.session_state.chat_engine: 
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."): 
                    try: 
                        # Use stream_chat for a streaming response 
                        streaming_response = st.session_state.chat_engine.stream_chat(prompt) 
                        response_container = st.empty()  # Placeholder for streaming response
                        full_response_text = "" 
                        for token in streaming_response.response_gen: 
                            full_response_text += token
                            response_container.markdown(full_response_text + "▌") # Show cursor while streaming response
                        response_container.markdown(full_response_text)  # Finalize the response

                        st.session_state.messages.append({"role": "assistant", "content": full_response_text})
                    except Exception as e:
                        error_message = f"Error during chat: {e}"
                        st.error(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": error_message})
        else: 
            st.warning("Chat engine is not initialized. Please ensuere a file is uploaded and processed.")
            st.session_state.messages.append({"role": "assistant", "content": "Chat engine not ready"})


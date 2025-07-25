import pandas as pd 
import streamlit as st  
import os 
import torch 
import tomllib

# LlamaIndex imports.
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

if hasattr(torch, 'classes'):
    # Known issue with torch and streamlit. This is a bypass for the error. 
    torch.classes.__path__ = []

# --- Page Configuration ---
# Set the page title and a relevant icon. The layout "wide" is good for apps that display a lot of data.
st.set_page_config(
    page_title="Local Log Analyzer",
    layout="wide"
)

# --- Constant for Embedding Model. This is likely never to change so not included in config.toml ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # Local HuggingFace model for embeddings

# ---Defaults for configuration loading ---
DEFAULT_LLM_MODEL_NAME = "tinyllama"
DEFAULT_PROCESSING_ROW_LIMIT = None # Process all rows by default if not specified
DEFAULT_SIMILAR_DOCUMENTS_LIMIT = 5

config = {}
try:
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    print("[INFO] Loaded configuration from config.toml")
except FileNotFoundError:
    print("[INFO] config.toml not found, using default settings.")
except tomllib.TOMLDecodeError:
    print("[ERROR] Error decoding config.toml, using default settings.")

LLM_MODEL_NAME = config.get("LLM_MODEL_NAME", DEFAULT_LLM_MODEL_NAME)

PROCESSING_ROW_LIMIT_CONFIG = config.get("PROCESSING_ROW_LIMIT", DEFAULT_PROCESSING_ROW_LIMIT)
if isinstance(PROCESSING_ROW_LIMIT_CONFIG, int) and PROCESSING_ROW_LIMIT_CONFIG > 0: 
    PROCESSING_ROW_LIMIT = PROCESSING_ROW_LIMIT_CONFIG
else: 
    PROCESSING_ROW_LIMIT = DEFAULT_PROCESSING_ROW_LIMIT

SIMILAR_DOCUMENTS_LIMIT_CONFIG = config.get("SIMILAR_DOCUMENTS_LIMIT", DEFAULT_SIMILAR_DOCUMENTS_LIMIT)
if isinstance(SIMILAR_DOCUMENTS_LIMIT_CONFIG, int) and SIMILAR_DOCUMENTS_LIMIT_CONFIG > 1: 
    SIMILAR_DOCUMENTS_LIMIT = SIMILAR_DOCUMENTS_LIMIT_CONFIG
else: 
    SIMILAR_DOCUMENTS_LIMIT = DEFAULT_SIMILAR_DOCUMENTS_LIMIT


# --- Application Title ---
st.title(f"Local Log Analyzer with {LLM_MODEL_NAME.upper()}")
st.write("Upload your log CSV file, and then ask questions about it!")
st.write(f"*Keep in mind that we are only retrieving {SIMILAR_DOCUMENTS_LIMIT} documents due to hardware limitations*")
st.write("Please see the README for more details")

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
        st.write(f'Connecting to Ollama at {ollama_base_url}')
        # st.write(f'Using LLM: {LLM_MODEL_NAME} and Embedding Model: {EMBEDDING_MODEL_NAME}')
        st.write(f'Using LLM: {LLM_MODEL_NAME} and Embedding Model: {EMBEDDING_MODEL_NAME}')

        # Initialize the LLM and Embedding Model from Ollama 
        llm = Ollama(model=LLM_MODEL_NAME, base_url=ollama_base_url, request_timeout=120)
        embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_NAME, 
                                           embed_batch_size=64)

        # Configure the LlamaIndex global settings 
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.chunk_size = 1024  # Set chunk size for document processing
        Settings.chunk_overlap = 50  # Set chunk overlap for document processing

        docs = [] 
        for i, row in _df.astype(str).iterrows(): 
            row_text = ", ".join([f"{col}: {val}" for col, val in row.items()])
            doc_id = f"{_uploaded_file_name_for_cache_key}_row_{i}"
            docs.append(Document(text=f"Row {i}: {row_text}", doc_id=doc_id))

        if not docs: 
            st.warning("The CSV data resulted in no documents to process")
            return None 

        st.write(f"Created {len(docs)} documents")
        st.write(f"Creating document embeddings...")

        # Create a VectorStoreIndex from the documents in memory 
        index = VectorStoreIndex.from_documents(docs, show_progress=True, use_async=False)
        st.write("Finished creating document embeddings. Initializing chat engine.")

        system_prompt = (
            "You are a helpful assistant for analyzing data from a CSV file. "
            "You will be given context from one or more rows of the file to answer the user's question. "
            "Your knowledge is strictly limited to the information provided in the context. "
            "When asked to count items like 'files' or 'entries', you should count the number of distinct 'Row X:' items you see in the context, not interpret the text within the rows. "
            "For example, if the context contains the text '*.log', do not assume this refers to actual files; it is just text within a row's data. "
            "If the answer is not in the context, clearly state that you do not have enough information based on the provided data."
        )
        # retriever = index.as_retriever(similarity_top_k=3)
        # chat_engine = CondensePlusContextChatEngine.from_defaults(
        #     retriever=retriever, 
        #     verbose=True
        # )
        # Create the chat engine 
        # "condense_plus_context" is good for maintaining conversational context with RAG 
        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context", # type: ignore
            verbose=True,
            similarity_top_k=SIMILAR_DOCUMENTS_LIMIT, 
            system_prompt=system_prompt
        )
        st.write("Chat engine initialized")
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
        type=["csv"], 
        key="file_uploader_widget"
    )

    if uploaded_file_obj: 
        new_file_uploaded = st.session_state.uploaded_file_name != uploaded_file_obj.name
    
        if new_file_uploaded: 
            # Clear the cache resource so that we trigger the recomputation of embeddings on file change
            st.cache_resource.clear()

            # Set the session state variables accordingly
            st.session_state.uploaded_file_name = uploaded_file_obj.name 
            st.session_state.messages = [] # Reset chat messages on new file upload
            st.session_state.chat_engine = None # Reset chat engine on new file upload
            st.session_state.df = None # Reset DataFrame on new file upload

            with st.spinner("Processing uploaded log file..."): 
                try: 
                    st.session_state.df = pd.read_csv(uploaded_file_obj, 
                                                      nrows=PROCESSING_ROW_LIMIT
                                                      )
                    st.success(f"File '{uploaded_file_obj.name}' uploaded successfully!")

                    # Initialize LlamaIndex and chat engine after the df is loaded 
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
    st.header(f"{st.session_state.uploaded_file_name} Preview (First 10 Rows)")
    st.dataframe(st.session_state.df.head(10))
    
    st.divider()
    
    st.header(f"Chat about: `{st.session_state.uploaded_file_name}`")

    # Display existing messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input 
    if prompt := st.chat_input(f"Ask a question about {st.session_state.uploaded_file_name}..."):
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


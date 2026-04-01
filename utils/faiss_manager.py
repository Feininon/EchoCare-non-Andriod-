# utils/faiss_manager.py
import os
import faiss
import numpy as np
from langchain_ollama import OllamaEmbeddings

class FAISSManager:
    """
    Manages user-specific vector indexes for context retrieval.
    Matches Architecture: Data & Memory Layer (Vector Store)
    """
    
    def __init__(self, base_dir="faiss_indexes", msg_dir="messages"):
        self.base_dir = base_dir
        self.msg_dir = msg_dir
        self.embedding_model = OllamaEmbeddings(model="nomic-embed-text")
        self.dimension = 768  # Matches nomic-embed-text
        
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.msg_dir, exist_ok=True)

    def get_user_paths(self, user_id):
        """Generate secure paths for user data."""
        # Sanitize user_id to prevent directory traversal
        safe_id = "".join(c for c in user_id if c.isalnum())
        return (
            f"{self.base_dir}/faiss_index_{safe_id}.index",
            f"{self.msg_dir}/message_store_{safe_id}.txt"
        )

    def load_index(self, user_id):
        """Load existing FAISS index or create new one."""
        index_path, _ = self.get_user_paths(user_id)
        
        if os.path.exists(index_path):
            return faiss.read_index(index_path)
        else:
            return faiss.IndexFlatL2(self.dimension)

    def save_index(self, user_id, index):
        """Persist FAISS index to disk."""
        index_path, _ = self.get_user_paths(user_id)
        faiss.write_index(index, index_path)

    def add_message(self, user_id, text, role, index):
        """Embed and store a new message."""
        _, text_path = self.get_user_paths(user_id)
        
        # Clean text
        clean_text = " ".join(text.split())
        
        # Generate Embedding
        embedding = self.embedding_model.embed_documents([clean_text])[0]
        index.add(np.array([embedding], dtype=np.float32))
        
        # Store raw text for retrieval context
        with open(text_path, "a", encoding="utf-8") as f:
            f.write(f"{role}: {clean_text}\n")

    def retrieve_context(self, user_id, query, index, top_k=3):
        """Retrieve relevant conversation history."""
        _, text_path = self.get_user_paths(user_id)
        
        if not os.path.exists(text_path):
            return ""
            
        with open(text_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if not lines:
            return ""
            
        # Embed Query
        query_embedding = self.embedding_model.embed_query(query)
        
        # Search
        distances, indices = index.search(
            np.array([query_embedding], dtype=np.float32), 
            min(top_k, len(lines))
        )
        
        # Extract text
        retrieved = []
        for i in indices[0]:
            if 0 <= i < len(lines):
                # Remove role prefix for context
                content = lines[i].strip().split(":", 1)[1] 
                retrieved.append(content)
                
        return "\n".join(retrieved)
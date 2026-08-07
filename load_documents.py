from langchain_community.document_loaders import PyPDFLoader
import json
import os

GUIDELINES_PATH = "data/guidelines"
SOURCES_FILE = "data/sources.json"

def load_documents():
    # Attaches metadata from sources.json to each document loaded from the guidelines folder
    with open(SOURCES_FILE) as f:
        sources = json.load(f)

    documents = []
    for filename, meta in sources.items():
        loader = PyPDFLoader(os.path.join(GUIDELINES_PATH, filename))
        docs = loader.load()
        for doc in docs:
            doc.metadata.update(meta) # Add metadata from sources.json to each document
        documents.extend(docs)
    return documents

from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents):
    # Split documents into smaller chunks for processing
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
    )
    return splitter.split_documents(documents)

if __name__ == "__main__":
    # Load documents and split them into chunks
    docs = load_documents()
    chunks = split_documents(docs)
    print(f"Loaded {len(docs)} pages -> {len(chunks)} chunks.")
    print(chunks[0].page_content[:300])
    print(chunks[0].metadata)
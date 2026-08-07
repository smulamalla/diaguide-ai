import shutil
import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from load_documents import load_documents, split_documents


load_dotenv()  # load API keys from .env file

CHROMA_PATH = "chroma"


def create_database():
    """
    Creates a Chroma database from the loaded documents, splits them into chunks,
    and saves the database to disk.
    """
    documents = load_documents()
    chunks = split_documents(documents)

    # Remove the previous Chroma database
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Build and persist the database
    Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH,
    )

    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    create_database()
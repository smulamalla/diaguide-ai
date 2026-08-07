from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings()

vector = embeddings.embed_query("Hello world")

print(len(vector))
print(vector[:5])
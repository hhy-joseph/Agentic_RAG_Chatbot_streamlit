import streamlit as st
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Initialize OpenAI LLM
llm = OpenAI(temperature=0)

# Initialize vector store
def initialize_vector_store(texts):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.create_documents(texts)
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store

# Vector store search tool
def vector_store_search(query):
    docs = vector_store.similarity_search(query, k=1)
    return docs[0].page_content

vector_tool = Tool(
    name="Vector Store",
    func=vector_store_search,
    description="Useful for searching general information and database metadata."
)

# Initialize SQLite database
def init_sqlite_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, quantity INTEGER)''')
    
    # Insert sample data
    c.execute("INSERT OR IGNORE INTO users VALUES (1, 'Alice', 'alice@example.com')")
    c.execute("INSERT OR IGNORE INTO users VALUES (2, 'Bob', 'bob@example.com')")
    c.execute("INSERT OR IGNORE INTO products VALUES (1, 'Laptop', 999.99)")
    c.execute("INSERT OR IGNORE INTO products VALUES (2, 'Smartphone', 499.99)")
    c.execute("INSERT OR IGNORE INTO orders VALUES (1, 1, 1, 1)")
    c.execute("INSERT OR IGNORE INTO orders VALUES (2, 2, 2, 2)")
    
    conn.commit()
    conn.close()

init_sqlite_db()

# Initialize SQL database
db = SQLDatabase.from_uri("sqlite:///ecommerce.db")

# SQL query tool
def run_sql_query(query):
    sql_chain = create_sql_query_chain(llm, db)
    sql_query = sql_chain.invoke({"question": query})
    result = db.run(sql_query)
    return result

sql_tool = Tool(
    name="SQL Database",
    func=run_sql_query,
    description="Useful for querying specific data from the SQL database."
)

# Initialize agent
tools = [vector_tool, sql_tool]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Sample texts including database metadata and random information
texts = [
    "The e-commerce database has three main tables: users, products, and orders.",
    "The users table contains columns: id (INTEGER PRIMARY KEY), name (TEXT), email (TEXT).",
    "The products table has columns: id (INTEGER PRIMARY KEY), name (TEXT), price (REAL).",
    "The orders table includes: id (INTEGER PRIMARY KEY), user_id (INTEGER), product_id (INTEGER), quantity (INTEGER).",
    "Our e-commerce platform offers a wide range of electronic products.",
    "We have a 30-day return policy for all products purchased through our platform.",
    "Customer satisfaction is our top priority, and we strive to provide excellent service.",
    "We offer free shipping on orders over $500.",
    "Our platform uses advanced encryption to ensure the security of user data.",
    "We have a loyalty program that rewards frequent customers with discounts and special offers.",
]
vector_store = initialize_vector_store(texts)

# Streamlit app
def main():
    st.title("E-commerce Agentic RAG System")

    query = st.text_input("Enter your query:")

    if query:
        response = agent.run(query)
        st.write("Response:", response)

if __name__ == "__main__":
    main()
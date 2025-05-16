import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sales_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# LLM setup
llm = ChatGroq(model="llama3-70b-8192", temperature=0.5)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:0000@localhost:5432/sales_db")
engine = create_engine(DATABASE_URL)

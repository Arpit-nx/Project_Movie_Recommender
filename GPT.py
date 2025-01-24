import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not API_KEY:
    logger.error("API key is missing. Please set it in the .env file.")
    exit()

genai.configure(api_key=API_KEY)

def get_ai_response():
    flag = True
    while flag:
        prompt = input("Your query (type 'exit' to quit): ")
        if prompt.lower() != "exit":
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                print(f"GPT: {response.text}")
            except Exception as e:
                logger.error(f"An error occurred: {e}")
        else:
            flag = False

get_ai_response()

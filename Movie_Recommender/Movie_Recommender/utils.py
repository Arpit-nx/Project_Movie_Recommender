import os

os.environ['GRPC_VERBOSITY'] = 'ERROR'

import google.generativeai as genai
from dotenv import load_dotenv
from django.http import JsonResponse
import logging

# Load environment variables from the .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Retrieve the GOOGLE_GEMINI_API key
API_KEY = os.getenv('API_KEY')

def get_movie_suggestions_from_mood(mood):
    """
    Use Google Gemini API to generate movie suggestions based on user mood.
    """
    try:
        # AI prompt for generating movie recommendations
        prompt = f"Suggest 10 random Hollywood and Bollywood movies for someone in a '{mood}' mood. Return only movie names, separated by commas."
        genai.configure(api_key=API_KEY)
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        # print(response.text)
        if response.text:
            movie_list = [movie.strip() for movie in response.text.split(',')]
            # print(movie_list)
            return movie_list
        else:
            return ["No recommendations available."]

    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn't generate recommendations at this time."
    
get_movie_suggestions_from_mood("happy")
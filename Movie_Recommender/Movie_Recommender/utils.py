import os

os.environ['GRPC_VERBOSITY'] = 'ERROR'

import google.generativeai as genai
from dotenv import load_dotenv
from django.http import JsonResponse
import logging
import json

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
        
        if response.text:
            movie_list = [movie.strip() for movie in response.text.split(',')]
            return movie_list
        else:
            return ["No recommendations available."]

    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn't generate recommendations at this time."

def get_enhanced_movie_suggestions_from_mood(mood):
    """
    Enhanced AI function to generate detailed movie suggestions based on user mood with reasoning.
    """
    try:
        # Enhanced AI prompt for better movie recommendations
        prompt = f"""
        As a movie expert, suggest 8 perfect movies for someone feeling '{mood}'. 
        Consider the psychological impact of movies on mood and recommend films that would either:
        1. Complement their current mood
        2. Help improve their emotional state
        3. Provide the right kind of entertainment for their mindset
        
        For a '{mood}' mood, think about:
        - Genre preferences that match this emotion
        - Pacing and tone that would resonate
        - Themes that would be meaningful
        - Both popular and hidden gem recommendations
        
        Include a mix of:
        - Recent releases (2020-2024)
        - Classic films
        - Different genres
        - Both Hollywood and international cinema
        
        Return only the movie titles, separated by commas. Make sure all titles are accurate and well-known films.
        """
        
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if response.text:
            movie_list = [movie.strip() for movie in response.text.split(',')]
            # Clean up the list and ensure we have valid movie titles
            cleaned_movies = []
            for movie in movie_list:
                # Remove any numbering or extra characters
                cleaned_movie = movie.strip().lstrip('1234567890.- ').strip()
                if cleaned_movie and len(cleaned_movie) > 2:
                    cleaned_movies.append(cleaned_movie)
            
            return cleaned_movies[:8]  # Return max 8 movies
        else:
            return get_fallback_recommendations(mood)

    except Exception as e:
        print(f"Error in enhanced recommendations: {e}")
        return get_fallback_recommendations(mood)

def get_fallback_recommendations(mood):
    """
    Fallback movie recommendations when AI fails.
    """
    mood_movies = {
        'happy': ['The Grand Budapest Hotel', 'La La Land', 'Paddington 2', 'The Princess Bride', 'Mamma Mia!', 'School of Rock', 'The Incredibles', 'Ferris Bueller\'s Day Off'],
        'sad': ['Inside Out', 'Her', 'The Pursuit of Happyness', 'Good Will Hunting', 'A Monster Calls', 'The Green Mile', 'Marley & Me', 'Up'],
        'excited': ['Mad Max: Fury Road', 'John Wick', 'Mission: Impossible', 'The Avengers', 'Baby Driver', 'Speed', 'Die Hard', 'Top Gun: Maverick'],
        'romantic': ['The Notebook', 'Casablanca', 'When Harry Met Sally', 'Pride and Prejudice', 'Titanic', 'Before Sunrise', 'Sleepless in Seattle', 'The Holiday'],
        'adventurous': ['Indiana Jones', 'Pirates of the Caribbean', 'The Lord of the Rings', 'Jurassic Park', 'National Treasure', 'The Mummy', 'Tomb Raider', 'Uncharted'],
        'thoughtful': ['Inception', 'Interstellar', 'The Matrix', 'Blade Runner 2049', 'Arrival', 'Ex Machina', 'Her', 'The Social Dilemma'],
        'nostalgic': ['Back to the Future', 'E.T.', 'The Goonies', 'Stand by Me', 'The Sandlot', 'Home Alone', 'Toy Story', 'The Lion King'],
        'scared': ['Get Out', 'A Quiet Place', 'Hereditary', 'The Conjuring', 'It', 'Scream', 'Halloween', 'The Babadook']
    }
    
    # Find the closest mood match
    mood_lower = mood.lower()
    for key in mood_movies:
        if key in mood_lower or mood_lower in key:
            return mood_movies[key]
    
    # Default recommendations
    return mood_movies['happy']

def analyze_mood_sentiment(mood_text):
    """
    Analyze the sentiment and context of the mood input for better recommendations.
    """
    try:
        prompt = f"""
        Analyze this mood/feeling: "{mood_text}"
        
        Categorize it into one of these primary emotions and provide reasoning:
        - Happy/Joyful
        - Sad/Melancholic  
        - Excited/Energetic
        - Romantic/Loving
        - Adventurous/Thrilling
        - Thoughtful/Contemplative
        - Nostalgic/Sentimental
        - Anxious/Tense
        
        Return only the primary emotion category (one word).
        """
        
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip().lower()
        else:
            return mood_text.lower()
            
    except Exception as e:
        print(f"Error analyzing mood: {e}")
        return mood_text.lower()
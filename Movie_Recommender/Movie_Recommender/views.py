import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
import requests
from .models import Feedback
from .utils import get_movie_suggestions_from_mood, get_enhanced_movie_suggestions_from_mood
import json

# Home page view
def Home(request):
    return render(request, 'index.html')

# Feedback submission view
def feedback(request):
    """
    Handles feedback form submission and saves feedback to the database.
    """
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Save the feedback to the database
        feedback_entry = Feedback(name=name, email=email, message=message)
        feedback_entry.save()

        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"message": "Feedback submitted successfully!"}, status=200)

        # Redirect back to the feedback page after successful submission
        return redirect('feedback')

    # Render the feedback page for GET requests
    return render(request, 'feedback.html')

# Mood-based movie recommendations view
def mood_recommendations(request):
    """
    Handles mood input and provides movie recommendations based on AI suggestions.
    """
    if request.method == 'POST':
        # Extract the user's mood from the request
        mood = request.POST.get('mood', '').strip()

        # Validate input
        if not mood:
            return HttpResponse('Mood input is required.', status=400)

        try:
            # Call the enhanced utility function to get AI recommendations based on mood
            ai_response = get_enhanced_movie_suggestions_from_mood(mood)

            # Check if AI provided recommendations
            if not ai_response:
                return HttpResponse('No recommendations available for the provided mood.', status=404)

            # Render the movie cards HTML with the recommendations
            movie_cards_html = render_enhanced_movie_cards(ai_response)

            return HttpResponse(movie_cards_html, content_type="text/html")

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return HttpResponse('An error occurred while generating recommendations. Please try again later.', status=500)

    return HttpResponse('Invalid request method.', status=405)

def fetch_movie_details(movie_name):
    """
    Fetches comprehensive movie details from OMDb API including streaming info.
    """
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={os.getenv('OMDB_API_KEY')}&plot=full"
    response = requests.get(url)
    data = response.json()

    if data.get('Response') == 'True':
        return {
            'title': data.get('Title', movie_name),
            'poster': data.get('Poster', 'https://via.placeholder.com/300x450?text=No+Image'),
            'year': data.get('Year', 'Unknown'),
            'genre': data.get('Genre', 'Unknown'),
            'director': data.get('Director', 'Unknown'),
            'actors': data.get('Actors', 'Unknown'),
            'plot': data.get('Plot', 'No plot available'),
            'rating': data.get('imdbRating', 'N/A'),
            'runtime': data.get('Runtime', 'Unknown'),
            'language': data.get('Language', 'Unknown'),
            'imdbID': data.get('imdbID', ''),
            'metascore': data.get('Metascore', 'N/A')
        }
    else:
        return {
            'title': movie_name,
            'poster': 'https://via.placeholder.com/300x450?text=No+Image',
            'year': 'Unknown',
            'genre': 'Unknown',
            'director': 'Unknown',
            'actors': 'Unknown',
            'plot': 'No information available',
            'rating': 'N/A',
            'runtime': 'Unknown',
            'language': 'Unknown',
            'imdbID': '',
            'metascore': 'N/A'
        }

def get_streaming_links(movie_title, imdb_id):
    """
    Generate streaming/download links for movies.
    """
    links = []
    
    # Popular streaming platforms
    streaming_platforms = [
        {'name': 'Netflix', 'url': f'https://www.netflix.com/search?q={movie_title.replace(" ", "%20")}', 'color': '#E50914'},
        {'name': 'Amazon Prime', 'url': f'https://www.amazon.com/s?k={movie_title.replace(" ", "+")}+movie', 'color': '#00A8E1'},
        {'name': 'Disney+', 'url': f'https://www.disneyplus.com/search/{movie_title.replace(" ", "%20")}', 'color': '#113CCF'},
        {'name': 'Hulu', 'url': f'https://www.hulu.com/search?q={movie_title.replace(" ", "%20")}', 'color': '#1CE783'},
        {'name': 'YouTube Movies', 'url': f'https://www.youtube.com/results?search_query={movie_title.replace(" ", "+")}+full+movie', 'color': '#FF0000'},
        {'name': 'IMDb', 'url': f'https://www.imdb.com/title/{imdb_id}/' if imdb_id else f'https://www.imdb.com/find?q={movie_title.replace(" ", "+")}', 'color': '#F5C518'}
    ]
    
    return streaming_platforms

def render_enhanced_movie_cards(movies):
    """
    Helper function to render enhanced HTML for movie cards with detailed information.
    """
    movie_cards_html = ''
    
    for movie in movies:
        movie_details = fetch_movie_details(movie)
        streaming_links = get_streaming_links(movie_details['title'], movie_details['imdbID'])
        
        streaming_buttons = ''.join([
            f'<a href="{link["url"]}" target="_blank" class="streaming-link" style="background-color: {link["color"]}">{link["name"]}</a>'
            for link in streaming_links
        ])
        
        movie_cards_html += f'''
        <div class="enhanced-movie-card" data-imdbid="{movie_details['imdbID']}">
            <div class="movie-poster-container">
                <img src="{movie_details['poster']}" alt="{movie_details['title']}" class="enhanced-movie-poster">
                <div class="movie-overlay">
                    <div class="movie-rating">⭐ {movie_details['rating']}</div>
                </div>
            </div>
            <div class="enhanced-movie-info">
                <h3 class="enhanced-movie-title">{movie_details['title']}</h3>
                <p class="movie-year-genre">{movie_details['year']} • {movie_details['genre']}</p>
                <p class="movie-runtime">⏱️ {movie_details['runtime']}</p>
                <p class="movie-plot">{movie_details['plot'][:100]}{'...' if len(movie_details['plot']) > 100 else ''}</p>
                <div class="streaming-links">
                    {streaming_buttons}
                </div>
            </div>
        </div>
        '''
    
    return movie_cards_html

def get_trending_movies(request):
    """
    Fetch trending/popular movies from OMDb API.
    """
    try:
        # Popular movie titles to fetch
        popular_movies = [
            "Avengers: Endgame", "Spider-Man: No Way Home", "Top Gun: Maverick",
            "Black Panther", "Dune", "The Batman", "Doctor Strange", "Thor: Love and Thunder",
            "Jurassic World Dominion", "Minions: The Rise of Gru"
        ]
        
        movie_cards_html = render_enhanced_movie_cards(popular_movies)
        return HttpResponse(movie_cards_html, content_type="text/html")
        
    except Exception as e:
        print(f"Error fetching trending movies: {e}")
        return HttpResponse('<p>Error loading trending movies.</p>', status=500)

def get_recent_movies(request):
    """
    Fetch recently released movies.
    """
    try:
        # Recent movie releases
        recent_movies = [
            "Oppenheimer", "Barbie", "Fast X", "Indiana Jones 5", "Transformers: Rise of the Beasts",
            "The Flash", "Guardians of the Galaxy Vol. 3", "John Wick: Chapter 4",
            "Scream VI", "Creed III"
        ]
        
        movie_cards_html = render_enhanced_movie_cards(recent_movies)
        return HttpResponse(movie_cards_html, content_type="text/html")
        
    except Exception as e:
        print(f"Error fetching recent movies: {e}")
        return HttpResponse('<p>Error loading recent movies.</p>', status=500)

def get_movie_details_api(request, imdb_id):
    """
    API endpoint to get detailed movie information.
    """
    try:
        url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={os.getenv('OMDB_API_KEY')}&plot=full"
        response = requests.get(url)
        data = response.json()
        
        if data.get('Response') == 'True':
            streaming_links = get_streaming_links(data.get('Title', ''), imdb_id)
            data['streaming_links'] = streaming_links
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Movie not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
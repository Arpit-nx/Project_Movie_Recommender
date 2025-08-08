import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import json
from .models import Feedback
from .utils import get_movie_suggestions_from_mood, get_enhanced_movie_suggestions_from_mood
from .supabase_client import supabase

# Home page view
def Home(request):
    return render(request, 'index.html')

# Authentication views
@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    """
    Handle user registration with Supabase Auth
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name', '')
        username = data.get('username', '')

        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)

        # Sign up user with Supabase
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "username": username
                }
            }
        })

        if response.user:
            return JsonResponse({
                'message': 'Registration successful! Please check your email for verification.',
                'user': {
                    'id': response.user.id,
                    'email': response.user.email
                }
            })
        else:
            return JsonResponse({'error': 'Registration failed'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def signin(request):
    """
    Handle user login with Supabase Auth
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)

        # Sign in user with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            return JsonResponse({
                'message': 'Login successful!',
                'user': {
                    'id': response.user.id,
                    'email': response.user.email
                },
                'session': {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def signout(request):
    """
    Handle user logout
    """
    try:
        supabase.auth.sign_out()
        return JsonResponse({'message': 'Logout successful!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_profile(request):
    """
    Get user profile information
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({'error': 'Authorization header required'}, status=401)

        token = auth_header.replace('Bearer ', '')
        
        # Get user from token
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        user_id = user_response.user.id

        # Get profile data
        profile_response = supabase.table('profiles').select('*').eq('id', user_id).execute()
        
        profile = profile_response.data[0] if profile_response.data else None

        return JsonResponse({
            'user': {
                'id': user_response.user.id,
                'email': user_response.user.email,
                'profile': profile
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Enhanced feedback submission with Supabase
@csrf_exempt
def feedback(request):
    """
    Handles feedback form submission and saves feedback to Supabase.
    """
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            name = data.get('name')
            email = data.get('email')
            message = data.get('message')
            rating = int(data.get('rating', 5))

            if not all([name, email, message]):
                return JsonResponse({'error': 'All fields are required'}, status=400)

            # Get user ID if authenticated
            user_id = None
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.replace('Bearer ', '')
                    user_response = supabase.auth.get_user(token)
                    if user_response.user:
                        user_id = user_response.user.id
                except:
                    pass  # Continue as anonymous user

            # Save feedback to Supabase
            feedback_data = {
                'name': name,
                'email': email,
                'message': message,
                'rating': rating,
                'user_id': user_id
            }

            response = supabase.table('feedback').insert(feedback_data).execute()

            if response.data:
                return JsonResponse({
                    'message': 'Feedback submitted successfully!',
                    'feedback_id': response.data[0]['id']
                })
            else:
                return JsonResponse({'error': 'Failed to submit feedback'}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Render the feedback page for GET requests
    return render(request, 'feedback.html')

# Track user movie interactions
@csrf_exempt
@require_http_methods(["POST"])
def track_movie_interaction(request):
    """
    Track user interactions with movies (viewed, liked, watchlist)
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        token = auth_header.replace('Bearer ', '')
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        data = json.loads(request.body)
        movie_title = data.get('movie_title')
        imdb_id = data.get('imdb_id')
        interaction_type = data.get('interaction_type')  # 'viewed', 'liked', 'watchlist'
        mood_context = data.get('mood_context', '')

        if not all([movie_title, interaction_type]):
            return JsonResponse({'error': 'Movie title and interaction type are required'}, status=400)

        # Check if interaction already exists
        existing = supabase.table('user_movie_interactions').select('*').eq('user_id', user_response.user.id).eq('movie_title', movie_title).eq('interaction_type', interaction_type).execute()

        if existing.data:
            return JsonResponse({'message': 'Interaction already recorded'})

        # Insert new interaction
        interaction_data = {
            'user_id': user_response.user.id,
            'movie_title': movie_title,
            'imdb_id': imdb_id,
            'interaction_type': interaction_type,
            'mood_context': mood_context
        }

        response = supabase.table('user_movie_interactions').insert(interaction_data).execute()

        if response.data:
            return JsonResponse({'message': 'Interaction tracked successfully'})
        else:
            return JsonResponse({'error': 'Failed to track interaction'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Get user's movie history and recommendations
@csrf_exempt
@require_http_methods(["GET"])
def get_user_recommendations(request):
    """
    Get personalized recommendations based on user's movie history
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        token = auth_header.replace('Bearer ', '')
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # Get user's movie interactions
        interactions = supabase.table('user_movie_interactions').select('*').eq('user_id', user_response.user.id).order('created_at', desc=True).limit(20).execute()

        # Get user's liked movies for better recommendations
        liked_movies = [interaction['movie_title'] for interaction in interactions.data if interaction['interaction_type'] == 'liked']
        
        # Generate personalized recommendations based on liked movies
        if liked_movies:
            # Use AI to generate recommendations based on user's preferences
            prompt = f"Based on these movies the user liked: {', '.join(liked_movies[:5])}, recommend 8 similar movies they might enjoy."
            try:
                from .utils import get_enhanced_movie_suggestions_from_mood
                recommendations = get_enhanced_movie_suggestions_from_mood(f"movies similar to {', '.join(liked_movies[:3])}")
            except:
                recommendations = ["The Shawshank Redemption", "The Godfather", "Pulp Fiction", "The Dark Knight", "Forrest Gump", "Inception", "The Matrix", "Goodfellas"]
        else:
            # Default popular recommendations for new users
            recommendations = ["The Shawshank Redemption", "The Godfather", "Pulp Fiction", "The Dark Knight", "Forrest Gump", "Inception", "The Matrix", "Goodfellas"]

        return JsonResponse({
            'recommendations': recommendations,
            'user_history': interactions.data,
            'liked_count': len(liked_movies)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Mood-based movie recommendations view (enhanced with user tracking)
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

            # Track mood search if user is authenticated
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.replace('Bearer ', '')
                    user_response = supabase.auth.get_user(token)
                    if user_response.user:
                        # Track each recommended movie as viewed with mood context
                        for movie in ai_response[:3]:  # Track first 3 recommendations
                            try:
                                supabase.table('user_movie_interactions').insert({
                                    'user_id': user_response.user.id,
                                    'movie_title': movie,
                                    'interaction_type': 'viewed',
                                    'mood_context': mood
                                }).execute()
                            except:
                                pass  # Continue if tracking fails
                except:
                    pass  # Continue as anonymous user

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
                <div class="movie-actions">
                    <button class="action-btn like-btn" data-movie="{movie_details['title']}" data-imdb="{movie_details['imdbID']}">❤️</button>
                    <button class="action-btn watchlist-btn" data-movie="{movie_details['title']}" data-imdb="{movie_details['imdbID']}">📋</button>
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
            
            # Track movie view if user is authenticated
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.replace('Bearer ', '')
                    user_response = supabase.auth.get_user(token)
                    if user_response.user:
                        supabase.table('user_movie_interactions').insert({
                            'user_id': user_response.user.id,
                            'movie_title': data.get('Title', ''),
                            'imdb_id': imdb_id,
                            'interaction_type': 'viewed'
                        }).execute()
                except:
                    pass  # Continue if tracking fails
            
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Movie not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
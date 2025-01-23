import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
import requests
from .models import Feedback
from .utils import get_movie_suggestions_from_mood  # Import your AI suggestion utility

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
            # Call the utility function to get AI recommendations based on mood
            ai_response = get_movie_suggestions_from_mood(mood)

            # Check if AI provided recommendations
            if not ai_response:
                return HttpResponse('No recommendations available for the provided mood.', status=404)

            # Render the movie cards HTML with the recommendations
            movie_cards_html = render_movie_cards(ai_response)

            return HttpResponse(movie_cards_html, content_type="text/html")

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return HttpResponse('An error occurred while generating recommendations. Please try again later.', status=500)

    return HttpResponse('Invalid request method.', status=405)

def fetch_movie_poster(movie_name):
    """
    Fetches the movie poster and year from OMDb API based on the movie title.
    """
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={os.getenv('OMDB_API_KEY')}"
    response = requests.get(url)
    data = response.json()

    if data.get('Response') == 'True':
        poster = data.get('Poster', 'https://via.placeholder.com/200x300?text=No+Image')
        year = data.get('Year', 'Unknown')
        return poster, year
    else:
        return 'https://via.placeholder.com/200x300?text=No+Image', 'Unknown'

def render_movie_cards(movies):
    """
    Helper function to render HTML for movie cards from the movie titles.
    This includes a movie title, poster image, and year of release.
    """
    movie_cards_html = ''.join(
        f'''
        <div class="movie-card">
            <img src="{fetch_movie_poster(movie)[0]}" alt="{movie}" class="movie-poster">
            <div class="movie-info">
                <h3 class="movie-title">{movie}</h3>
                <p class="movie-year">Year: {fetch_movie_poster(movie)[1]}</p>
            </div>
        </div>
        '''
        for movie in movies
    )
    return movie_cards_html

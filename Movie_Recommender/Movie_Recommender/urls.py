"""
URL configuration for Movie_Recommender project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Movie_Recommender import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.Home, name='home'),
    path('feedback/', views.feedback, name='feedback'),
    path('mood-recommendations/', views.mood_recommendations, name='mood_recommendations'),
    path('trending-movies/', views.get_trending_movies, name='trending_movies'),
    path('recent-movies/', views.get_recent_movies, name='recent_movies'),
    path('movie-details/<str:imdb_id>/', views.get_movie_details_api, name='movie_details_api'),
]
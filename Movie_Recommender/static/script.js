// API key for OMDb API
const API_KEY = '35dbc24e';
const BASE_URL = 'https://www.omdbapi.com/';

// Select DOM elements
const searchBox = document.getElementById('movie-search');
const searchButton = document.getElementById('search-button');
const movieResults = document.getElementById('movie-results');
const genreButtons = document.querySelectorAll('.genre');
const moodInput = document.getElementById('mood-search');
const moodSearchButton = document.getElementById('mood-search-button');

// Tab functionality
document.addEventListener('DOMContentLoaded', function() {
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Load content based on tab
            if (targetTab === 'trending') {
                loadTrendingMovies();
            } else if (targetTab === 'recent') {
                loadRecentMovies();
            }
        });
    });
    
    // Load trending movies by default
    loadTrendingMovies();
});

// Function to show a loading spinner
function showLoading() {
    movieResults.innerHTML = `
        <div class="loading-spinner">
            <div>Loading amazing movies for you...</div>
        </div>
    `;
}

// Function to hide the loading spinner
function hideLoading() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.remove();
}

// Function to get CSRF token
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Function to fetch movies based on a query
async function fetchMovies(query) {
    showLoading();
    try {
        const response = await fetch(`${BASE_URL}?s=${query}&apikey=${API_KEY}`);
        const data = await response.json();
        hideLoading();
        if (data.Response === "True") {
            displayMovies(data.Search);
        } else {
            movieResults.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <h3>No results found for "${query}"</h3>
                    <p>Try searching with different keywords or check the spelling.</p>
                </div>
            `;
        }
    } catch (error) {
        hideLoading();
        console.error("Error fetching movies:", error);
        movieResults.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ff6b6b;">
                <h3>Oops! Something went wrong</h3>
                <p>Please check your internet connection and try again.</p>
            </div>
        `;
    }
}

// Function to fetch movies based on genre
async function fetchMoviesByGenre(genre) {
    showLoading();
    try {
        const query = `${genre} movies`;
        const response = await fetch(`${BASE_URL}?s=${query}&apikey=${API_KEY}`);
        const data = await response.json();
        hideLoading();
        if (data.Response === "True") {
            displayMovies(data.Search);
        } else {
            movieResults.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <h3>No ${genre} movies found</h3>
                    <p>Try another genre or refine your search.</p>
                </div>
            `;
        }
    } catch (error) {
        hideLoading();
        console.error("Error fetching movies by genre:", error);
        movieResults.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ff6b6b;">
                <h3>Error loading ${genre} movies</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// Load trending movies
async function loadTrendingMovies() {
    showLoading();
    try {
        const response = await fetch('/trending-movies/');
        const htmlContent = await response.text();
        hideLoading();
        movieResults.innerHTML = htmlContent;
        addMovieCardListeners();
    } catch (error) {
        hideLoading();
        console.error("Error loading trending movies:", error);
        movieResults.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ff6b6b;">
                <h3>Error loading trending movies</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// Load recent movies
async function loadRecentMovies() {
    showLoading();
    try {
        const response = await fetch('/recent-movies/');
        const htmlContent = await response.text();
        hideLoading();
        movieResults.innerHTML = htmlContent;
        addMovieCardListeners();
    } catch (error) {
        hideLoading();
        console.error("Error loading recent movies:", error);
        movieResults.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ff6b6b;">
                <h3>Error loading recent movies</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// Fetch detailed information about a movie
async function getMovieDetails(imdbID) {
    try {
        const response = await fetch(`/movie-details/${imdbID}/`);
        const data = await response.json();
        if (response.ok) {
            showEnhancedMovieDetails(data);
        } else {
            alert("Movie details not found.");
        }
    } catch (error) {
        console.error("Error fetching movie details:", error);
        alert("An error occurred. Please try again.");
    }
}

// Display enhanced movie details in a modal
function showEnhancedMovieDetails(movie) {
    const modal = document.getElementById("movie-modal");
    const modalContent = document.getElementById("modal-content");

    const streamingLinksHtml = movie.streaming_links ? 
        movie.streaming_links.map(link => 
            `<a href="${link.url}" target="_blank" class="streaming-link" style="background-color: ${link.color}">${link.name}</a>`
        ).join('') : '';

    modalContent.innerHTML = `
        <div class="modal-header">
            <h2>${movie.Title}</h2>
            <button id="close-modal">×</button>
        </div>
        <div class="modal-body">
            <img 
                src="${movie.Poster !== "N/A" ? movie.Poster : 'https://via.placeholder.com/300x450?text=No+Image'}" 
                alt="${movie.Title}" 
                class="modal-poster"
            >
            <div class="modal-info">
                <p><strong>Year:</strong> ${movie.Year}</p>
                <p><strong>Genre:</strong> ${movie.Genre}</p>
                <p><strong>Director:</strong> ${movie.Director}</p>
                <p><strong>Actors:</strong> ${movie.Actors}</p>
                <p><strong>Runtime:</strong> ${movie.Runtime}</p>
                <p><strong>Language:</strong> ${movie.Language}</p>
                <p><strong>IMDB Rating:</strong> ⭐ ${movie.imdbRating}</p>
                <p><strong>Metascore:</strong> ${movie.Metascore}</p>
                <p><strong>Plot:</strong> ${movie.Plot}</p>
                <div style="margin-top: 20px;">
                    <strong>Watch/Download:</strong>
                    <div class="streaming-links" style="margin-top: 10px;">
                        ${streamingLinksHtml}
                    </div>
                </div>
            </div>
        </div>
    `;

    modal.style.display = "block";

    document.getElementById("close-modal").addEventListener("click", () => {
        modal.style.display = "none";
    });

    // Close modal when clicking outside
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });
}

// Add event listener for movie cards
function addMovieCardListeners() {
    const movieCards = document.querySelectorAll(".movie-card, .enhanced-movie-card");
    movieCards.forEach(card => {
        card.addEventListener("click", () => {
            const imdbID = card.getAttribute("data-imdbid");
            if (imdbID) {
                getMovieDetails(imdbID);
            }
        });
    });
}

// Display movies in the results container
function displayMovies(movies) {
    movieResults.innerHTML = movies
        .map(
            movie => `
            <div class="movie-card" data-imdbid="${movie.imdbID}">
                <img 
                    src="${movie.Poster !== "N/A" ? movie.Poster : 'https://via.placeholder.com/300x450?text=No+Image'}" 
                    alt="${movie.Title}" 
                    class="movie-poster"
                >
                <div class="movie-info">
                    <h3 class="movie-title">${movie.Title}</h3>
                    <p class="movie-year">Year: ${movie.Year}</p>
                </div>
            </div>
        `).join('');

    addMovieCardListeners();
}

// Event listeners for searching movies
if (searchButton) {
    searchButton.addEventListener('click', () => {
        const query = searchBox.value.trim();
        if (query) {
            fetchMovies(query);
        } else {
            alert("Please enter a movie name.");
        }
    });
}

// Allow Enter key for search
if (searchBox) {
    searchBox.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchBox.value.trim();
            if (query) {
                fetchMovies(query);
            }
        }
    });
}

// Event listeners for genre-based searches
genreButtons.forEach(button => {
    button.addEventListener('click', () => {
        const genre = button.getAttribute('data-genre');
        fetchMoviesByGenre(genre);
    });
});

// Function to fetch movie recommendations based on mood
async function fetchMovieRecommendations(mood) {
    showLoading();
    try {
        const formData = new FormData();
        formData.append('mood', mood);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        const response = await fetch('/mood-recommendations/', {
            method: 'POST',
            body: formData,
        });

        const htmlResponse = await response.text();
        hideLoading();

        if (response.ok) {
            movieResults.innerHTML = htmlResponse;
            addMovieCardListeners();
        } else {
            movieResults.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #ff6b6b;">
                    <h3>Error getting recommendations</h3>
                    <p>${htmlResponse}</p>
                </div>
            `;
        }
    } catch (error) {
        hideLoading();
        console.error("Error fetching movie recommendations:", error);
        movieResults.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ff6b6b;">
                <h3>Something went wrong</h3>
                <p>Please check your connection and try again.</p>
            </div>
        `;
    }
}

// Event listener for mood-based recommendations
if (moodSearchButton) {
    moodSearchButton.addEventListener('click', (e) => {
        e.preventDefault();
        const mood = moodInput.value.trim();
        if (mood) {
            fetchMovieRecommendations(mood);
        } else {
            alert("Please enter your mood.");
        }
    });
}

// Allow Enter key for mood search
if (moodInput) {
    moodInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const mood = moodInput.value.trim();
            if (mood) {
                fetchMovieRecommendations(mood);
            }
        }
    });
}

// Mood suggestions functionality
document.addEventListener('DOMContentLoaded', function() {
    const moodSuggestions = document.querySelectorAll('.mood-suggestion');
    moodSuggestions.forEach(suggestion => {
        suggestion.addEventListener('click', () => {
            const mood = suggestion.textContent.trim();
            if (moodInput) {
                moodInput.value = mood;
                fetchMovieRecommendations(mood);
            }
        });
    });
});

// Enhanced error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
});

// Add smooth scrolling to results
function scrollToResults() {
    movieResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Modify existing functions to include smooth scrolling
const originalFetchMovies = fetchMovies;
fetchMovies = async function(query) {
    await originalFetchMovies(query);
    setTimeout(scrollToResults, 500);
};

const originalFetchMoviesByGenre = fetchMoviesByGenre;
fetchMoviesByGenre = async function(genre) {
    await originalFetchMoviesByGenre(genre);
    setTimeout(scrollToResults, 500);
};

const originalFetchMovieRecommendations = fetchMovieRecommendations;
fetchMovieRecommendations = async function(mood) {
    await originalFetchMovieRecommendations(mood);
    setTimeout(scrollToResults, 500);
};
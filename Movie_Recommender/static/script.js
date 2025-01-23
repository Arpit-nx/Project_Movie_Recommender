// API key for OMDb API
const API_KEY = '35dbc24e';
const BASE_URL = 'https://www.omdbapi.com/';

// Select DOM elements
const searchBox = document.getElementById('movie-search');
const searchButton = document.getElementById('search-button');
const movieResults = document.getElementById('movie-results');
const genreButtons = document.querySelectorAll('.genre');
const moodInput = document.getElementById('mood-input'); // Text input for mood
const moodSearchButton = document.getElementById('mood-search-button');

// Function to show a loading spinner
function showLoading() {
    movieResults.innerHTML = `<div class="loading-spinner">Loading...</div>`;
}

// Function to hide the loading spinner
function hideLoading() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.remove();
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
            movieResults.innerHTML = `<p>No results found for "${query}".</p>`;
        }
    } catch (error) {
        hideLoading();
        console.error("Error fetching movies:", error);
        movieResults.innerHTML = `<p>An error occurred. Please try again later.</p>`;
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
            movieResults.innerHTML = `<p>No results found for "${genre}". Try another genre or refine your search.</p>`;
        }
    } catch (error) {
        hideLoading();
        console.error("Error fetching movies by genre:", error);
        movieResults.innerHTML = `<p>An error occurred. Please try again later.</p>`;
    }
}

// Fetch detailed information about a movie
async function getMovieDetails(imdbID) {
    try {
        const response = await fetch(`${BASE_URL}?i=${imdbID}&apikey=${API_KEY}`);
        const data = await response.json();
        if (data.Response === "True") {
            showMovieDetails(data);
        } else {
            alert("Movie details not found.");
        }
    } catch (error) {
        console.error("Error fetching movie details:", error);
        alert("An error occurred. Please try again.");
    }
}

// Display movie details in a modal
function showMovieDetails(movie) {
    const modal = document.getElementById("movie-modal");
    const modalContent = document.getElementById("modal-content");

    modalContent.innerHTML = `
        <div class="modal-header">
            <h2>${movie.Title}</h2>
            <button id="close-modal">×</button>
        </div>
        <div class="modal-body">
            <img 
                src="${movie.Poster !== "N/A" ? movie.Poster : 'https://via.placeholder.com/200x300?text=No+Image'}" 
                alt="${movie.Title}" 
                class="modal-poster"
            >
            <div class="modal-info">
                <p><strong>Year:</strong> ${movie.Year}</p>
                <p><strong>Genre:</strong> ${movie.Genre}</p>
                <p><strong>Director:</strong> ${movie.Director}</p>
                <p><strong>Actors:</strong> ${movie.Actors}</p>
                <p><strong>Plot:</strong> ${movie.Plot}</p>
                <p><strong>IMDB Rating:</strong> ${movie.imdbRating}</p>
            </div>
        </div>
    `;

    modal.style.display = "block";

    document.getElementById("close-modal").addEventListener("click", () => {
        modal.style.display = "none";
    });
}

// Add event listener for movie cards
function addMovieCardListeners() {
    const movieCards = document.querySelectorAll(".movie-card");
    movieCards.forEach(card => {
        card.addEventListener("click", () => {
            const imdbID = card.getAttribute("data-imdbid");
            getMovieDetails(imdbID);
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
                    src="${movie.Poster !== "N/A" ? movie.Poster : 'https://via.placeholder.com/200x300?text=No+Image'}" 
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
searchButton.addEventListener('click', () => {
    const query = searchBox.value.trim();
    if (query) {
        fetchMovies(query);
    } else {
        alert("Please enter a movie name.");
    }
});

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
        const response = await fetch('/mood-recommendations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(), // Add CSRF token if needed
            },
            body: JSON.stringify({ mood }), // Send the mood as JSON
        });

        const htmlResponse = await response.text();  // Read the HTML response

        hideLoading();

        if (response.ok) {
            // Directly inject the returned HTML into the results container
            movieResults.innerHTML = htmlResponse;
            // Optional: Add click listeners for new movie cards if needed
            addMovieCardListeners();
        } else {
            movieResults.innerHTML = `<p>${htmlResponse}</p>`;
        }
    } catch (error) {
        hideLoading();
        console.error("Error fetching movie recommendations:", error);
        movieResults.innerHTML = `<p>An error occurred. Please try again later.</p>`;
    }
}

// Event listener for mood-based recommendations
moodSearchButton.addEventListener('click', () => {
    const mood = moodInput.value.trim();
    if (mood) {
        fetchMovieRecommendations(mood);
    } else {
        alert("Please enter your mood.");
    }
});

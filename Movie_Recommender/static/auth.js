// Authentication functionality
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthState();
    }

    bindEvents() {
        // Auth modal controls
        document.getElementById('login-btn')?.addEventListener('click', () => this.showAuthModal('login'));
        document.getElementById('signup-btn')?.addEventListener('click', () => this.showAuthModal('signup'));
        document.getElementById('logout-btn')?.addEventListener('click', () => this.logout());
        document.getElementById('close-auth-modal')?.addEventListener('click', () => this.hideAuthModal());
        
        // Auth form
        document.getElementById('auth-form')?.addEventListener('submit', (e) => this.handleAuthSubmit(e));
        document.getElementById('auth-switch-btn')?.addEventListener('click', () => this.switchAuthMode());

        // Close modal on outside click
        document.getElementById('auth-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'auth-modal') {
                this.hideAuthModal();
            }
        });
    }

    async checkAuthState() {
        if (!supabase) return;

        try {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                this.setUser(session.user);
            }
        } catch (error) {
            console.error('Error checking auth state:', error);
        }
    }

    showAuthModal(mode = 'login') {
        const modal = document.getElementById('auth-modal');
        const title = document.getElementById('auth-modal-title');
        const submitBtn = document.getElementById('auth-submit-btn');
        const signupFields = document.getElementById('signup-fields');
        const switchText = document.getElementById('auth-switch-text');
        const switchBtn = document.getElementById('auth-switch-btn');

        if (mode === 'signup') {
            title.textContent = 'Sign Up';
            submitBtn.textContent = 'Sign Up';
            signupFields.style.display = 'block';
            switchText.textContent = 'Already have an account?';
            switchBtn.textContent = 'Login';
            modal.dataset.mode = 'signup';
        } else {
            title.textContent = 'Login';
            submitBtn.textContent = 'Login';
            signupFields.style.display = 'none';
            switchText.textContent = "Don't have an account?";
            switchBtn.textContent = 'Sign Up';
            modal.dataset.mode = 'login';
        }

        modal.style.display = 'flex';
    }

    hideAuthModal() {
        document.getElementById('auth-modal').style.display = 'none';
        document.getElementById('auth-form').reset();
    }

    switchAuthMode() {
        const modal = document.getElementById('auth-modal');
        const currentMode = modal.dataset.mode;
        this.showAuthModal(currentMode === 'login' ? 'signup' : 'login');
    }

    async handleAuthSubmit(e) {
        e.preventDefault();
        
        if (!supabase) {
            this.showMessage('Supabase not configured', 'error');
            return;
        }

        const modal = document.getElementById('auth-modal');
        const mode = modal.dataset.mode;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            if (mode === 'signup') {
                const fullName = document.getElementById('full-name').value;
                const username = document.getElementById('username').value;

                const { data, error } = await supabase.auth.signUp({
                    email,
                    password,
                    options: {
                        data: {
                            full_name: fullName,
                            username: username
                        }
                    }
                });

                if (error) throw error;

                this.showMessage('Registration successful! Please check your email for verification.', 'success');
                this.hideAuthModal();
            } else {
                const { data, error } = await supabase.auth.signInWithPassword({
                    email,
                    password
                });

                if (error) throw error;

                this.setUser(data.user);
                this.showMessage('Login successful!', 'success');
                this.hideAuthModal();
            }
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    async logout() {
        if (!supabase) return;

        try {
            const { error } = await supabase.auth.signOut();
            if (error) throw error;

            this.setUser(null);
            this.showMessage('Logged out successfully!', 'success');
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    setUser(user) {
        this.currentUser = user;
        const authButtons = document.getElementById('auth-buttons');
        const userInfo = document.getElementById('user-info');
        const userEmail = document.getElementById('user-email');
        const personalTab = document.getElementById('personal-tab');

        if (user) {
            authButtons.style.display = 'none';
            userInfo.style.display = 'flex';
            userEmail.textContent = user.email;
            personalTab.style.display = 'block';
            
            // Load personal recommendations
            this.loadPersonalRecommendations();
        } else {
            authButtons.style.display = 'flex';
            userInfo.style.display = 'none';
            personalTab.style.display = 'none';
        }
    }

    async loadPersonalRecommendations() {
        if (!this.currentUser) return;

        try {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const response = await fetch('/api/user/recommendations/', {
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayPersonalRecommendations(data);
            }
        } catch (error) {
            console.error('Error loading personal recommendations:', error);
        }
    }

    displayPersonalRecommendations(data) {
        const personalStats = document.getElementById('personal-stats');
        const movieResults = document.getElementById('movie-results');

        // Display user stats
        personalStats.innerHTML = `
            <div class="stats-container">
                <div class="stat-item">
                    <span class="stat-number">${data.liked_count}</span>
                    <span class="stat-label">Movies Liked</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${data.user_history.length}</span>
                    <span class="stat-label">Movies Viewed</span>
                </div>
            </div>
        `;

        // Display recommendations if on personal tab
        const personalTab = document.getElementById('personal');
        if (personalTab.classList.contains('active')) {
            this.renderMovieCards(data.recommendations);
        }
    }

    async renderMovieCards(movies) {
        const movieResults = document.getElementById('movie-results');
        movieResults.innerHTML = '<div class="loading-spinner">Loading your personalized recommendations...</div>';

        try {
            // Fetch detailed movie information for each recommendation
            const movieCards = await Promise.all(movies.map(async (movie) => {
                try {
                    const response = await fetch(`http://www.omdbapi.com/?t=${encodeURIComponent(movie)}&apikey=35dbc24e&plot=full`);
                    const data = await response.json();
                    
                    if (data.Response === 'True') {
                        return this.createMovieCard(data);
                    }
                } catch (error) {
                    console.error(`Error fetching details for ${movie}:`, error);
                }
                return null;
            }));

            const validCards = movieCards.filter(card => card !== null);
            movieResults.innerHTML = validCards.join('');
            
            // Add event listeners to new cards
            this.addMovieCardListeners();
        } catch (error) {
            console.error('Error rendering movie cards:', error);
            movieResults.innerHTML = '<p>Error loading recommendations.</p>';
        }
    }

    createMovieCard(movie) {
        const streamingLinks = [
            { name: 'Netflix', url: `https://www.netflix.com/search?q=${encodeURIComponent(movie.Title)}`, color: '#E50914' },
            { name: 'Amazon Prime', url: `https://www.amazon.com/s?k=${encodeURIComponent(movie.Title)}+movie`, color: '#00A8E1' },
            { name: 'IMDb', url: `https://www.imdb.com/title/${movie.imdbID}/`, color: '#F5C518' }
        ];

        const streamingButtons = streamingLinks.map(link => 
            `<a href="${link.url}" target="_blank" class="streaming-link" style="background-color: ${link.color}">${link.name}</a>`
        ).join('');

        return `
            <div class="enhanced-movie-card" data-imdbid="${movie.imdbID}">
                <div class="movie-poster-container">
                    <img src="${movie.Poster !== 'N/A' ? movie.Poster : 'https://via.placeholder.com/300x450?text=No+Image'}" 
                         alt="${movie.Title}" class="enhanced-movie-poster">
                    <div class="movie-overlay">
                        <div class="movie-rating">⭐ ${movie.imdbRating}</div>
                    </div>
                    <div class="movie-actions">
                        <button class="action-btn like-btn" data-movie="${movie.Title}" data-imdb="${movie.imdbID}">❤️</button>
                        <button class="action-btn watchlist-btn" data-movie="${movie.Title}" data-imdb="${movie.imdbID}">📋</button>
                    </div>
                </div>
                <div class="enhanced-movie-info">
                    <h3 class="enhanced-movie-title">${movie.Title}</h3>
                    <p class="movie-year-genre">${movie.Year} • ${movie.Genre}</p>
                    <p class="movie-runtime">⏱️ ${movie.Runtime}</p>
                    <p class="movie-plot">${movie.Plot.length > 100 ? movie.Plot.substring(0, 100) + '...' : movie.Plot}</p>
                    <div class="streaming-links">
                        ${streamingButtons}
                    </div>
                </div>
            </div>
        `;
    }

    addMovieCardListeners() {
        // Add click listeners for movie cards
        document.querySelectorAll('.enhanced-movie-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.action-btn') && !e.target.closest('.streaming-link')) {
                    const imdbId = card.dataset.imdbid;
                    if (imdbId) {
                        this.trackMovieInteraction(card.dataset.movie || '', imdbId, 'viewed');
                        // Trigger movie details modal (assuming it exists)
                        if (typeof getMovieDetails === 'function') {
                            getMovieDetails(imdbId);
                        }
                    }
                }
            });
        });

        // Add listeners for action buttons
        document.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const movie = btn.dataset.movie;
                const imdbId = btn.dataset.imdb;
                this.trackMovieInteraction(movie, imdbId, 'liked');
                btn.classList.toggle('active');
            });
        });

        document.querySelectorAll('.watchlist-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const movie = btn.dataset.movie;
                const imdbId = btn.dataset.imdb;
                this.trackMovieInteraction(movie, imdbId, 'watchlist');
                btn.classList.toggle('active');
            });
        });
    }

    async trackMovieInteraction(movieTitle, imdbId, interactionType) {
        if (!this.currentUser || !supabase) return;

        try {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            await fetch('/api/movies/track/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                    movie_title: movieTitle,
                    imdb_id: imdbId,
                    interaction_type: interactionType
                })
            });
        } catch (error) {
            console.error('Error tracking movie interaction:', error);
        }
    }

    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('auth-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'auth-message';
            messageEl.className = 'auth-message';
            document.body.appendChild(messageEl);
        }

        messageEl.textContent = message;
        messageEl.className = `auth-message ${type}`;
        messageEl.style.display = 'block';

        // Auto-hide after 3 seconds
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 3000);
    }

    getAuthToken() {
        return supabase?.auth.getSession().then(({ data: { session } }) => session?.access_token);
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});

// Listen for auth state changes
if (supabase) {
    supabase.auth.onAuthStateChange((event, session) => {
        if (window.authManager) {
            window.authManager.setUser(session?.user || null);
        }
    });
}
class PropertySearch {
    constructor() {
        this.form = document.querySelector('.search-form');
        this.resultsContainer = document.querySelector('.property-grid');
        this.filters = document.querySelector('.property-filters');
        this.searchInput = document.querySelector('#search-input');
        this.locationInput = document.querySelector('#location-input');
        this.useLocationBtn = document.querySelector('#use-location-btn');
        this.autocompleteResults = document.querySelector('#autocomplete-results');
        this.currentLocation = null;
        
        this.priceRange = {
            min: document.querySelector('#min-price'),
            max: document.querySelector('#max-price')
        };
        this.propertyType = document.querySelector('#property-type');
        this.listingType = document.querySelector('#listing-type');
        this.bedrooms = document.querySelector('#bedrooms');
        this.bathrooms = document.querySelector('#bathrooms');
        
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMoreResults = true;
        
        this.init();
    }
    
    init() {
        // Initialize range sliders
        if (this.priceRange.min && this.priceRange.max) {
            this.initializePriceRange();
        }
        
        // Add event listeners
        if (this.searchInput) {
            this.searchInput.addEventListener('input', debounce(() => this.handleSearch(), 500));
        }
        
        if (this.locationInput) {
            this.locationInput.addEventListener('input', debounce(() => this.handleLocationInput(), 300));
            this.locationInput.addEventListener('focus', () => this.showAutocomplete());
            document.addEventListener('click', (e) => this.handleClickOutside(e));
        }
        
        if (this.useLocationBtn) {
            this.useLocationBtn.addEventListener('click', () => this.getCurrentLocation());
        }
        
        if (this.filters) {
            const filterInputs = this.filters.querySelectorAll('select, input[type="number"]');
            filterInputs.forEach(input => {
                input.addEventListener('change', () => this.handleSearch());
            });
        }
        
        // Initialize infinite scroll
        window.addEventListener('scroll', () => this.handleScroll());
        
        // Handle form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }
    
    initializePriceRange() {
        const minValue = parseInt(this.priceRange.min.dataset.min);
        const maxValue = parseInt(this.priceRange.max.dataset.max);
        
        noUiSlider.create(this.priceRange.min.parentElement, {
            start: [minValue, maxValue],
            connect: true,
            step: 1000,
            range: {
                'min': minValue,
                'max': maxValue
            },
            format: {
                to: value => Math.round(value),
                from: value => Math.round(value)
            }
        });
        
        this.priceRange.min.parentElement.noUiSlider.on('update', (values, handle) => {
            this.priceRange.min.value = values[0];
            this.priceRange.max.value = values[1];
            this.handleSearch();
        });
    }
    
    async handleSearch() {
        this.currentPage = 1;
        this.hasMoreResults = true;
        await this.fetchResults();
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        await this.handleSearch();
    }
    
    handleScroll() {
        if (this.isLoading || !this.hasMoreResults) return;
        
        const scrollPos = window.innerHeight + window.scrollY;
        const pageBottom = document.documentElement.offsetHeight - 200;
        
        if (scrollPos >= pageBottom) {
            this.currentPage++;
            this.fetchResults(true);
        }
    }
    
    async handleLocationInput() {
        const query = this.locationInput.value.trim();
        if (query.length < 3) {
            this.hideAutocomplete();
            return;
        }
        
        try {
            const response = await fetchData(`/api/locations/autocomplete/?query=${encodeURIComponent(query)}`);
            this.showAutocompleteResults(response.suggestions);
        } catch (error) {
            console.error('Error fetching location suggestions:', error);
        }
    }
    
    showAutocompleteResults(suggestions) {
        if (!this.autocompleteResults) return;
        
        this.autocompleteResults.innerHTML = '';
        if (suggestions.length === 0) {
            this.hideAutocomplete();
            return;
        }
        
        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';
            div.textContent = suggestion.description;
            div.addEventListener('click', () => {
                this.locationInput.value = suggestion.description;
                this.currentLocation = {
                    lat: suggestion.latitude,
                    lng: suggestion.longitude
                };
                this.hideAutocomplete();
                this.handleSearch();
            });
            this.autocompleteResults.appendChild(div);
        });
        
        this.showAutocomplete();
    }
    
    showAutocomplete() {
        if (this.autocompleteResults) {
            this.autocompleteResults.style.display = 'block';
        }
    }
    
    hideAutocomplete() {
        if (this.autocompleteResults) {
            this.autocompleteResults.style.display = 'none';
        }
    }
    
    handleClickOutside(event) {
        if (!this.locationInput.contains(event.target) && 
            !this.autocompleteResults.contains(event.target)) {
            this.hideAutocomplete();
        }
    }
    
    async getCurrentLocation() {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }
        
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject);
            });
            
            this.currentLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            
            // Get address from coordinates
            const response = await fetchData(
                `/api/locations/reverse-geocode/?lat=${this.currentLocation.lat}&lng=${this.currentLocation.lng}`
            );
            
            this.locationInput.value = response.address;
            this.handleSearch();
            
        } catch (error) {
            console.error('Error getting location:', error);
            alert('Unable to get your location. Please enter it manually.');
        }
    }
    
    getFilterValues() {
        const filters = {
            query: this.searchInput ? this.searchInput.value : '',
            property_type: this.propertyType ? this.propertyType.value : '',
            listing_type: this.listingType ? this.listingType.value : '',
            min_price: this.priceRange.min ? this.priceRange.min.value : '',
            max_price: this.priceRange.max ? this.priceRange.max.value : '',
            bedrooms: this.bedrooms ? this.bedrooms.value : '',
            bathrooms: this.bathrooms ? this.bathrooms.value : '',
            page: this.currentPage
        };
        
        if (this.currentLocation) {
            filters.latitude = this.currentLocation.lat;
            filters.longitude = this.currentLocation.lng;
        }
        
        return filters;
    }
    
    async fetchResults(append = false) {
        this.isLoading = true;
        this.toggleLoadingState(true);
        
        try {
            const params = new URLSearchParams(this.getFilterValues());
            const response = await fetchData(`/api/properties/filter/?${params}`);
            
            if (!append) {
                this.resultsContainer.innerHTML = '';
            }
            
            if (response.properties.length === 0) {
                this.hasMoreResults = false;
                if (!append) {
                    this.showNoResults();
                }
            } else {
                this.renderResults(response.properties);
            }
            
        } catch (error) {
            console.error('Error fetching results:', error);
            this.showError();
        } finally {
            this.isLoading = false;
            this.toggleLoadingState(false);
        }
    }
    
    renderResults(properties) {
        properties.forEach(property => {
            const propertyCard = this.createPropertyCard(property);
            this.resultsContainer.appendChild(propertyCard);
        });
        
        // Initialize new favorite buttons
        const newFavoriteButtons = this.resultsContainer.querySelectorAll('.favorite-button:not(.initialized)');
        newFavoriteButtons.forEach(button => {
            new PropertyFavorite(button);
            button.classList.add('initialized');
        });
    }
    
    createPropertyCard(property) {
        const card = document.createElement('div');
        card.className = 'property-card';
        card.innerHTML = `
            <div class="property-image">
                <img src="${property.images[0]?.image || '/static/img/placeholder.jpg'}" 
                     alt="${property.title}">
                <span class="property-badge">${property.listing_type}</span>
                <button class="favorite-button" data-property-id="${property.id}"
                        aria-label="${property.is_favorited ? 'Remove from favorites' : 'Add to favorites'}">
                    <i class="fas fa-heart ${property.is_favorited ? 'active' : ''}"></i>
                </button>
            </div>
            <div class="property-content">
                <h3 class="property-title">${property.title}</h3>
                <div class="property-price">${formatCurrency(property.price)}</div>
                <div class="property-details">
                    <span class="property-detail-item">
                        <i class="fas fa-bed"></i> ${property.bedrooms} beds
                    </span>
                    <span class="property-detail-item">
                        <i class="fas fa-bath"></i> ${property.bathrooms} baths
                    </span>
                    <span class="property-detail-item">
                        <i class="fas fa-ruler-combined"></i> ${property.area} sq ft
                    </span>
                </div>
                <div class="property-location">
                    <i class="fas fa-map-marker-alt"></i> ${property.city}, ${property.state}
                </div>
            </div>
        `;
        return card;
    }
    
    showNoResults() {
        this.resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search fa-3x mb-3"></i>
                <h3>No properties found</h3>
                <p>Try adjusting your search criteria</p>
            </div>
        `;
    }
    
    showError() {
        this.resultsContainer.innerHTML = `
            <div class="search-error">
                <i class="fas fa-exclamation-circle fa-3x mb-3"></i>
                <h3>Something went wrong</h3>
                <p>Please try again later</p>
            </div>
        `;
    }
    
    toggleLoadingState(isLoading) {
        const loader = document.querySelector('.search-loader');
        if (loader) {
            loader.style.display = isLoading ? 'block' : 'none';
        }
    }
}

// Initialize search functionality
document.addEventListener('DOMContentLoaded', () => {
    new PropertySearch();
});
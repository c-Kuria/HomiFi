class PropertyGallery {
    constructor(container) {
        this.container = container;
        this.mainImage = container.querySelector('.gallery-main img');
        this.thumbnails = container.querySelectorAll('.gallery-thumbnail');
        this.currentIndex = 0;
        
        this.init();
    }
    
    init() {
        this.thumbnails.forEach((thumbnail, index) => {
            thumbnail.addEventListener('click', () => this.setActiveImage(index));
        });
        
        // Add keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') this.prev();
            if (e.key === 'ArrowRight') this.next();
        });
    }
    
    setActiveImage(index) {
        this.currentIndex = index;
        const newSrc = this.thumbnails[index].querySelector('img').src;
        this.mainImage.src = newSrc;
        
        // Update active thumbnail
        this.thumbnails.forEach(thumb => thumb.classList.remove('active'));
        this.thumbnails[index].classList.add('active');
    }
    
    next() {
        const nextIndex = (this.currentIndex + 1) % this.thumbnails.length;
        this.setActiveImage(nextIndex);
    }
    
    prev() {
        const prevIndex = (this.currentIndex - 1 + this.thumbnails.length) % this.thumbnails.length;
        this.setActiveImage(prevIndex);
    }
}

class PropertyFavorite {
    constructor(button) {
        this.button = button;
        this.propertyId = button.dataset.propertyId;
        this.init();
    }
    
    init() {
        this.button.addEventListener('click', () => this.toggleFavorite());
    }
    
    async toggleFavorite() {
        try {
            const response = await fetchData(`/properties/${this.propertyId}/favorite/`, {
                method: 'POST'
            });
            
            if (response.status === 'added') {
                this.button.classList.add('active');
                this.button.setAttribute('aria-label', 'Remove from favorites');
            } else {
                this.button.classList.remove('active');
                this.button.setAttribute('aria-label', 'Add to favorites');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }
}

class PropertyForm {
    constructor(form) {
        this.form = form;
        this.imagePreview = form.querySelector('.image-preview');
        this.imageInput = form.querySelector('input[type="file"]');
        this.init();
    }
    
    init() {
        if (this.imageInput) {
            this.imageInput.addEventListener('change', (e) => this.handleImageUpload(e));
        }
        
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
    
    handleImageUpload(event) {
        this.imagePreview.innerHTML = '';
        const files = Array.from(event.target.files);
        
        files.forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const preview = document.createElement('div');
                    preview.className = 'preview-item';
                    preview.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">
                        <button type="button" class="remove-image">&times;</button>
                    `;
                    
                    preview.querySelector('.remove-image').addEventListener('click', () => {
                        preview.remove();
                        // Update the FileList
                        const dt = new DataTransfer();
                        const input = this.imageInput;
                        const { files } = input;
                        
                        for (let i = 0; i < files.length; i++) {
                            const file = files[i];
                            if (file !== files[i]) dt.items.add(file);
                        }
                        
                        input.files = dt.files;
                    });
                    
                    this.imagePreview.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        if (!validateForm(this.form)) {
            return;
        }
        
        const formData = new FormData(this.form);
        
        try {
            const response = await fetch(this.form.action, {
                method: this.form.method,
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                window.location.href = '/dashboard/';
            } else {
                const data = await response.json();
                Object.keys(data).forEach(key => {
                    const input = this.form.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.classList.add('is-invalid');
                        const feedback = input.nextElementSibling;
                        if (feedback && feedback.classList.contains('invalid-feedback')) {
                            feedback.textContent = data[key].join(' ');
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error submitting form:', error);
        }
    }
}

// Initialize components
document.addEventListener('DOMContentLoaded', () => {
    // Initialize property gallery
    const galleryContainer = document.querySelector('.property-gallery');
    if (galleryContainer) {
        new PropertyGallery(galleryContainer);
    }
    
    // Initialize favorite buttons
    const favoriteButtons = document.querySelectorAll('.favorite-button');
    favoriteButtons.forEach(button => new PropertyFavorite(button));
    
    // Initialize property form
    const propertyForm = document.querySelector('.property-form');
    if (propertyForm) {
        new PropertyForm(propertyForm);
    }
});
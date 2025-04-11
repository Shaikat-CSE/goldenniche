/**
 * AJAX Product Filtering
 * Handles filtering products without page reload
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find the filter button
    const filterBtn = document.getElementById('ajax-filter');
    
    if (filterBtn) {
        // Initialize the filter button with data attributes
        setTimeout(function() {
            const urlsDiv = document.getElementById('ajax-filter-urls');
            
            if (urlsDiv) {
                filterBtn.setAttribute('data-url', urlsDiv.getAttribute('data-filter-url'));
                filterBtn.setAttribute('data-cart-url', urlsDiv.getAttribute('data-cart-url'));
                filterBtn.setAttribute('data-wishlist-url', urlsDiv.getAttribute('data-wishlist-url'));
            }
        }, 100);

        filterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get filter values
            const categories = [];
            document.querySelectorAll('input[type="checkbox"].filter-checkbox:checked').forEach(checkbox => {
                // Use the value attribute directly
                if (checkbox.value) {
                    categories.push(checkbox.value);
                    console.log('Selected category:', checkbox.value);
                }
            });
            
            const minPrice = document.querySelector('#price-min')?.value || '';
            const maxPrice = document.querySelector('#price-max')?.value || '';
            
            console.log('Filter parameters:', {
                categories,
                minPrice,
                maxPrice,
                sort
            });
            
            // Get sort value
            let sort = '';
            const sortSelect = document.querySelector('#sort-by');
            if (sortSelect) {
                sort = sortSelect.value;
            } else {
                // Fallback to store-sort if sort-by doesn't exist
                const storeSort = document.querySelector('.store-sort .input-select');
                if (storeSort) {
                    const sortValue = storeSort.value;
                    if (sortValue === '0') {
                        sort = 'popularity';
                    } else if (sortValue === '1') {
                        sort = 'newest';
                    }
                }
            }
            
            // Get URLs from data attributes
            const filterUrl = filterBtn.getAttribute('data-url');
            const cartUrl = filterBtn.getAttribute('data-cart-url');
            const wishlistUrl = filterBtn.getAttribute('data-wishlist-url');
            
            if (!filterUrl) {
                console.error('Filter URL not found');
                return;
            }
            
            // Show loading indicator
            const productsContainer = document.querySelector('.products-container');
            if (productsContainer) {
                productsContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p>Loading products...</p></div>';
            }
            
            // Build query parameters
            const params = new URLSearchParams();
            if (categories.length > 0) {
                params.append('category', categories.join(','));
            }
            if (minPrice) params.append('min_price', minPrice);
            if (maxPrice) params.append('max_price', maxPrice);
            if (sort && sort !== 'default') params.append('sort_by', sort);
            
            // Add search query if it exists in URL
            const urlParams = new URLSearchParams(window.location.search);
            const searchQuery = urlParams.get('q');
            if (searchQuery) {
                params.append('q', searchQuery);
            }
            
            // Make AJAX request
            console.log('Making AJAX request to:', `${filterUrl}?${params.toString()}`);
            
            fetch(`${filterUrl}?${params.toString()}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('AJAX response:', data);
                    
                    if (productsContainer) {
                        if (data.html) {
                            // If server returns HTML, use it directly
                            productsContainer.innerHTML = data.html;
                            
                            // If no products were found, show a message
                            if (data.count === 0) {
                                productsContainer.innerHTML = `
                                    <div class="col-md-12">
                                        <div class="alert alert-info">
                                            <p>No products found matching your filter criteria.</p>
                                            <p>Try selecting different categories or adjusting the price range.</p>
                                        </div>
                                    </div>
                                `;
                            }
                        } else if (data.products && Array.isArray(data.products)) {
                            // If server returns product data, build HTML
                            let html = '<div class="row" id="products-container">';
                            
                            if (data.products.length > 0) {
                                data.products.forEach((product, index) => {
                                    html += `
                                        <div class="col-md-4 col-xs-6">
                                            <div class="product">
                                                <div class="product-img">
                                                    ${product.image_url ? 
                                                        `<img src="${product.image_url}" alt="${product.name}">` : 
                                                        `<img src="/static/img/default-product.jpg" alt="${product.name}">`
                                                    }
                                                    ${product.discount_price ? 
                                                        `<div class="product-label">
                                                            <span class="sale">-${Math.round(((product.price - product.discount_price) / product.price) * 100)}%</span>
                                                            ${product.is_new ? '<span class="new">NEW</span>' : ''}
                                                        </div>` : 
                                                        (product.is_new ? '<div class="product-label"><span class="new">NEW</span></div>' : '')
                                                    }
                                                </div>
                                                <div class="product-body">
                                                    <p class="product-category">${product.category}</p>
                                                    <h3 class="product-name"><a href="/product/${product.slug}/">${product.name}</a></h3>
                                                    ${product.discount_price ? 
                                                        `<h4 class="product-price">৳${product.discount_price.toFixed(2)} <del class="product-old-price">৳${product.price.toFixed(2)}</del></h4>` : 
                                                        `<h4 class="product-price">৳${product.price.toFixed(2)}</h4>`
                                                    }
                                                    <div class="product-rating">
                                                        <i class="fa fa-star"></i>
                                                        <i class="fa fa-star"></i>
                                                        <i class="fa fa-star"></i>
                                                        <i class="fa fa-star"></i>
                                                        <i class="fa fa-star-o"></i>
                                                    </div>
                                                    <div class="product-btns">
                                                        <button class="add-to-wishlist" data-product-id="${product.id}"><i class="fa fa-heart-o"></i><span class="tooltipp">add to wishlist</span></button>
                                                        <button class="add-to-compare"><i class="fa fa-exchange"></i><span class="tooltipp">add to compare</span></button>
                                                        <button class="quick-view"><i class="fa fa-eye"></i><span class="tooltipp">quick view</span></button>
                                                    </div>
                                                </div>
                                                <div class="add-to-cart">
                                                    <button class="add-to-cart-btn" data-product-id="${product.id}"><i class="fa fa-shopping-cart"></i> add to cart</button>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                    
                                    // Add clearfix divs
                                    if ((index + 1) % 3 === 0) {
                                        html += '<div class="clearfix visible-lg visible-md"></div>';
                                    }
                                    if ((index + 1) % 2 === 0) {
                                        html += '<div class="clearfix visible-sm visible-xs"></div>';
                                    }
                                });
                            } else {
                                html += `
                                    <div class="col-md-12">
                                        <div class="alert alert-info">
                                            <p>No products found matching your filter criteria.</p>
                                        </div>
                                    </div>
                                `;
                            }
                            
                            html += '</div>';
                            productsContainer.innerHTML = html;
                        } else {
                            productsContainer.innerHTML = '<div class="alert alert-danger">Error: Invalid response format from server.</div>';
                        }
                        
                        // Re-initialize cart and wishlist buttons
                        initializeButtons(cartUrl, wishlistUrl);
                    }
                })
                .catch(error => {
                    console.error('Error fetching filtered products:', error);
                    if (productsContainer) {
                        productsContainer.innerHTML = '<div class="alert alert-danger">Error loading products. Please try again.</div>';
                    }
                });
        });
    }

    // Initialize price slider if nouislider is available
    if (typeof noUiSlider !== 'undefined') {
        const priceSlider = document.getElementById('price-slider');
        
        if (priceSlider && !priceSlider.noUiSlider) {
            const minPriceInput = document.getElementById('price-min');
            const maxPriceInput = document.getElementById('price-max');
            
            const minPriceDefault = minPriceInput.value || 0;
            const maxPriceDefault = maxPriceInput.value || 10000;
            
            noUiSlider.create(priceSlider, {
                start: [parseInt(minPriceDefault), parseInt(maxPriceDefault)],
                connect: true,
                step: 100,
                range: {
                    'min': 0,
                    'max': 10000
                }
            });
            
            // Update input fields when slider changes
            priceSlider.noUiSlider.on('update', function(values, handle) {
                const value = Math.round(values[handle]);
                
                if (handle) {
                    maxPriceInput.value = value;
                } else {
                    minPriceInput.value = value;
                }
            });
            
            // Update slider when input fields change
            minPriceInput.addEventListener('change', function() {
                priceSlider.noUiSlider.set([this.value, null]);
            });
            
            maxPriceInput.addEventListener('change', function() {
                priceSlider.noUiSlider.set([null, this.value]);
            });
        }
    }
});

/**
 * Initialize cart and wishlist buttons after AJAX content is loaded
 */
function initializeButtons(cartUrl, wishlistUrl) {
    // Initialize cart buttons - handle both button classes
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            if (productId && cartUrl) {
                // Replace the placeholder ID with the actual product ID
                const url = cartUrl.replace('/0/', `/${productId}/`);
                
                // Try POST first, fall back to GET if needed
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => {
                    if (!response.ok && response.status === 405) {
                        // Method Not Allowed, try GET instead
                        return fetch(url, {
                            method: 'GET',
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                    }
                    return response;
                })
                .then(response => response.json())
                .then(data => {
                    // Handle both success formats (status or success property)
                    const isSuccess = data.status === 'success' || data.success === true;
                    
                    if (isSuccess) {
                        // Update cart count in all cart badges
                        document.querySelectorAll('.cart-badge, .cart-qty').forEach(function(el) {
                            el.textContent = data.cart_count;
                        });
                        
                        // Reload cart items if function exists
                        if (typeof loadCartItems === 'function') {
                            loadCartItems();
                        }
                        
                        // Show success message
                        showMessage(data.message || 'Product added to cart successfully!', 'success');
                    } else {
                        showMessage(data.message || 'Failed to add product to cart', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error adding to cart:', error);
                    showMessage('An error occurred. Please try again.', 'error');
                });
            }
        });
    });
    
    // Initialize wishlist buttons
    document.querySelectorAll('.add-to-wishlist').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            if (productId && wishlistUrl) {
                // Replace the placeholder ID with the actual product ID
                const url = wishlistUrl.replace('/0/', `/${productId}/`);
                
                // Try POST first, fall back to GET if needed
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => {
                    if (!response.ok && response.status === 405) {
                        // Method Not Allowed, try GET instead
                        return fetch(url, {
                            method: 'GET',
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                    }
                    return response;
                })
                .then(response => response.json())
                .then(data => {
                    // Handle both success formats (status or success property)
                    const isSuccess = data.status === 'success' || data.success === true;
                    
                    if (isSuccess) {
                        // Update wishlist count in all wishlist badges
                        document.querySelectorAll('.wishlist-badge, .wishlist-qty').forEach(function(el) {
                            el.textContent = data.wishlist_count;
                        });
                        
                        // Change button appearance
                        const icon = this.querySelector('i');
                        if (icon) {
                            icon.classList.remove('fa-heart-o');
                            icon.classList.add('fa-heart');
                        }
                        
                        const tooltip = this.querySelector('.tooltipp');
                        if (tooltip) {
                            tooltip.textContent = 'added to wishlist';
                        }
                        
                        // Show success message
                        showMessage(data.message || 'Product added to wishlist successfully!', 'success');
                    } else {
                        showMessage(data.message || 'Failed to add product to wishlist', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error adding to wishlist:', error);
                    showMessage('An error occurred. Please try again.', 'error');
                });
            }
        });
    });
    
    // Initialize background images for set-bg elements
    document.querySelectorAll('.set-bg').forEach(element => {
        const bg = element.getAttribute('data-setbg');
        if (bg) {
            element.style.backgroundImage = `url(${bg})`;
        }
    });
}

/**
 * Show a message to the user
 */
function showMessage(message, type = 'success') {
    // Remove any existing message
    const existingMessages = document.querySelectorAll('.message-popup');
    existingMessages.forEach(msg => msg.remove());
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} message-popup`;
    messageDiv.innerHTML = message;
    document.body.appendChild(messageDiv);
    
    // Add styles
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '9999';
    messageDiv.style.minWidth = '250px';
    messageDiv.style.padding = '15px';
    messageDiv.style.borderRadius = '4px';
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(-20px)';
    messageDiv.style.transition = 'opacity 0.3s, transform 0.3s';
    
    // Show message with animation
    setTimeout(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            if (document.body.contains(messageDiv)) {
                document.body.removeChild(messageDiv);
            }
        }, 300);
    }, 3000);
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 
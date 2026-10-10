// Main JavaScript utilities

// Get CSRF token from cookie
function getCSRFToken() {
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

// Format currency
function formatCurrency(amount, currency = 'USD') {
    if (currency === 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    } else if (currency === 'INR') {
        return '₹ ' + new Intl.NumberFormat('en-IN', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }
    return amount.toLocaleString();
}

// Compact suffix display (e.g. K / L / Cr) often used with INR amounts
function formatIndianNumber(num) {
    if (num >= 10000000) {
        return (num / 10000000).toFixed(2) + ' Cr';
    } else if (num >= 100000) {
        return (num / 100000).toFixed(2) + ' L';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + ' K';
    }
    return num.toString();
}

// INR with grouping suited to en-IN locale
function formatIndianCurrency(amount) {
    const formatted = new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
    return '₹ ' + formatted;
}

// API request helper
async function apiRequest(url, options = {}) {
    const token = getCookie('access_token');
    const headers = {};

    if (options.body != null) {
        headers['Content-Type'] = 'application/json';
    }
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const finalOptions = {
        credentials: 'include',
        ...options,
        headers: {
            ...headers,
            ...(options.headers || {})
        }
    };

    try {
        const response = await fetch(url, finalOptions);
        
        if (response.status === 401) {
            // Unauthorized - redirect to login only if not already on login page
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
            return null;
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        // Only log network errors, not 401 redirects
        if (error.name !== 'TypeError' || !error.message.includes('fetch')) {
            console.error('API request failed:', error);
        }
        throw error;
    }
}

/**
 * Exchange rate: 1 unit of `from` equals `rate` units of `to` (same semantics as the portfolio API).
 */
async function getExchangeRate(fromCurrency, toCurrency) {
    if (!fromCurrency || !toCurrency || fromCurrency === toCurrency) {
        return 1;
    }
    try {
        const q =
            'from_currency=' +
            encodeURIComponent(fromCurrency) +
            '&to_currency=' +
            encodeURIComponent(toCurrency);
        const response = await apiRequest('/api/portfolio/exchange-rate?' + q);
        if (response && response.rate != null && !Number.isNaN(Number(response.rate))) {
            return Number(response.rate);
        }
    } catch (e) {
        console.error('Failed to get exchange rate:', e);
    }
    if (fromCurrency === 'USD' && toCurrency === 'INR') return 83;
    if (fromCurrency === 'INR' && toCurrency === 'USD') return 1 / 83;
    return 1;
}

/** Convert a monetary amount using live rates (amount * rate). */
async function convertCurrencyAmount(amount, fromCurrency, toCurrency) {
    const n = Number(amount);
    if (Number.isNaN(n)) return 0;
    if (!fromCurrency || !toCurrency || fromCurrency === toCurrency) return n;
    const rate = await getExchangeRate(fromCurrency, toCurrency);
    return n * rate;
}

// Get cookie helper
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Modal helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal on outside click
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
});

// Close modal on close button
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-close') || event.target.classList.contains('modal-cancel')) {
        const modal = event.target.closest('.modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }
});

// Escape key to close modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.active');
        modals.forEach(modal => modal.classList.remove('active'));
    }
});

// Prevent default behavior on placeholder links (href="#")
function setupPlaceholderLinks() {
    // Handle all placeholder links, excluding watch-demo-btn
    const placeholderLinks = document.querySelectorAll('a[href="#"]');
    placeholderLinks.forEach(link => {
        // Skip watch-demo-btn if it exists
        if (link.id === 'watch-demo-btn' || link.dataset.placeholderHandled) {
            return;
        }
        
        // Mark as handled to avoid duplicate listeners
        link.dataset.placeholderHandled = 'true';
        
        // Add click handler with capture phase to catch early
        link.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // Get the link text for better messaging
            const linkText = this.textContent.trim();
            showNotification(`${linkText} feature is coming soon!`, 'info');
            return false;
        }, true); // Use capture phase to catch before other handlers
        
        // Also prevent default on mousedown
        link.addEventListener('mousedown', function(e) {
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
            }
        }, true);
    });
}

// Run on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupPlaceholderLinks);
} else {
    // DOM already loaded
    setupPlaceholderLinks();
}

// Also run after a short delay to catch dynamically added content
setTimeout(setupPlaceholderLinks, 100);

// Show notification
function showNotification(message, type = 'info') {
    // Remove any existing notifications first
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    // Simple notification - can be enhanced with a toast library
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background-color: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#2563eb'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-weight: 500;
        font-size: 14px;
        max-width: 350px;
        animation: slideInRight 0.3s ease;
    `;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    if (!document.querySelector('style[data-notification]')) {
        style.setAttribute('data-notification', 'true');
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s, transform 0.3s';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

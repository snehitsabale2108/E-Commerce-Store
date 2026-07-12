/* ================================================================
   FreshMart - Main JavaScript
   ================================================================ */

// ── Initialization ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    // Initialize AOS animations
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 600, easing: 'ease-out', once: true, offset: 80 });
    }

    initDarkMode();
    initSearchAutocomplete();
    initAIChat();
    initCartBadge();
    initToastContainer();
});

// ── Dark Mode ──────────────────────────────────────────────────────
function initDarkMode() {
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const saved = localStorage.getItem('theme') || 'light';

    applyTheme(saved);

    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('theme', next);
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.innerHTML = theme === 'dark'
            ? '<i class="bi bi-sun-fill text-warning"></i>'
            : '<i class="bi bi-moon-fill"></i>';
    }
}

// ── Toast Notifications ────────────────────────────────────────────
let toastContainer;

function initToastContainer() {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toastContainer.style.zIndex = '10000';
    document.body.appendChild(toastContainer);
}

function showToast(message, type = 'success', duration = 3500) {
    if (!toastContainer) initToastContainer();
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', info: 'bi-info-circle-fill', warning: 'bi-exclamation-triangle-fill' };
    const toast = document.createElement('div');
    toast.className = `fm-toast ${type}`;
    toast.innerHTML = `
        <i class="bi ${icons[type] || icons.success} toast-icon fs-5"></i>
        <span>${message}</span>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toastSlide 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ── Cart Functions ─────────────────────────────────────────────────
function addToCart(productId, quantity = 1) {
    const btn = document.querySelector(`[data-product-id="${productId}"]`);
    if (btn) {
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<span class="fm-spinner"></span>';
        btn.disabled = true;
        
        fetch('/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: quantity })
        })
        .then(r => r.json())
        .then(data => {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            if (data.success) {
                showToast(data.message || 'Added to cart! 🛒', 'success');
                updateCartCount(data.cart_count);
                // Animate button
                btn.innerHTML = '<i class="bi bi-check"></i>';
                btn.classList.add('btn-success');
                btn.classList.remove('btn-primary');
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-primary');
                }, 1500);
            } else {
                showToast(data.message || 'Failed to add to cart', 'error');
            }
        })
        .catch(() => {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            showToast('Please log in to add items to cart', 'info');
            setTimeout(() => window.location.href = '/auth/login', 1500);
        });
    } else {
        // Direct add without button reference
        fetch('/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: quantity })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(data.message || 'Added to cart! 🛒', 'success');
                updateCartCount(data.cart_count);
            } else {
                showToast(data.message || 'Failed to add', 'error');
            }
        })
        .catch(() => showToast('Please log in first', 'info'));
    }
}

function updateCart(itemId, quantity) {
    fetch('/cart/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, quantity: quantity })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (quantity <= 0) {
                document.getElementById(`cartItem${itemId}`)?.remove();
                showToast('Item removed', 'info');
            } else {
                document.getElementById(`qty${itemId}`).textContent = quantity;
            }
        }
    });
}

function removeFromCart(itemId) {
    fetch('/cart/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const el = document.getElementById(`cartItem${itemId}`);
            if (el) {
                el.style.animation = 'toastSlide 0.3s ease reverse';
                setTimeout(() => el.remove(), 280);
            }
            updateCartCount(data.cart_count);
            showToast('Item removed from cart', 'info');
        }
    });
}

function saveForLater(itemId) {
    fetch('/cart/save-for-later', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('Saved for later 📌', 'success');
            setTimeout(() => location.reload(), 800);
        }
    });
}

function moveToCart(itemId) {
    fetch('/cart/move-to-cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('Moved to cart! 🛒', 'success');
            setTimeout(() => location.reload(), 600);
        }
    });
}

function updateCartCount(count) {
    const badge = document.getElementById('cartCount');
    if (badge) {
        badge.textContent = count;
        badge.style.animation = 'none';
        badge.offsetHeight; // reflow
        badge.style.animation = 'pulse 0.4s ease';
    }
}

function initCartBadge() {
    // pulse animation for badges
    const style = document.createElement('style');
    style.textContent = '@keyframes pulse { 0%,100%{transform:translate(35%,-35%) scale(1)} 50%{transform:translate(35%,-35%) scale(1.4)} }';
    document.head.appendChild(style);
}

// ── Wishlist ───────────────────────────────────────────────────────
function toggleWishlist(productId, btn) {
    fetch('/wishlist/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, data.action === 'added' ? 'success' : 'info');
            if (btn) {
                if (data.action === 'added') {
                    btn.innerHTML = '<i class="bi bi-heart-fill text-danger"></i>';
                } else {
                    btn.innerHTML = '<i class="bi bi-heart"></i>';
                }
            }
            const badge = document.getElementById('wishlistCount');
            if (badge) badge.textContent = data.count;
        }
    })
    .catch(() => {
        showToast('Please log in to use wishlist', 'info');
        setTimeout(() => window.location.href = '/auth/login', 1500);
    });
}

// ── Search Autocomplete ────────────────────────────────────────────
function initSearchAutocomplete() {
    const input = document.getElementById('searchInput');
    const results = document.getElementById('searchResults');
    if (!input || !results) return;

    let timeout;
    input.addEventListener('input', function () {
        clearTimeout(timeout);
        const q = this.value.trim();
        if (q.length < 2) {
            results.style.display = 'none';
            return;
        }
        timeout = setTimeout(() => {
            fetch(`/products/api/search?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.length === 0) {
                        results.style.display = 'none';
                        return;
                    }
                    results.innerHTML = data.map(p => `
                        <a href="/products/${p.slug}" class="search-result-item">
                            <img src="/static/images/products/${p.image}" 
                                 onerror="this.src='/static/images/default_product.png'">
                            <div>
                                <div class="fw-semibold small">${p.name}</div>
                                <div class="text-success small">₹${p.price} / ${p.unit}</div>
                            </div>
                        </a>
                    `).join('') + `<a href="/products/?q=${encodeURIComponent(q)}" class="search-result-item text-primary"><i class="bi bi-search me-2"></i>See all results for "${q}"</a>`;
                    results.style.display = 'block';
                });
        }, 300);
    });

    document.addEventListener('click', e => {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            results.style.display = 'none';
        }
    });

    input.addEventListener('keydown', e => {
        if (e.key === 'Escape') results.style.display = 'none';
    });
}

// ── AI Chat Widget ─────────────────────────────────────────────────
function initAIChat() {
    const toggle = document.getElementById('aiChatToggle');
    const window_ = document.getElementById('aiChatWindow');
    const close = document.getElementById('aiChatClose');
    const input = document.getElementById('aiChatInput');
    const send = document.getElementById('aiChatSend');
    const messages = document.getElementById('aiChatMessages');
    const quickReplies = document.getElementById('aiQuickReplies');

    if (!toggle || !window_) return;

    toggle.addEventListener('click', () => {
        window_.classList.toggle('open');
        if (window_.classList.contains('open') && input) {
            setTimeout(() => input.focus(), 200);
        }
    });

    if (close) close.addEventListener('click', () => window_.classList.remove('open'));

    // Quick reply buttons
    if (quickReplies) {
        quickReplies.querySelectorAll('.quick-reply-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (input) input.value = btn.textContent.trim();
                sendAIMessage();
            });
        });
    }

    if (send) send.addEventListener('click', sendAIMessage);
    if (input) {
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAIMessage();
            }
        });
    }

    function sendAIMessage() {
        if (!input) return;
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';

        // Add user message
        appendMessage(msg, 'user');

        // Show typing indicator
        const typingId = 'typing-' + Date.now();
        appendTyping(typingId);

        fetch('/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, history: [] })
        })
        .then(r => r.json())
        .then(data => {
            document.getElementById(typingId)?.remove();
            if (data.success) {
                appendMessage(formatAIResponse(data.reply), 'ai');
                // Update quick replies if provided
                if (data.quick_replies && quickReplies) {
                    quickReplies.innerHTML = data.quick_replies.slice(0, 4).map(
                        r => `<button class="quick-reply-btn">${r}</button>`
                    ).join('');
                    quickReplies.querySelectorAll('.quick-reply-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            input.value = btn.textContent.trim();
                            sendAIMessage();
                        });
                    });
                }
            } else {
                appendMessage("Sorry, I'm having trouble right now. Please try again in a moment.", 'ai');
            }
        })
        .catch(() => {
            document.getElementById(typingId)?.remove();
            appendMessage("Connection error. Please check your internet and try again.", 'ai');
        });
    }

    function appendMessage(text, role) {
        if (!messages) return;
        const div = document.createElement('div');
        div.className = role === 'user' ? 'user-message' : 'ai-message';
        if (role === 'ai') {
            div.innerHTML = `
                <div class="ai-avatar"><i class="bi bi-robot"></i></div>
                <div class="ai-bubble">${text}</div>
            `;
        } else {
            div.innerHTML = `<div class="user-bubble">${escapeHTML(text)}</div>`;
        }
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendTyping(id) {
        if (!messages) return;
        const div = document.createElement('div');
        div.className = 'ai-message typing-indicator';
        div.id = id;
        div.innerHTML = `
            <div class="ai-avatar"><i class="bi bi-robot"></i></div>
            <div class="ai-bubble">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function formatAIResponse(text) {
        // Convert markdown-like formatting to HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.*)$/, '<p>$1</p>')
            .replace(/<p><\/p>/g, '');
    }

    function escapeHTML(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
}

// ── Utility ────────────────────────────────────────────────────────
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2);
}

// Auto-dismiss bootstrap alerts
document.querySelectorAll('.alert').forEach(alert => {
    if (!alert.querySelector('.btn-close')) return;
    setTimeout(() => {
        const bsAlert = bootstrap?.Alert?.getOrCreateInstance(alert);
        bsAlert?.close();
    }, 5000);
});

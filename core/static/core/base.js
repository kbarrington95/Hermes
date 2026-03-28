// base.js — loaded on every page via base.html
// Manages nav auth state from localStorage JWT

(function () {
    const navAuth = document.getElementById('nav-auth');
    const navLinks = document.getElementById('nav-links');
    const token = localStorage.getItem('access_token');

    if (token) {
        // Show user email + logout button
        const username = localStorage.getItem('user_username') || '';
        const email = localStorage.getItem('user_email') || '';
        const userLabel = username && email ? `${username} - ${email}` : username || email || 'Account';
        const isStaff = localStorage.getItem('user_is_staff') === '1';
        const adminLink = isStaff ? `<a href="/admin/" class="btn btn-outline btn-sm" target="_blank">Admin</a>` : '';
        navAuth.innerHTML = `
            <span class="nav-user">${userLabel}</span>
            <button class="btn btn-outline btn-sm" id="logout-btn">Logout</button>
            ${adminLink}
        `;
        document.getElementById('logout-btn').addEventListener('click', function () {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_email');
            localStorage.removeItem('user_username');
            localStorage.removeItem('user_is_staff');
            window.location.href = '/';
        });
    } else {
        // Hide nav links that require auth, show login
        if (navLinks) navLinks.style.display = 'none';
        navAuth.innerHTML = `<a href="/login/" class="btn btn-primary btn-sm">Login</a>`;
    }
})();

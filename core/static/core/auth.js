// auth.js — shared auth utilities, imported on login/register pages

const Auth = {
    // Store tokens after successful login
    setSession(data) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
    },

    // Store user info after fetching /auth/users/me/
    setUser(data) {
        localStorage.setItem('user_email', data.email);
        localStorage.setItem('user_username', data.username);
        localStorage.setItem('user_is_staff', data.is_staff ? '1' : '0');
    },

    // Fetch the current user's email and store it
    async fetchAndStoreUser() {
        const res = await fetch('/auth/users/me/', {
            headers: { 'Authorization': `JWT ${localStorage.getItem('access_token')}` }
        });
        if (res.ok) {
            const data = await res.json();
            this.setUser(data);
        }
    },

    // Full login flow: get tokens, fetch user, redirect
    async login(username, password) {
        const res = await fetch('/auth/jwt/create/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Invalid credentials');
        }

        const data = await res.json();
        this.setSession(data);
        await this.fetchAndStoreUser();
        window.location.href = '/notetaker/dashboard/';
    },

    // Register then auto-login
    async register(username, email, password) {
        const res = await fetch('/auth/users/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, username })
        });

        if (!res.ok) {
            const err = await res.json();
            const msg = Object.values(err).flat().join(' ');
            throw new Error(msg || 'Registration failed');
        }

        // Auto-login after successful registration
        await this.login(username, password);
    },

    // Redirect away if already logged in
    requireGuest() {
        if (localStorage.getItem('access_token')) {
            window.location.href = '/notetaker/dashboard/';
        }
    },

    // Redirect to login if not authenticated
    requireAuth() {
        if (!localStorage.getItem('access_token')) {
            window.location.href = '/login/';
        }
    }
};

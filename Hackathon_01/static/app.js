// Common functions for the app

function isLoggedIn() {
    return localStorage.getItem('logged_in') === 'true';
}

function getUsername() {
    return localStorage.getItem('username');
}

function updateNav() {
    const loggedIn = isLoggedIn();
    document.getElementById('login-link').style.display = loggedIn ? 'none' : 'block';
    document.getElementById('signup-link').style.display = loggedIn ? 'none' : 'block';
    document.getElementById('profile-link').style.display = loggedIn ? 'block' : 'none';
    document.getElementById('chat-link').style.display = loggedIn ? 'block' : 'none';
    document.getElementById('logout-link').style.display = loggedIn ? 'block' : 'none';
}

function logout() {
    localStorage.removeItem('logged_in');
    localStorage.removeItem('username');
    localStorage.removeItem('chat_history');
    showMessage('You have been logged out.', 'success');
    updateNav();
    setTimeout(() => window.location.href = 'index.html', 1000);
}

function showMessage(message, type) {
    const messagesDiv = document.getElementById('messages');
    if (messagesDiv) {
        messagesDiv.innerHTML = `<div class="alert ${type}">${message}</div>`;
        setTimeout(() => messagesDiv.innerHTML = '', 3000);
    }
}

function redirectToChat() {
    if (isLoggedIn()) {
        window.location.href = 'chat.html';
    } else {
        window.location.href = 'login.html';
    }
}

function loadUsers() {
    const users = localStorage.getItem('users');
    return users ? JSON.parse(users) : {};
}

function saveUsers(users) {
    localStorage.setItem('users', JSON.stringify(users));
}

function loadChatHistory(username) {
    const history = localStorage.getItem(`chat_history_${username}`);
    return history ? JSON.parse(history) : [];
}

function saveChatHistory(username, history) {
    localStorage.setItem(`chat_history_${username}`, JSON.stringify(history));
}

function loadProfile(username) {
    const profile = localStorage.getItem(`profile_${username}`);
    if (profile) {
        return JSON.parse(profile);
    }
    // Create default profile
    const defaultProfile = {
        username: username,
        created_date: new Date().toISOString(),
        total_sessions: 0,
        total_messages: 0,
        last_active: new Date().toISOString()
    };
    saveProfile(username, defaultProfile);
    return defaultProfile;
}

function saveProfile(username, profile) {
    localStorage.setItem(`profile_${username}`, JSON.stringify(profile));
}

// Initialize nav on page load
document.addEventListener('DOMContentLoaded', updateNav);
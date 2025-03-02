document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('nav-links');
    const auth = document.getElementById('auth');

    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        auth.classList.toggle('active');
    });
});

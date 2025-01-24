const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const toggleToSignup = document.getElementById('toggle-to-signup');
const toggleToLogin = document.getElementById('toggle-to-login');

toggleToSignup.addEventListener('click', () => {
    loginForm.style.display = 'none';
    signupForm.style.display = 'block';
});
toggleToLogin.addEventListener('click', () => {
    loginForm.style.display = 'block';
    signupForm.style.display = 'none';
});
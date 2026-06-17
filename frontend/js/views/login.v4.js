// ===== Login / Register Page =====
let loginMode = 'login';

function showLoginPage() {
    renderLoginForm();
    document.querySelector('#loginOverlay').style.display = 'flex';
    document.querySelector('#sidebar').style.display = 'none';
    document.querySelector('#main').style.display = 'none';
}

function hideLoginPage() {
    document.querySelector('#loginOverlay').style.display = 'none';
    document.querySelector('#sidebar').style.display = 'flex';
    document.querySelector('#main').style.display = 'flex';
}

function renderLoginForm() {
    const container = document.querySelector('#loginFormContainer');
    const isLogin = loginMode === 'login';
    container.innerHTML = ''
        + '<div class="login-tabs">'
        + '  <button class="login-tab ' + (isLogin ? 'active' : '') + '" onclick="switchLoginMode(\'login\')">Login</button>'
        + '  <button class="login-tab ' + (!isLogin ? 'active' : '') + '" onclick="switchLoginMode(\'register\')">Register</button>'
        + '</div>'
        + '<div class="login-form">'
        + '  <div class="form-group">'
        + '    <label>Username</label>'
        + '    <input class="form-control" id="loginUsername" type="text" placeholder="Enter username" autocomplete="username">'
        + '  </div>'
        + '  <div class="form-group">'
        + '    <label>Password</label>'
        + '    <input class="form-control" id="loginPassword" type="password" placeholder="Enter password" autocomplete="current-password">'
        + '  </div>'
        + '  <div id="loginError" class="login-error"></div>'
        + '  <button class="btn btn-primary btn-login" id="loginBtn" onclick="handleLogin()">'
        +       (isLogin ? 'Log In' : 'Register')
        + '  </button>'
        + '</div>';
}

function switchLoginMode(mode) {
    loginMode = mode;
    renderLoginForm();
}

async function handleLogin() {
    const username = document.querySelector('#loginUsername').value.trim();
    const password = document.querySelector('#loginPassword').value.trim();
    const errorEl = document.querySelector('#loginError');
    const btn = document.querySelector('#loginBtn');

    if (!username || !password) {
        errorEl.textContent = 'Please enter username and password';
        return;
    }

    errorEl.textContent = '';
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        let result;
        if (loginMode === 'login') {
            result = await api.login(username, password);
        } else {
            result = await api.register(username, password);
        }
        api.setToken(result.access_token);
        hideLoginPage();
        document.querySelector('#usernameDisplay').textContent = result.username;
        router.init();
    } catch (e) {
        errorEl.textContent = e.message;
        btn.disabled = false;
        btn.textContent = loginMode === 'login' ? 'Log In' : 'Register';
    }
}

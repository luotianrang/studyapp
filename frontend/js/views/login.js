// ===== 登录 / 注册页面 =====
let loginMode = 'login'; // 'login' or 'register'

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
        + '  <button class="login-tab ' + (isLogin ? 'active' : '') + '" onclick="switchLoginMode(\'login\')">登录</button>'
        + '  <button class="login-tab ' + (!isLogin ? 'active' : '') + '" onclick="switchLoginMode(\'register\')">注册</button>'
        + '</div>'
        + '<div class="login-form">'
        + '  <div class="form-group">'
        + '    <label>用户名</label>'
        + '    <input class="form-control" id="loginUsername" type="text" placeholder="输入用户名" autocomplete="username">'
        + '  </div>'
        + '  <div class="form-group">'
        + '    <label>密码</label>'
        + '    <input class="form-control" id="loginPassword" type="password" placeholder="输入密码" autocomplete="current-password">'
        + '  </div>'
        + '  <div id="loginError" class="login-error"></div>'
        + '  <button class="btn btn-primary btn-login" id="loginBtn" onclick="handleLogin()">'
        +       (isLogin ? '登 录' : '注 册')
        + '  </button>'
        + '</div>';

    // Enter key to submit
    document.getElementById('loginPassword').onkeydown = function(e) {
        if (e.key === 'Enter') handleLogin();
    };
    document.getElementById('loginUsername').onkeydown = function(e) {
        if (e.key === 'Enter') document.getElementById('loginPassword').focus();
    };
    setTimeout(function() { document.getElementById('loginUsername').focus(); }, 100);
}

function switchLoginMode(mode) {
    loginMode = mode;
    renderLoginForm();
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const errorEl = document.getElementById('loginError');
    const btn = document.getElementById('loginBtn');

    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        return;
    }

    errorEl.textContent = '';
    btn.disabled = true;
    btn.textContent = '处理中...';

    try {
        let result;
        if (loginMode === 'login') {
            result = await api.login(username, password);
        } else {
            result = await api.register(username, password);
        }
        api.setToken(result.access_token);
        hideLoginPage();
        document.getElementById('usernameDisplay').textContent = result.username;
        router.init();
    } catch (e) {
        errorEl.textContent = e.message;
        btn.disabled = false;
        btn.textContent = loginMode === 'login' ? '登 录' : '注 册';
    }
}

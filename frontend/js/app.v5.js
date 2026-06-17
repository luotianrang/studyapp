
// ===== Global State =====
var pageContent = null;
var headerActions = null;

async function refreshBookCountBadge() {
    var badge = document.querySelector("#book-count-badge");
    if (!badge || !api.getToken()) return;
    try {
        var books = await api.listMyLearningBooks();
        badge.textContent = String(books.length);
    } catch (e) {
        console.warn("Failed to refresh book count badge:", e);
    }
}

function setPage(title, subtitle) {
    document.querySelector("#page-title").textContent = title;
    document.querySelector("#page-subtitle").textContent = subtitle || "";
    headerActions = document.querySelector("#header-actions");
    headerActions.innerHTML = "";
    pageContent = document.querySelector("#page-content");
}

function escHtml(str) {
    if (!str) return "";
    var d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}

(function init() {
    try {
    var token = api.getToken();
    if (token) {
        api.getMe().then(function(user) {
            document.querySelector("#usernameDisplay").textContent = user.username;
            var su = document.querySelector("#sidebarUser");
            if (su) su.style.display = "flex";
            document.querySelector("#loginOverlay").style.display = "none";
            document.querySelector("#sidebar").style.display = "flex";
            document.querySelector("#main").style.display = "flex";
            refreshBookCountBadge();
            router.init();
        }).catch(function() {
            api.clearToken();
            showLogin();
        });
    } else {
        showLogin();
    }
    function showLogin() {
        document.querySelector("#loginOverlay").style.display = "flex";
        document.querySelector("#sidebar").style.display = "none";
        document.querySelector("#main").style.display = "none";
        var c = document.querySelector("#loginFormContainer");
        if (c) c.innerHTML = "<div class='login-tabs'>" +
          "<button class='login-tab active' onclick=\"switchLoginMode('login')\">\u767b\u5f55</button>" +
          "<button class='login-tab' onclick=\"switchLoginMode('register')\">\u6ce8\u518c</button></div>" +
          "<div class='login-form'>" +
          "<div class='form-group'><label>\u7528\u6237\u540d</label>" +
          "<input class='form-control' id='loginUsername' type='text' placeholder='\u8f93\u5165\u7528\u6237\u540d'></div>" +
          "<div class='form-group'><label>\u5bc6\u7801</label>" +
          "<input class='form-control' id='loginPassword' type='password' placeholder='\u8f93\u5165\u5bc6\u7801'></div>" +
          "<div id='loginError' class='login-error'></div>" +
          "<button class='btn btn-primary btn-login' id='loginBtn' onclick='handleLogin()'>\u767b \u5f55</button></div>";
        var u = document.querySelector("#loginUsername");
        var pw = document.querySelector("#loginPassword");
        if (u) u.onkeydown = function(e) { if (e.key === "Enter" && pw) pw.focus(); };
        if (pw) pw.onkeydown = function(e) { if (e.key === "Enter") handleLogin(); };
    }
    } catch(e) { console.error('Init error:', e); document.querySelector('#loginOverlay').style.display = 'flex'; document.querySelector('#sidebar').style.display = 'none'; document.querySelector('#main').style.display = 'none'; }
})();

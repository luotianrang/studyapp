// ===== Global State =====
let pageContent = null;
let headerActions = null;

function setPage(title, subtitle) {
    document.getElementById("page-title").textContent = title;
    document.getElementById("page-subtitle").textContent = subtitle || "";
    headerActions = document.getElementById("header-actions");
    headerActions.innerHTML = "";
    pageContent = document.getElementById("page-content");
}

function escHtml(str) {
    if (!str) return "";
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}

function formatSize(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let i = 0;
    let size = bytes;
    while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
    return size.toFixed(i > 0 ? 1 : 0) + " " + units[i];
}

// ===== Init =====
(async function init() {
    // Check auth first
    const token = api.getToken();
    if (token) {
        try {
            const user = await api.getMe();
            // Valid token: show main app
            document.querySelector("#usernameDisplay").textContent = user.username;
            var su = document.querySelector("#sidebarUser");
            if (su) su.style.display = "flex";
            var lo = document.querySelector("#loginOverlay");
            if (lo) lo.style.display = "none";
            var sb = document.querySelector("#sidebar");
            if (sb) sb.style.display = "flex";
            var mn = document.querySelector("#main");
            if (mn) mn.style.display = "flex";

            // Check if server is alive
            try {
                await fetch("http://localhost:8899/api/health", { signal: AbortSignal.timeout(2000) });
            } catch {
                console.warn("Backend server not reachable on port 8899");
            }
            router.init();
            return;
        } catch (e) {
            // Invalid token: clear and show login
            api.clearToken();
        }
    }

    // No valid token: render login page directly
    document.querySelector("#loginOverlay").style.display = "flex";
    document.querySelector("#sidebar").style.display = "none";
    document.querySelector("#main").style.display = "none";
    var container = document.querySelector("#loginFormContainer");
    if (container) {
        container.innerHTML = '<div class="login-tabs">' +
          '<button class="login-tab active" onclick="switchLoginMode('login')">' + String.fromCharCode(30331,24405) + '</button>' +
          '<button class="login-tab" onclick="switchLoginMode('register')">' + String.fromCharCode(27880,20876) + '</button>' +
          "</div>" +
          '<div class="login-form">' +
          '<div class="form-group"><label>' + String.fromCharCode(29992,25143,21517) + '</label>' +
          '<input class="form-control" id="loginUsername" type="text" placeholder="' + String.fromCharCode(36755,20837,29992,25143,21517) + '"></div>' +
          '<div class="form-group"><label>' + String.fromCharCode(23494,30721) + '</label>' +
          '<input class="form-control" id="loginPassword" type="password" placeholder="' + String.fromCharCode(36755,20837,23494,30721) + '"></div>' +
          '<div id="loginError" class="login-error"></div>' +
          '<button class="btn btn-primary btn-login" onclick="handleLogin()">' + String.fromCharCode(30331,32,24405) + '</button></div>';
        document.querySelector("#loginUsername").onkeydown = function(e) {
            if (e.key === "Enter") document.querySelector("#loginPassword").focus();
        };
        document.querySelector("#loginPassword").onkeydown = function(e) {
            if (e.key === "Enter") handleLogin();
        };
    }
    var su3 = document.querySelector("#sidebarUser");
    if (su3) su3.style.display = "flex";
})();

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

    // No valid token: show login page
    var su2 = document.querySelector("#sidebarUser");
    if (su2) su2.style.display = "flex";
    var lo2 = document.querySelector("#loginOverlay");
    if (lo2) lo2.style.display = "flex";
    var sb2 = document.querySelector("#sidebar");
    if (sb2) sb2.style.display = "none";
    var mn2 = document.querySelector("#main");
    if (mn2) mn2.style.display = "none";
    showLoginPage();
})();

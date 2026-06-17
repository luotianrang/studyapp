///
router.register("settings", async () => {
    setPage("Settings", "Local analysis and notifications");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>Loading...</p></div>`;

    try {
        const notif = await api.getNotificationSettings();
        c.innerHTML = `
            <div class="card mb-16">
                <div class="card-header">Local AI Analysis</div>
                <div class="card-body">
                    <p class="text-secondary" style="line-height:1.8">
                        Analysis now runs automatically in the backend.
                        If Ollama is available, the app prefers a local model.
                        Otherwise it falls back to built-in rule-based analysis.
                    </p>
                    <p class="text-xs text-secondary mt-8">Users no longer need or can enter an API key.</p>
                </div>
            </div>

            <div class="card mb-16">
                <div class="card-header">Notification Settings</div>
                <div class="card-body">
                    <p class="text-sm text-secondary mb-16"><b>Pushover</b> needs Token and User Key. <b>ServerChan</b> needs SendKey. <b>Bark</b> needs Bark Token.</p>

                    <div class="form-group" style="max-width:300px">
                        <label>Provider</label>
                        <select class="form-control" id="notifProvider">
                            <option value="none" ${notif.provider === "none" ? "selected" : ""}>Disabled</option>
                            <option value="pushover" ${notif.provider === "pushover" ? "selected" : ""}>Pushover</option>
                            <option value="serverchan" ${notif.provider === "serverchan" ? "selected" : ""}>ServerChan</option>
                            <option value="bark" ${notif.provider === "bark" ? "selected" : ""}>Bark</option>
                        </select>
                    </div>
                    <div class="form-group" style="max-width:400px">
                        <label>Token / API Key</label>
                        <input class="form-control" id="notifToken" value="${notif.token || ""}">
                    </div>
                    <div class="form-group" style="max-width:400px" id="userKeyGroup">
                        <label>User Key</label>
                        <input class="form-control" id="notifUserKey" value="${notif.user_key || ""}">
                    </div>
                    <div class="form-group" style="max-width:300px">
                        <label>Notify Time</label>
                        <input class="form-control" id="notifTime" type="time" value="${notif.notify_time || "09:00"}">
                    </div>
                    <div class="setting-row">
                        <div>
                            <div class="setting-label">Enable Notifications</div>
                            <div class="setting-desc">Send a daily study reminder</div>
                        </div>
                        <label class="toggle">
                            <input type="checkbox" id="notifEnabled" ${notif.enabled ? "checked" : ""}>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <button class="btn btn-primary mt-16" id="saveNotifBtn">Save Notification Settings</button>
                    <span id="notifSaveStatus" class="text-sm text-secondary ml-8" style="margin-left:8px"></span>
                </div>
            </div>
        `;

        const pv = document.getElementById("notifProvider");
        pv.onchange = () => {
            document.getElementById("userKeyGroup").style.display = (pv.value === "pushover") ? "block" : "none";
        };
        pv.dispatchEvent(new Event("change"));

        document.getElementById("saveNotifBtn").onclick = async () => {
            const s = {
                provider: document.getElementById("notifProvider").value,
                token: document.getElementById("notifToken").value.trim(),
                user_key: document.getElementById("notifUserKey").value.trim(),
                notify_time: document.getElementById("notifTime").value,
                enabled: document.getElementById("notifEnabled").checked
            };
            const statusEl = document.getElementById("notifSaveStatus");
            statusEl.textContent = "Saving...";
            try {
                await api.updateNotificationSettings(s);
                statusEl.textContent = "Saved";
            } catch (e) {
                statusEl.textContent = "Save failed: " + e.message;
            }
            setTimeout(() => statusEl.textContent = "", 3000);
        };
    } catch (e) {
        c.innerHTML = `<div class="empty-state"><h3></h3><p>${escHtml(e.message)}</p></div>`;
    }
});

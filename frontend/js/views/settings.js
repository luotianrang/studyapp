/// 
router.register("settings", async () => {
    setPage("设置", "DeepSeek API 与通知设置");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>..</p></div>`;

    try {
        const notif = await api.getNotificationSettings();
        c.innerHTML = `
            <div class="card mb-16">
                <div class="card-header"> DeepSeek API </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>DeepSeek API Key</label>
                        <input class="form-control" id="apiKey" type="password" placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" value="${localStorage.getItem("deepseek_api_key") || ""}">
                        <p class="text-xs text-secondary mt-8">API Key 存储在 localStorage</p>
                    </div>
                    <div class="form-group">
                        <label>DeepSeek 模型</label>
                        <input class="form-control" id="apiModel" placeholder="deepseek-chat" value="${localStorage.getItem("deepseek_model") || "deepseek-chat"}">
                        <p class="text-xs text-secondary mt-8">默认 deepseek-chat；可选 deepseek-reasoner 等</p>
                    </div>
                    <button class="btn btn-primary" id="saveApiBtn">💾 保存 API 配置</button>
                    <span id="apiSaveStatus" class="text-sm text-secondary ml-8" style="margin-left:8px"></span>
                </div>
            </div>

            <div class="card mb-16">
                <div class="card-header">🔔 推送通知</div>
                <div class="card-body">
                    <p class="text-sm text-secondary mb-16"><b>Pushover</b>（iOS/Android）· <b>Server酱</b>· <b>Bark</b></p>

                    <div class="form-group" style="max-width:300px">
                        <label>通知服务</label>
                        <select class="form-control" id="notifProvider">
                            <option value="none" ${notif.provider === "none" ? "selected" : ""}>不启用</option>
                            <option value="pushover" ${notif.provider === "pushover" ? "selected" : ""}>Pushover</option>
                            <option value="serverchan" ${notif.provider === "serverchan" ? "selected" : ""}>Server酱</option>
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
                        <label>通知时间</label>
                        <input class="form-control" id="notifTime" type="time" value="${notif.notify_time || "09:00"}">
                    </div>
                    <div class="setting-row">
                        <div>
                            <div class="setting-label">启用推送通知</div>
                            <div class="setting-desc">每天按时推送学习提醒</div>
                        </div>
                        <label class="toggle">
                            <input type="checkbox" id="notifEnabled" ${notif.enabled ? "checked" : ""}>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <button class="btn btn-primary mt-16" id="saveNotifBtn">💾 保存通知设置</button>
                    <span id="notifSaveStatus" class="text-sm text-secondary ml-8" style="margin-left:8px"></span>
                </div>
            </div>

            <div class="card">
            <div class="card-header">ℹ️ 关于通知服务</div>
                <div class="card-body text-secondary" style="font-size:13px;line-height:1.8">
                    <p><b>Pushover</b>（iOS/Android）：需 Token 和 User Key</p>
                    <p><b>Server酱</b>：需 sct.ftqq.com 的 SendKey</p>
                    <p><b>Bark</b>（iOS）：需 Bark App 的 Token</p>
                    <p class="mt-8"><b>API Key</b> 存储在 localStorage，DeepSeek API 密钥用于生成学习计划</p>
                </div>
            </div>
        `;

        // Provider-dependent visibility
        const pv = document.getElementById("notifProvider");
        pv.onchange = () => {
            document.getElementById("userKeyGroup").style.display = (pv.value === "pushover") ? "block" : "none";
        };
        pv.dispatchEvent(new Event("change"));

        // Save API Key
        document.getElementById("saveApiBtn").onclick = async () => {
            const key = document.getElementById("apiKey").value.trim();
            const model = document.getElementById("apiModel").value.trim() || "deepseek-chat";
            localStorage.setItem("deepseek_api_key", key);
            localStorage.setItem("deepseek_model", model);
            const statusEl = document.getElementById("apiSaveStatus");
            statusEl.textContent = "保存中...";
            try {
                await api.setDeepSeekConfig(key, model);
                statusEl.textContent = "✅ 已保存";
            } catch (e) {
                statusEl.textContent = "保存失败: " + e.message;
            }
            setTimeout(() => statusEl.textContent = "", 3000);
        };

        // Save Notification Settings
        document.getElementById("saveNotifBtn").onclick = async () => {
            const s = {
                provider: document.getElementById("notifProvider").value,
                token: document.getElementById("notifToken").value.trim(),
                user_key: document.getElementById("notifUserKey").value.trim(),
                notify_time: document.getElementById("notifTime").value,
                enabled: document.getElementById("notifEnabled").checked
            };
            const statusEl = document.getElementById("notifSaveStatus");
            statusEl.textContent = "保存中...";
            try {
                await api.updateNotificationSettings(s);
                statusEl.textContent = "✅ 已保存";
            } catch (e) {
                statusEl.textContent = "保存失败: " + e.message;
            }
            setTimeout(() => statusEl.textContent = "", 3000);
        };
    } catch (e) {
        c.innerHTML = `<div class="empty-state"><h3></h3><p>${escHtml(e.message)}</p></div>`;
    }
});

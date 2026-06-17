// API 接口
const api = {
    BASE: "/api",
    TOKEN_KEY: "studyapp_token",

    getToken() { return localStorage.getItem(this.TOKEN_KEY); },
    setToken(token) { localStorage.setItem(this.TOKEN_KEY, token); },
    clearToken() { localStorage.removeItem(this.TOKEN_KEY); },

    async request(method, path, body, isForm) {
        const url = this.BASE + path;
        const opts = { method, headers: {} };
        const token = this.getToken();
        if (token) {
            opts.headers["Authorization"] = "Bearer " + token;
        }
        if (body && isForm) {
            opts.body = body;
        } else if (body) {
            opts.headers["Content-Type"] = "application/json";
            opts.body = JSON.stringify(body);
        }
        const resp = await fetch(url, opts);
        if (resp.status === 401) {
            this.clearToken();
        throw new Error("Session expired");
        }
        if (!resp.ok) {
            const err = await resp.text();
            let msg = err;
            try {
                const j = JSON.parse(err);
                msg = j.message || j.detail || err;
            } catch {}
            throw new Error(msg);
        }
        if (resp.status === 204) return null;
        return resp.json();
    },

    // Books - 
    listPresetBooks() { return this.request("GET", "/books/preset"); },
    listMyLearningBooks() { return this.request("GET", "/books/my-learning"); },
    addToMyLearning(bookId) { return this.request("POST", "/books/add-to-my-learning?book_id=" + bookId); },
    removeFromMyLearning(bookId) { return this.request("DELETE", "/books/remove-from-my-learning/" + bookId); },
    getBook(id) { return this.request("GET", "/books/" + id); },
    getChapters(bookId) { return this.request("GET", "/books/" + bookId + "/chapters"); },

    // ?
    getKnowledgePoints(chapterId) { return this.request("GET", "/analysis/knowledge-points/" + chapterId); },
    getAllKnowledgePoints(bookId) { return this.request("GET", "/analysis/book/" + bookId + "/knowledge-points"); },

    // Plans
    generatePlan(bookId, totalDays, dailyMinutes) {
        return this.request("POST", "/plans/generate", { book_id: bookId, total_days: totalDays, daily_minutes: dailyMinutes });
    },
    listPlans() { return this.request("GET", "/plans/"); },
    getPlan(id) { return this.request("GET", "/plans/" + id); },
    getPlanDays(planId) { return this.request("GET", "/plans/" + planId + "/days"); },
    completeDay(planId, dayId) { return this.request("POST", "/plans/" + planId + "/days/" + dayId + "/complete"); },
    deletePlan(id) { return this.request("DELETE", "/plans/" + id); },
    // Reviews
    submitReview(planId, itemId, quality) {
        return this.request("POST", "/plans/" + planId + "/items/" + itemId + "/review", { quality, plan_item_id: itemId });
    },
    getReviewStats(planId) {
        return this.request("GET", "/plans/" + planId + "/review-stats");
    },
    getReviewRecords(planId) {
        return this.request("GET", "/plans/" + planId + "/review-records");
    },


    // Notifications
    getNotificationSettings() { return this.request("GET", "/notifications/settings"); },
    updateNotificationSettings(s) { return this.request("PUT", "/notifications/settings", s); },

    // Config
    setDeepSeekConfig(apiKey, model) {
        return this.request("POST", "/config/deepseek", { api_key: apiKey, model: model });
    },

    // ===== Auth =====
    login(username, password) {
        return this.request("POST", "/auth/login", { username, password });
    },
    register(username, password) {
        return this.request("POST", "/auth/register", { username, password });
    },
    getMe() {
        return this.request("GET", "/auth/me");
    },
    logout() {
        this.clearToken();
        window.location.reload();
    },
    // ===== Admin =====
    adminListBooks() { return this.request("GET", "/admin/books"); },
    adminCreateBook(data) { return this.request("POST", "/admin/books", data); },
    adminUpdateBook(id, data) { return this.request("PUT", "/admin/books/" + id, data); },
    adminDeleteBook(id) { return this.request("DELETE", "/admin/books/" + id); },
    adminListChapters(bookId) { return this.request("GET", "/admin/books/" + bookId + "/chapters"); },
    adminCreateChapter(bookId, data) { return this.request("POST", "/admin/books/" + bookId + "/chapters", data); },
    adminUpdateChapter(id, data) { return this.request("PUT", "/admin/chapters/" + id, data); },
    adminDeleteChapter(id) { return this.request("DELETE", "/admin/chapters/" + id); },
    adminListKnowledgePoints(chapterId) { return this.request("GET", "/admin/chapters/" + chapterId + "/knowledge-points"); },
    adminCreateKnowledgePoint(chapterId, data) { return this.request("POST", "/admin/chapters/" + chapterId + "/knowledge-points", data); },
    adminUpdateKnowledgePoint(id, data) { return this.request("PUT", "/admin/knowledge-points/" + id, data); },
    adminDeleteKnowledgePoint(id) { return this.request("DELETE", "/admin/knowledge-points/" + id); },
    adminBulkImport(bookId, data) { return this.request("POST", "/admin/books/" + bookId + "/import", data); },
};

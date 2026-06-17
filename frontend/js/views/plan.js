/// SM-2 间隔重复
router.register("plans", async (mode, bookId) => {
    setPage("学习计划", "管理和查看学习计划");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>..</p></div>`;

    if (mode === "new" && bookId) {
        try {
            const book = await api.getBook(bookId);
            c.innerHTML = `
                <div class="card" style="max-width:540px">
                <div class="card-header">🚀 生成学习计划 - ${escHtml(book.title)}</div>
                    <div class="card-body">
                        <div class="form-group">
                            <label>学习天数</label>
                            <input class="form-control" id="planDays" type="number" min="1" max="365" value="14">
                        </div>
                        <div class="form-group">
                            <label>每天学习分钟数</label>
                            <input class="form-control" id="planMinutes" type="number" min="5" max="480" value="30">
                        </div>
                        <p class="text-sm text-secondary mb-16">复习将采用 SM-2 间隔重复算法</p>
                        <button class="btn btn-primary btn-lg" id="generatePlanBtn">🚀 生成计划</button>
                        <button class="btn btn-secondary" onclick="router.go('plans')">取消</button>
                        <div id="planProgress" class="mt-16" style="display:none">
                            <div class="progress-bar"><div class="progress-fill" style="width:0%"></div></div>
                        <p class="text-sm text-secondary mt-8" id="planStatus">准备好后点击生成</p>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById("generatePlanBtn").onclick = async () => {
                const days = parseInt(document.getElementById("planDays").value);
                const minutes = parseInt(document.getElementById("planMinutes").value);
                    if (!days || !minutes || days < 1 || minutes < 5) {
                        alert("请输入有效的天数和分钟数");
                    return;
                }
                const btn = document.getElementById("generatePlanBtn");
                const progress = document.getElementById("planProgress");
                btn.disabled = true;
                progress.style.display = "block";
                document.getElementById("planStatus").textContent = "生成中...";
                try {
                    const plan = await api.generatePlan(bookId, days, minutes);
                    document.getElementById("planStatus").textContent = `✅ 已生成计划「${plan.name}」`;
                    setTimeout(() => router.go("plans"), 1000);
                } catch (e) {
                    document.getElementById("planStatus").textContent = "❌ " + e.message;
                    btn.disabled = false;
                }
            };
        } catch (e) {
            c.innerHTML = `<div class="empty-state"><h3>📭</h3><p>${escHtml(e.message)}</p></div>`;
        }
        return;
    }

    // List all plans
    try {
        const plans = await api.listPlans();
        if (!plans.length) {
            c.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📅</div>
                    <h3>还没有学习计划</h3>
                    <p>从书库选择一本书，创建学习计划开始学习</p>
                    <button class="btn btn-primary mt-16" onclick="router.go('library')">📚 去书库</button>
                </div>
            `;
            return;
        }
        let html = "";
        for (const plan of plans) {
            const statusClass = `badge-${plan.status}`;
            html += `<div class="card mb-16">
                <div class="card-body">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 style="font-size:16px;font-weight:600">${escHtml(plan.name)}</h3>
                        <p class="text-sm text-secondary mt-8">
                            📅 ${plan.total_days} 天 · 每天 ${plan.daily_minutes} 分钟
                            🕐 ${new Date(plan.created_at).toLocaleDateString("zh-CN")}
                            </p>
                        </div>
                        <span class="badge ${statusClass}">${plan.status === "active" ? "进行中" : plan.status === "completed" ? "已完成" : plan.status}</span>
                    </div>
                    <div class="mt-8 flex gap-8">
                        <button class="btn btn-primary btn-sm" onclick="viewPlanDetail(${plan.id})">📖 查看详情</button>
                        <button class="btn btn-ghost btn-sm" onclick="deletePlan(${plan.id},this)" style="color:var(--danger)">🗑️ 删除</button>
                    </div>
                </div>
            </div>`;
        }
        c.innerHTML = html;
    } catch (e) {
        c.innerHTML = `<div class="empty-state"><h3>📭</h3><p>${escHtml(e.message)}</p></div>`;
    }
});

window.viewPlanDetail = async (planId) => {
    setPage("", "");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>..</p></div>`;

    try {
        const [plan, days, reviewStats] = await Promise.all([
            api.getPlan(planId),
            api.getPlanDays(planId),
            api.getReviewStats(planId),
        ]);
        setPage(plan.name, `${plan.total_days} 天计划 · 每天 ${plan.daily_minutes} 分钟`);

        // Review stats summary
        let html = `<div class="review-summary${reviewStats.total_reviews > 0 ? " has-data" : ""}">
            <div class="review-summary-item">
                <div class="review-stat-value">${reviewStats.total_reviews}</div>
                <div class="review-stat-label">已复习</div>
            </div>
            <div class="review-summary-item">
                <div class="review-stat-value">${reviewStats.pending_reviews}</div>
                <div class="review-stat-label">待复习</div>
            </div>
            <div class="review-summary-item">
                <div class="review-stat-value">${reviewStats.average_quality > 0 ? "⭐ " + reviewStats.average_quality.toFixed(1) : "—"}</div>
                <div class="review-stat-label">平均评分</div>
            </div>
            <div class="review-summary-item">
                <div class="review-stat-value" style="color:var(--primary)"> SM-2</div>
                <div class="review-stat-label">算法</div>
            </div>
        </div>`;

        html += `<div class="timeline" id="planTimeline">`;
        for (const day of days) {
            const dateStr = day.target_date ? new Date(day.target_date).toLocaleDateString("zh-CN", { month: "long", day: "numeric", weekday: "short" }) : "";
            const hasReview = day.items.some(i => i.item_type === "review");
            html += `<div class="timeline-item ${day.completed ? "completed" : ""} ${hasReview ? "has-review" : ""}" id="day-${day.day_number}">
        <div class="timeline-date">📅 第 ${day.day_number} 天 · ${dateStr}</div>
                <div class="timeline-title">${day.total_minutes} 分钟 · ${day.items.length} 项</div>
                <div class="timeline-meta">
                    <span class="badge ${day.completed ? "badge-completed" : "badge-active"}">${day.completed ? "✅ 已完成" : "⏳ 进行中"}</span>
                    ${!day.completed ? `<button class="btn btn-sm btn-success" onclick="completePlanDay(${planId},${day.id},${day.day_number})">✅ 标记完成</button>` : ""}
                </div>
                <div class="mt-8" style="padding-left:8px">`;
            for (const item of day.items) {
                const isReview = item.item_type === "review";
                const borderColor = item.completed ? "var(--success)" : (isReview ? "#8b5cf6" : "var(--primary)");
                const label = isReview ? '<span class="review-badge">🔄 复习</span>' : '<span class="learn-badge">📖 学习</span>';
                html += `<div class="plan-item ${isReview ? "plan-item-review" : ""}" style="border-left-color:${borderColor}">
                    <div style="display:flex;align-items:center;gap:6px">
                        ${label}
                        <span style="font-size:13px;font-weight:500">${escHtml(item.knowledge_point_title)}</span>
                    </div>
                    <div class="text-xs text-secondary" style="margin-top:2px">
                        ${escHtml(item.chapter_title)} · ${item.estimated_minutes} 分钟
                        ${item.completed ? ' ✅ 已完成' : ''}
                    </div>
                    ${!day.completed && isReview && !item.completed ? `
                        <div class="review-rating mt-8" id="rating-${item.id}">
                            <span class="text-xs text-secondary">复习评分：</span>
                            ${[1,2,3,4,5].map(q => `<button class="rating-btn" data-quality="${q}" onclick="rateReviewItem(${planId},${item.id},${q})">${q}</button>`).join("")}
                            <span class="text-xs text-secondary" style="margin-left:6px">(1= 完全不记得 · 5= 非常熟悉)</span>
                        </div>
                    ` : ''}
                    ${item.completed && isReview ? `
                    <div class="text-xs text-secondary mt-4">✅ 已完成复习</div>
                    ` : ''}
                </div>`;
            }
            html += `</div></div>`;
        }
        html += `</div>`;
        html += `<div class="mt-16"><button class="btn btn-secondary" onclick="router.go('plans')">🔙 返回计划列表</button></div>`;
        c.innerHTML = html;
    } catch (e) {
        c.innerHTML = `<div class="empty-state"><h3>📭</h3><p>${escHtml(e.message)}</p></div>`;
    }
    headerActions.innerHTML = `<button class="btn btn-secondary btn-sm" onclick="router.go('plans')">🔙 返回</button>`;
};

window.completePlanDay = async (planId, dayId, dayNumber) => {
    if (!confirm(`确定第 ${dayNumber} 天已完成所有学习内容？`)) return;
    try {
        await api.completeDay(planId, dayId);
        viewPlanDetail(planId);
    } catch (e) {
        alert("操作失败: " + e.message);
    }
};

window.rateReviewItem = async (planId, itemId, quality) => {
    const ratingDiv = document.getElementById("rating-" + itemId);
    if (ratingDiv) {
        ratingDiv.innerHTML = `<span class="text-xs text-secondary">..</span>`;
    }
    try {
        const result = await api.submitReview(planId, itemId, quality);
        if (ratingDiv) {
            const stars = "★".repeat(quality) + "☆".repeat(5 - quality);
            ratingDiv.innerHTML = `<span class="text-xs" style="color:var(--success)">✅ ${stars}</span>
                <span class="text-xs text-secondary">下次复习：${result.interval_days} 天后</span>`;
        }
    } catch (e) {
        if (ratingDiv) {
            ratingDiv.innerHTML = `<span class="text-xs" style="color:var(--danger)">评分失败: ${e.message}</span>`;
        }
    }
};

window.deletePlan = async (planId, btn) => {
    if (!confirm("确定要删除这个学习计划吗？")) return;
    btn.disabled = true;
    btn.textContent = "删除中...";
    try {
        await api.deletePlan(planId);
        router.go("plans");
    } catch (e) {
        alert("❌ " + e.message);
    }
};

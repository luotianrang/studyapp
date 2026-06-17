/// 📘 书籍详情
router.register("book-detail", async (bookId) => {
    setPage("", "");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>..</p></div>`;

    try {
        const [book, chapters] = await Promise.all([
            api.getBook(bookId),
            api.getChapters(bookId)
        ]);
        setPage(book.title, `${chapters.length} 章${book.status === "analyzed" ? " · 已分析" : ""}`);

        let html = `
            <div class="card mb-16">
                <div class="card-header">📘 ${escHtml(book.title)}</div>
                <div class="card-body">
                    <div class="flex gap-16">
                        <div><span class="text-secondary">👤 </span>${book.author || "未知作者"}</div>
                        <div><span class="text-secondary">📑 </span>${book.total_chapters || 0} 章</div>
                        <div><span class="text-secondary">📌 </span><span class="badge badge-${book.status}">${book.status}</span></div>
                    </div>
                    <div class="text-secondary mt-16">已自动生成分析结果，前端不再触发 AI 分析。</div>
                </div>
            </div>
            <div style="display:flex;gap:12px;margin-bottom:16px">
                <button class="btn btn-primary" id="showChaptersBtn">📖 章节列表</button>
                <button class="btn btn-secondary" id="showKpBtn" ${book.status !== "analyzed" ? "disabled" : ""}>📋 全部知识点</button>
                ${book.status === "analyzed" ? `<button class="btn btn-success" onclick="router.go('plans','new',${book.id})">🚀 生成计划</button>` : ""}
            </div>
            <div id="detailContent"></div>
        `;
        c.innerHTML = html;

        async function renderChapters() {
            const dc = document.getElementById("detailContent");
            dc.innerHTML = `<div class="text-center" style="padding:20px"><p>...</p></div>`;
            const chaps = await api.getChapters(bookId);
            let html = `<div class="card"><div class="card-body"><div class="table-wrapper"><table><thead><tr><th>#</th><th>章名称</th><th>状态</th><th>知识点</th><th></th></tr></thead><tbody>`;
            for (const ch of chaps) {
                const statusLabel = { pending: "⏳ 待处理", analyzing: "🔄 分析中", analyzed: "✅ 已分析", error: "❌ 错误" };
                html += `<tr>
                    <td>${ch.chapter_number}</td>
                    <td>${escHtml(ch.title)}</td>
                    <td><span class="badge badge-${ch.status}">${statusLabel[ch.status] || ch.status}</span></td>
                    <td>${ch.knowledge_point_count}</td>
                    <td>${ch.status === "analyzed" ? `<button class="btn btn-ghost btn-sm" onclick="showChapterKps(${ch.id},'${escHtml(ch.title)}')">📋 知识点</button>` : ""}</td>
                </tr>`;
            }
            html += `</tbody></table></div></div></div>`;
            dc.innerHTML = html;
        }

        async function renderAllKps() {
            const dc = document.getElementById("detailContent");
            dc.innerHTML = `<div class="text-center" style="padding:20px"><p>..</p></div>`;
            const kps = await api.getAllKnowledgePoints(bookId);
            if (!kps.length) {
                dc.innerHTML = `<div class="empty-state"><h3>📭 暂无知识点</h3></div>`;
                return;
            }
            let html = `<div class="card"><div class="card-body"><div class="grid-2">`;
            for (const kp of kps) {
                html += `<div class="kp-card">
                    <div class="kp-title">${escHtml(kp.title)}</div>
                    <div class="kp-desc">${escHtml(kp.description)}</div>
                    <div class="mt-8 flex gap-12 text-sm text-secondary">
                        <span>⭐ ${"★".repeat(kp.importance)}${"☆".repeat(5-kp.importance)}</span>
                        <span>⏱ ${kp.estimated_minutes} 分钟</span>
                    </div>
                </div>`;
            }
            html += `</div></div></div>`;
            dc.innerHTML = html;
        }

        document.getElementById("showChaptersBtn").onclick = renderChapters;
        document.getElementById("showKpBtn").onclick = renderAllKps;
        renderChapters();
    } catch (e) {
        c.innerHTML = `<div class="empty-state"><h3></h3><p>${escHtml(e.message)}</p></div>`;
    }
});

window.showChapterKps = async (chapterId, chapterTitle) => {
    const kps = await api.getKnowledgePoints(chapterId);
    let html = `<div class="card mt-8"><div class="card-header">${escHtml(chapterTitle)}</div><div class="card-body"><div class="grid-2">`;
    if (!kps.length) {
        html += `<p class="text-secondary">📭 暂无知识点</p>`;
    }
    for (const kp of kps) {
        html += `<div class="kp-card">
            <div class="kp-title">${escHtml(kp.title)}</div>
            <div class="kp-desc">${escHtml(kp.description)}</div>
            <div class="mt-8 flex gap-12 text-sm text-secondary">
                <span>⭐ ${"★".repeat(kp.importance)}${"☆".repeat(5-kp.importance)}</span>
                <span>⏱ ${kp.estimated_minutes} 分钟</span>
            </div>
        </div>`;
    }
    html += `</div></div></div>`;

    const modal = document.createElement("div");
    modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:1000;display:flex;align-items:center;justify-content:center;padding:32px";
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `<div style="background:#fff;border-radius:10px;max-width:800px;width:100%;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.2)">${html}</div>`;
    document.body.appendChild(modal);
};

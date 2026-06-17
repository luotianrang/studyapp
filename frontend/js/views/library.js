//  - 
router.register("library", async () => {
    setPage("Preset Books", "Browse books to start learning");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>Loading...</p></div>`;

    try {
        const [presetBooks, myBooks] = await Promise.all([
            api.listPresetBooks(),
            api.listMyLearningBooks()
        ]);
        const badge = document.querySelector("#book-count-badge");
        if (badge) badge.textContent = String(myBooks.length);

        const myBookIds = new Set(myBooks.map(b => b.id));

        if (presetBooks.length === 0) {
            c.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📚</div>
                    <div class="empty-title">书库暂无预设书籍</div>
                    <div class="empty-text">请前往后台管理添加预设书籍</div>
                </div>
            `;
            return;
        }

        let html = `<div class="books-grid">`;
        for (const book of presetBooks) {
            const isAdded = myBookIds.has(book.id);
            const canGeneratePlan = book.status === "analyzed";
            html += `
                <div class="book-card">
                    <div class="book-header">
                        <div class="book-title">${escHtml(book.title)}</div>
                        <div class="preset-badge">📌 预设</div>
                    </div>
                    <div class="book-info">
                        <div class="book-author">✍️ ${escHtml(book.author || '')}</div>
                        <div class="book-meta">
                            <span>📄 ${book.total_chapters || 0} 章</span>
                            <span style="margin-left:8px" class="text-secondary">${canGeneratePlan ? "已可生成计划" : "待分析"}</span>
                        </div>
                    </div>
                    <div class="book-actions">
                        ${isAdded 
                            ? `<button class="btn-detail" onclick="router.go('my-learning')" style="flex:1">📖 已加入</button>`
                            : `<button class="btn-add" onclick="library.addToMyLearning(${book.id})">➕ 加入学习</button>`
                        }
                        <button class="btn-detail" onclick="router.go('book-detail', ${book.id})">🔍 详情</button>
                    </div>
                </div>
            `;
        }
        html += `</div>`;
        c.innerHTML = html;
    } catch (e) {
        c.innerHTML = `<div class="empty-state"><h3></h3><p>${escHtml(e.message)}</p></div>`;
    }
});

const library = {
    async addToMyLearning(bookId) {
        try {
            await api.addToMyLearning(bookId);
            router.go('library');
        } catch (e) {
            alert('操作失败: ' + e.message);
        }
    }
};

// 
router.register("my-learning", async () => {
    setPage("我的学习", "已加入的学习书籍");
    const c = pageContent;
    c.innerHTML = `<div class="text-center" style="padding:40px"><p>..</p></div>`;

    try {
        const books = await api.listMyLearningBooks();
        const badge = document.querySelector("#book-count-badge");
        if (badge) badge.textContent = String(books.length);

        if (books.length === 0) {
            c.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon"></div>
                    <div class="empty-title">还没有加入学习</div>
                    <div class="empty-text">去书库浏览预设书籍，开始你的学习之旅</div>
                    <button class="btn btn-primary mt-16" onclick="router.go('library')">📚 去书库</button>
                </div>
            `;
            return;
        }

        let html = `<div class="books-grid">`;
        for (const book of books) {
            html += `
                <div class="book-card">
                    <div class="book-header">
                        <div class="book-title">${escHtml(book.title)}</div>
                        <div class="preset-badge">📌 已加入</div>
                    </div>
                    <div class="book-info">
                        <div class="book-author">✍️ ${escHtml(book.author || '')}</div>
                        <div class="book-meta">
                            <span>📄 ${book.total_chapters || 0} 章</span>
                        </div>
                    </div>
                    <div class="book-actions">
                        <button class="btn-add" onclick="router.go('book-detail', ${book.id})">📖 查看详情</button>
                        <button class="btn-detail" onclick="myLearning.removeBook(${book.id})" style="color:var(--danger);border-color:var(--danger)">🗑️ 移除</button>
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

const myLearning = {
    async removeBook(bookId) {
        if (!confirm('确定从我的学习中移除这本书吗？')) return;
        try {
            await api.removeFromMyLearning(bookId);
            if (typeof refreshBookCountBadge === "function") {
                await refreshBookCountBadge();
            }
            router.go('my-learning');
        } catch (e) {
            alert('操作失败: ' + e.message);
        }
    }
};

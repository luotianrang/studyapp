/// 管理后台 - 书籍/章节/知识点
const admin = {
    _state: null, // { view: "books"|"chapters"|"kps", bookId, bookTitle, chapterId, chapterTitle }

    // ---- Render functions ----

    async renderBooks() {
        const c = pageContent;
        c.innerHTML = `<div class="text-center" style="padding:40px"><span class="spinner"></span> 加载中...</div>`;
        try {
            const books = await api.adminListBooks();
            let html = `
                <div class="admin-toolbar">
                    <div class="admin-toolbar-title">📚 预设书籍</div>
                    <button class="btn btn-primary btn-sm" onclick="admin.showBookModal()">＋ 添加书籍</button>
                </div>
            `;
            if (books.length === 0) {
                html += `<div class="empty-state"><div class="empty-icon">📚</div><div class="empty-title">暂无预设书籍</div><div class="empty-text">点击上方按钮添加第一本书</div></div>`;
            } else {
                html += `<div class="admin-section"><div class="table-wrapper"><table>
                    <thead><tr>
                        <th style="width:40px">#</th>
                        <th>书名</th>
                        <th style="width:120px">作者</th>
                        <th style="width:80px">章节</th>
                        <th style="width:100px">状态</th>
                        <th style="width:200px">操作</th>
                    </tr></thead><tbody>
                `;
                for (const b of books) {
                    html += `<tr>
                        <td>${b.id}</td>
                        <td><strong>${escHtml(b.title)}</strong></td>
                        <td>${escHtml(b.author || "-")}</td>
                        <td>${b.total_chapters || 0}</td>
                        <td><span class="badge badge-${b.status}">${b.status}</span></td>
                        <td>
                            <button class="btn btn-ghost btn-sm" onclick="admin.editBook(${b.id})" title="编辑">✏</button>
                            <button class="btn btn-ghost btn-sm" onclick="admin.renderChapters(${b.id}, '${escHtml(b.title).replace(/'/g, "\\'")}')" title="章节管理">📖</button>
                            <button class="btn btn-ghost btn-sm" style="color:var(--danger)" onclick="admin.deleteBook(${b.id})" title="删除">🗑</button>
                        </td>
                    </tr>`;
                }
                html += `</tbody></table></div></div>`;
            }
            c.innerHTML = html;
            admin._state = { view: "books" };
        } catch (e) {
            c.innerHTML = `<div class="empty-state"><h3>加载失败</h3><p>${escHtml(e.message)}</p></div>`;
        }
    },

    async renderChapters(bookId, bookTitle) {
        admin._state = { view: "chapters", bookId, bookTitle };
        const c = pageContent;
        c.innerHTML = `<div class="text-center" style="padding:40px"><span class="spinner"></span> 加载中...</div>`;
        try {
            const chapters = await api.adminListChapters(bookId);
            let html = `
                <div class="admin-toolbar">
                    <button class="btn btn-ghost btn-sm" onclick="admin.renderBooks()" title="返回">← 返回</button>
                    <div class="admin-toolbar-title">📖 ${escHtml(bookTitle)} - 章节管理</div>
                    <div style="display:flex;gap:8px">
                        <button class="btn btn-secondary btn-sm" onclick="admin.showImportModal(${bookId}, '${escHtml(bookTitle).replace(/'/g, "\\'")}')">↑ 批量导入</button>
                        <button class="btn btn-primary btn-sm" onclick="admin.showChapterModal(${bookId})">＋ 添加章节</button>
                    </div>
                </div>
            `;
            if (chapters.length === 0) {
                html += `<div class="empty-state"><div class="empty-icon">📖</div><div class="empty-title">暂无章节</div><div class="empty-text">点击"添加章节"或"批量导入"来添加内容</div></div>`;
            } else {
                html += `<div class="admin-section"><div class="table-wrapper"><table>
                    <thead><tr>
                        <th style="width:50px">#</th>
                        <th>章节名称</th>
                        <th style="width:80px">知识点</th>
                        <th style="width:100px">状态</th>
                        <th style="width:240px">操作</th>
                    </tr></thead><tbody>
                `;
                for (const ch of chapters) {
                    html += `<tr>
                        <td>${ch.chapter_number}</td>
                        <td>${escHtml(ch.title)}</td>
                        <td>${ch.knowledge_point_count}</td>
                        <td><span class="badge badge-${ch.status}">${ch.status}</span></td>
                        <td>
                            <button class="btn btn-ghost btn-sm" onclick="admin.editChapter(${ch.id})" title="编辑">✏</button>
                            <button class="btn btn-ghost btn-sm" onclick="admin.renderKps(${ch.id}, '${escHtml(ch.title).replace(/'/g, "\\'")}')" title="知识点">⊕</button>
                            <button class="btn btn-ghost btn-sm" style="color:var(--danger)" onclick="admin.deleteChapter(${ch.id}, ${bookId}, '${escHtml(bookTitle).replace(/'/g, "\\'")}')" title="删除">🗑</button>
                        </td>
                    </tr>`;
                }
                html += `</tbody></table></div></div>`;
            }
            c.innerHTML = html;
        } catch (e) {
            c.innerHTML = `<div class="empty-state"><h3>加载失败</h3><p>${escHtml(e.message)}</p></div>`;
        }
    },

    async renderKps(chapterId, chapterTitle) {
        const st = admin._state;
        if (!st || st.view !== "chapters") return;
        admin._state = { view: "kps", bookId: st.bookId, bookTitle: st.bookTitle, chapterId, chapterTitle };
        const c = pageContent;
        c.innerHTML = `<div class="text-center" style="padding:40px"><span class="spinner"></span> 加载中...</div>`;
        try {
            const kps = await api.adminListKnowledgePoints(chapterId);
            let html = `
                <div class="admin-toolbar">
                    <button class="btn btn-ghost btn-sm" onclick="admin.renderChapters(${st.bookId}, '${escHtml(st.bookTitle).replace(/'/g, "\\'")}')" title="返回">← 返回</button>
                    <div class="admin-toolbar-title">📚 ${escHtml(chapterTitle)} - 知识点</div>
                    <button class="btn btn-primary btn-sm" onclick="admin.showKpModal(${chapterId})">＋ 添加知识点</button>
                </div>
            `;
            if (kps.length === 0) {
                html += `<div class="empty-state"><div class="empty-icon">📝</div><div class="empty-title">暂无知识点</div><div class="empty-text">点击"添加知识点"来创建第一个知识点</div></div>`;
            } else {
                html += `<div class="admin-section"><div class="table-wrapper"><table>
                    <thead><tr>
                        <th style="width:40px">顺序</th>
                        <th>知识点名称</th>
                        <th>描述</th>
                        <th style="width:80px">重要性</th>
                        <th style="width:70px">分钟</th>
                        <th style="width:160px">操作</th>
                    </tr></thead><tbody>
                `;
                for (const kp of kps) {
                    const importanceStars = "⭐".repeat(Math.min(kp.importance, 5));
                    html += `<tr>
                        <td>${kp.order_index}</td>
                        <td><strong>${escHtml(kp.title)}</strong></td>
                        <td class="text-secondary" style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(kp.description)}</td>
                        <td title="${kp.importance}/5">${importanceStars}</td>
                        <td>${kp.estimated_minutes}</td>
                        <td>
                            <button class="btn btn-ghost btn-sm" onclick="admin.editKp(${kp.id})" title="编辑">✏</button>
                            <button class="btn btn-ghost btn-sm" style="color:var(--danger)" onclick="admin.deleteKp(${kp.id}, ${chapterId}, '${escHtml(chapterTitle).replace(/'/g, "\\'")}')" title="删除">🗑</button>
                        </td>
                    </tr>`;
                }
                html += `</tbody></table></div></div>`;
            }
            c.innerHTML = html;
        } catch (e) {
            c.innerHTML = `<div class="empty-state"><h3>加载失败</h3><p>${escHtml(e.message)}</p></div>`;
        }
    },

    // ---- Books CRUD UI ----
    showBookModal(bookData) {
        const isEdit = !!bookData;
        buildModal(isEdit ? "✏ 编辑书籍" : "＋ 添加书籍", `
            <div class="form-group">
                <label>书名 *</label>
                <input class="form-control" id="bookTitle" value="${isEdit ? escHtml(bookData.title) : ""}" placeholder="输入书籍名称">
            </div>
            <div class="form-group">
                <label>作者</label>
                <input class="form-control" id="bookAuthor" value="${isEdit ? escHtml(bookData.author) : ""}" placeholder="输入作者（可选）">
            </div>
        `, async () => {
            const title = document.getElementById("bookTitle").value.trim();
            if (!title) { alert("请输入书名"); return; }
            const author = document.getElementById("bookAuthor").value.trim();
            if (isEdit) {
                await api.adminUpdateBook(bookData.id, { title, author });
            } else {
                await api.adminCreateBook({ title, author });
            }
            admin.closeModal("adminModalOverlay");
            admin.renderBooks();
        });
    },

    async editBook(bookId) {
        const books = await api.adminListBooks();
        const book = books.find(b => b.id === bookId);
        if (book) admin.showBookModal(book);
    },

    async deleteBook(bookId) {
        if (!confirm("确定要删除这本书吗？所有章节和知识点也将被删除。")) return;
        try {
            await api.adminDeleteBook(bookId);
            admin.renderBooks();
        } catch (e) {
            alert("删除失败: " + e.message);
        }
    },

    // ---- Chapters CRUD UI ----
    showChapterModal(bookId, chapterData) {
        const isEdit = !!chapterData;
        buildModal(isEdit ? "✏ 编辑章节" : "＋ 添加章节", `
            <div class="form-group">
                <label>章节名称 *</label>
                <input class="form-control" id="chTitle" value="${isEdit ? escHtml(chapterData.title) : ""}" placeholder="输入章节名称">
            </div>
            <div class="form-group">
                <label>章节编号</label>
                <input class="form-control" id="chNumber" type="number" value="${isEdit ? chapterData.chapter_number : ""}" placeholder="如 1, 2, 3 ...">
            </div>
            <div class="form-group">
                <label>章节内容</label>
                <textarea class="form-control" id="chContent" rows="4" placeholder="章节概述或内容（可选）">${isEdit ? escHtml(chapterData.content || "") : ""}</textarea>
            </div>
        `, async () => {
            const title = document.getElementById("chTitle").value.trim();
            if (!title) { alert("请输入章节名称"); return; }
            const chNumber = parseInt(document.getElementById("chNumber").value) || 0;
            const content = document.getElementById("chContent").value;
            if (isEdit) {
                await api.adminUpdateChapter(chapterData.id, { title, chapter_number: chNumber, content });
            } else {
                await api.adminCreateChapter(bookId, { title, chapter_number: chNumber, content });
            }
            admin.closeModal("adminModalOverlay");
            const st = admin._state;
            if (st && st.view === "chapters") {
                admin.renderChapters(st.bookId, st.bookTitle);
            }
        });
    },

    async editChapter(chapterId) {
        const st = admin._state;
        if (!st || !st.bookId) return;
        const chapters = await api.adminListChapters(st.bookId);
        const ch = chapters.find(c => c.id === chapterId);
        if (ch) admin.showChapterModal(st.bookId, ch);
    },

    async deleteChapter(chapterId, bookId, bookTitle) {
        if (!confirm("确定要删除这个章节吗？知识点也将被删除。")) return;
        try {
            await api.adminDeleteChapter(chapterId);
            admin.renderChapters(bookId, bookTitle);
        } catch (e) {
            alert("删除失败: " + e.message);
        }
    },

    // ---- Knowledge Points CRUD UI ----
    showKpModal(chapterId, kpData) {
        const isEdit = !!kpData;
        buildModal(isEdit ? "✏ 编辑知识点" : "＋ 添加知识点", `
            <div class="form-group">
                <label>知识点名称 *</label>
                <input class="form-control" id="kpTitle" value="${isEdit ? escHtml(kpData.title) : ""}" placeholder="输入知识点名称">
            </div>
            <div class="form-group">
                <label>描述</label>
                <textarea class="form-control" id="kpDesc" rows="3" placeholder="知识点简要描述（可选）">${isEdit ? escHtml(kpData.description || "") : ""}</textarea>
            </div>
            <div style="display:flex;gap:12px">
                <div class="form-group" style="flex:1">
                    <label>重要性 (1-5)</label>
                    <input class="form-control" id="kpImportance" type="number" min="1" max="5" value="${isEdit ? kpData.importance : 3}">
                </div>
                <div class="form-group" style="flex:1">
                    <label>学习分钟</label>
                    <input class="form-control" id="kpMinutes" type="number" min="1" value="${isEdit ? kpData.estimated_minutes : 10}">
                </div>
                <div class="form-group" style="flex:1">
                    <label>排序</label>
                    <input class="form-control" id="kpOrder" type="number" min="0" value="${isEdit ? kpData.order_index : 0}">
                </div>
            </div>
        `, async () => {
            const title = document.getElementById("kpTitle").value.trim();
            if (!title) { alert("请输入知识点名称"); return; }
            const desc = document.getElementById("kpDesc").value;
            const importance = parseInt(document.getElementById("kpImportance").value) || 3;
            const minutes = parseInt(document.getElementById("kpMinutes").value) || 10;
            const order = parseInt(document.getElementById("kpOrder").value) || 0;
            if (isEdit) {
                await api.adminUpdateKnowledgePoint(kpData.id, {
                    title, description: desc, importance,
                    estimated_minutes: minutes, order_index: order
                });
            } else {
                await api.adminCreateKnowledgePoint(chapterId, {
                    title, description: desc, importance,
                    estimated_minutes: minutes, order_index: order
                });
            }
            admin.closeModal("adminModalOverlay");
            const st = admin._state;
            if (st && st.view === "kps") {
                admin.renderKps(st.chapterId, st.chapterTitle);
            }
        });
    },

    async editKp(kpId) {
        const st = admin._state;
        if (!st || !st.chapterId) return;
        const kps = await api.adminListKnowledgePoints(st.chapterId);
        const kp = kps.find(k => k.id === kpId);
        if (kp) admin.showKpModal(st.chapterId, kp);
    },

    async deleteKp(kpId, chapterId, chapterTitle) {
        if (!confirm("确定要删除这个知识点吗？")) return;
        try {
            await api.adminDeleteKnowledgePoint(kpId);
            admin.renderKps(chapterId, chapterTitle);
        } catch (e) {
            alert("删除失败: " + e.message);
        }
    },

    // ---- Bulk Import UI ----
    showImportModal(bookId, bookTitle) {
        buildModal("↑ 批量导入章节和知识点", `
            <div style="margin-bottom:16px">
                <p class="text-sm text-secondary">上传 JSON 文件批量导入章节和知识点，文件格式示例：</p>
                <pre style="background:var(--bg);padding:12px;border-radius:var(--radius-sm);font-size:12px;overflow-x:auto;margin-top:8px">{
  "chapters": [
    {
      "title": "第一章",
      "chapter_number": 1,
      "content": "章节内容概述",
      "knowledge_points": [
        { "title": "知识点1", "description": "描述", "importance": 3, "estimated_minutes": 10 }
      ]
    }
  ]
}</pre>
            </div>
            <div class="form-group">
                <label>选择 JSON 文件</label>
                <input class="form-control" type="file" id="importFileInput" accept=".json,application/json" style="padding:8px">
            </div>
            <div id="importPreview" style="display:none;margin-top:12px">
                <p class="text-sm" id="importInfo"></p>
            </div>
        `, async () => {
            const fileInput = document.getElementById("importFileInput");
            if (!fileInput.files || !fileInput.files[0]) {
                alert("请选择一个 JSON 文件");
                return;
            }
            try {
                const text = await fileInput.files[0].text();
                const data = JSON.parse(text);
                if (!data.chapters || !Array.isArray(data.chapters) || data.chapters.length === 0) {
                    alert("JSON 文件中必须包含 chapters 数组");
                    return;
                }
                const result = await api.adminBulkImport(bookId, data);
                admin.closeModal("adminModalOverlay");
                alert(result.message || "导入成功");
                admin.renderChapters(bookId, bookTitle);
            } catch (e) {
                alert("导入失败: " + (e.message || "请检查文件格式"));
            }
        }, "导入");
    },

    // ---- Utilities ----
    closeModal(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
};

// Helper to build modal HTML
function buildModal(title, bodyHtml, onSave, saveText) {
    const id = "adminModalOverlay";
    const existing = document.getElementById(id);
    if (existing) existing.remove();

    const html = `
        <div class="modal-overlay" id="${id}">
            <div class="modal">
                <div class="modal-header">${title}</div>
                <div class="modal-body">${bodyHtml}</div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="admin.closeModal('${id}')">取消</button>
                    <button class="btn btn-primary" id="adminModalSaveBtn">${saveText || (title.startsWith("✏") ? "保存" : "创建")}</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML("beforeend", html);
    document.getElementById("adminModalSaveBtn").onclick = onSave;
}

// Register admin route
router.register("admin", () => {
    setPage("管理后台", "管理预设书籍、章节和知识点");
    // Clear any stale chapter/KP state when entering admin from sidebar
    const st = admin._state;
    if (st && st.view !== "books") {
        admin._state = null;
    }
    admin.renderBooks();
});

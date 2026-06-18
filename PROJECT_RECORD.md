# 项目长期档案：学习助手 StudyApp

> 最后更新：2026-06-16
> 本文档为长期项目档案，记录版本历史和报错修复经验。
> 日常开发请阅读 CURRENT_STATE.md 和 NEXT_TASKS.md。
> 开发规范见 AGENT_RULES.md。

---

## 项目概况

一个「预设书库 + 我的学习」的在线学习工具——管理员整理好书籍的章节和知识点（通过 DOCX 导入或后台管理），用户浏览书库、加入学习、生成学习计划、每日学习并跟踪进度。

技术栈：Python FastAPI + SQLite + 原生 HTML/CSS/JS SPA

---

## 版本历史

### 2026-06-18 —— 调度系统升级：capacity-aware scheduler + review protection + effective_days

背景：原多书 scheduler 更像“按分数排序的任务投放器”，没有真正的分钟容量约束。实际问题包括：单日过载、短学习时长下计划不现实、review 在容量紧张时可能被普通学习挤掉，同时 `StudyPlan.total_days` 仍保存用户请求值，和实际生成天数不一致。

改动清单：
1. 升级 `backend/services/scheduler/interleaved_scheduler.py`，引入按分钟约束的 daily capacity model
2. 所有 task 在进入最终分配前统一补齐时长估算，缺失时回退到默认分钟数
3. 容量分配层新增 overflow handling：不再按任务数限制，而是按分钟检查剩余容量
4. 接入 review protection layer：review 先于 learning 分配，不参与普通 learning 的 push delay 逻辑
5. 约束 review 延迟上限：超过 1 天未安排时在后续分配中强制优先处理
6. 将长任务拆分升级为 session-based splitting：优先同日连续安排，超出日容量时跨天拆分，限制 session 过碎
7. 新增 `StudyPlan.effective_days` 字段，保留 `total_days` 为用户请求语义，`effective_days` 表示实际生成天数
8. 更新 `backend/database.py` 自动迁移逻辑，为旧库补 `effective_days` 列
9. 更新 `backend/schemas.py` / `backend/services/plan_service.py`，向 API 返回 `effective_days`，并对历史计划做兼容回填
10. 修复本机 Python 调用链：确认使用 `py -3.13` 启动解释器，并安装 `pytest`
11. 本地验证通过：`py -3.13 -m pytest backend/tests/test_spaced_repetition_integration.py backend/tests/test_plan_service_scheduler_routing.py`

涉及文件：
- backend/database.py
- backend/models.py
- backend/schemas.py
- backend/services/plan_service.py
- backend/services/scheduler/interleaved_scheduler.py
- backend/tests/test_plan_service_scheduler_routing.py
- backend/tests/test_spaced_repetition_integration.py
- CURRENT_STATE.md / NEXT_TASKS.md / PROJECT_RECORD.md

### 2026-06-18 —— 公网修复：预设书库自动恢复 + 书籍详情知识点显示恢复

背景：Railway 公网环境在空数据库或重建后，预设书库丢失；同时书籍详情页把“全部知识点”错误绑定到 `status === analyzed`，导致知识点数据存在时也可能看不到按钮。

改动清单：
1. 新增 `backend/services/seed_service.py`，启动时为空库自动补种两本高数预设书
2. 新增 `backend/preset_books_seed.json`，将两本预设书的章节与知识点纳入仓库
3. `backend/main.py` 启动阶段接入自动补种逻辑
4. 修复 `backend/services/admin_service.py` 批量导入逻辑，导入时保留已有知识点而不是重新生成空分析
5. 扩展 `backend/schemas.py` 中 `ChapterImport`，允许保留章节状态
6. 修复 `frontend/js/views/book-detail.js`，按真实 `knowledge_point_count` 决定是否显示“全部知识点”和“生成计划”
7. 推送到 GitHub `main` 并由 Railway 自动部署
8. 公网验证恢复成功：上册 7 章 124 个知识点，下册 5 章 50 个知识点

涉及文件：
- backend/main.py
- backend/schemas.py
- backend/services/admin_service.py
- backend/services/seed_service.py
- backend/preset_books_seed.json
- frontend/js/views/book-detail.js
- CURRENT_STATE.md / NEXT_TASKS.md

### 2026-06-16 —— 产品重构：从「上传分析」到「预设书库」

背景：上传 PDF 分析太慢、质量不稳定，用户体验不好。

改动清单：
1. 删除上传书籍功能及相关页面
2. 新增「我的学习」页面（侧边栏独立入口，设为默认首页）
3. 重写书库页面，改为纯预设书籍展示 + 「加入学习」按钮
4. 删除书库中的标签页（原合并模式）
5. 新增 UserBook 模型和 API（加入学习 / 移除 / 列表）
6. 修复 api.js 中 10 个断掉的接口 URL
7. 修复多个 Python 文件的引号转义错误和相对导入路径
8. 重写 analysis.py，保留知识点查询接口
9. 导入《高数下册》知识图谱（5章50个知识点）

---

## 报错与修复记录

### #1 start.bat 乱码
- 现象：双击后中文乱码，批处理无法执行
- 原因：PowerShell Out-File 写入 BOM，批处理把 BOM 当命令执行
- 修复：用 WriteAllText 无 BOM 写入；后改为纯 ASCII 内容

### #2 批处理行尾 LF
- 现象：报错 "'rst' 不是内部或外部命令" 等碎片化错误
- 原因：PowerShell 写入文件行尾是 LF，CMD 要求 CRLF
- 修复：写入时用 \r\n 确保 CRLF，首字节验证无 BOM

### #3 api.js URL 误写为正则表达式
- 现象：接口 404 或参数未传递
- 原因：10 处接口 URL 使用了正则字面量而非模板字符串
- 涉及方法：addToMyLearning, removeFromMyLearning, getBook, getChapters, getKnowledgePoints, getAllKnowledgePoints, getPlan, getPlanDays, completeDay, deletePlan
- 修复：全部改用模板字符串（反引号）

### #4 Python 引号转义错误
- 现象：SyntaxError: unexpected character after line continuation character
- 原因：文件中写入了 \" 而非 "
- 涉及文件：main.py, database.py
- 修复：全局替换 \" 为 "

### #5 Python 导入路径错误
- 现象：ImportError: attempted relative import
- 原因：analysis.py 使用 from models import 而非 from ..models import
- 修复：统一改为相对导入

### #6 python-docx 样式名含空格
- 现象：DOCX 章节检测不到，导入为 0
- 原因：样式名是 'Heading 1'（带空格）而非 'Heading1'
- 修复：导入脚本中样式名改为 "Heading 1" / "Heading 2"

### #7 PowerShell 与 Python 字符串冲突
- 现象：中文+特殊字符在 python -c 中频繁出错
- 原因：PowerShell ${} 与 Python f-string 冲突；中文路径可能被截断
- 修复：复杂脚本优先用 Node.js MCP 的 fs.writeFileSync 写入文件再执行

---

## 文件结构变更记录

> 文件结构的当前版本见 CURRENT_STATE.md，此处仅记录重大变更。

### 2026-06-16 变更
- 删除：upload.html, upload.js（上传页面）
- 新增：views/my-learning.js（我的学习）
- 重写：views/library.js（书库改为纯预设展示）
- 新增：backend/routers/books.py（含 UserBook API）
- 新增：CURRENT_STATE.md, NEXT_TASKS.md, AGENT_RULES.md（项目文档拆分）

### 2026-06-17 —— 实现：用户注册/登录 + 全 API user_id 隔离

背景：之前无多用户支持，user_id 固定为 1。所有用户的计划、通知设置混在一起。

改动清单：
1. StudyPlan 和 NotificationSetting 模型添加 user_id 列
2. plan.py 所有端点接入 get_current_user（create_plan 写入 user_id，list_plans 按 user 过滤，其余端点校验归属）
3. notifications.py 按 user_id 隔离通知设置
4. database.py 集成迁移逻辑（ALTER TABLE 自动添加列，不丢数据）
5. 前端无改动（login.v4.js / api.js / app.v5.js 原已支持 JWT 流程）

涉及文件：
- backend/models.py —— 加 user_id 列
- backend/routers/plan.py —— 全面改写，消除 user_id=1 硬编码
- backend/routers/notifications.py —— 接入 get_current_user
- backend/database.py —— 添加 _add_column_if_missing 迁移函数
- CURRENT_STATE.md / NEXT_TASKS.md —— 文档更新


### 2026-06-17 变更
- 新增：backend/auth.py（JWT 鉴权工具）
- 新增：backend/routers/auth.py（注册/登录/me 路由）
- 新增：frontend/js/views/login.v4.js（前端登录注册页面）
- 修改：backend/database.py（集成数据库迁移）
- 修改：backend/routers/plan.py（用户隔离）
- 修改：backend/routers/notifications.py（用户隔离）

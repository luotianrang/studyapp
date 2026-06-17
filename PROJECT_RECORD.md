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

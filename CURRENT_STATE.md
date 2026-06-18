# 当前项目状态
> 最后更新：2026-06-18
> 日常维护优先阅读本文档和 `NEXT_TASKS.md`
---

## 基本信息

| 项目 | 内容 |
|------|------|
| 项目名称 | 学习助手 StudyApp |
| 代码路径 | `C:/Users/28618/Desktop/学习app` |
| 启动方式 | 双击 `start.bat`，或 `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8899` |
| 本地地址 | http://localhost:8899 |
| 公网地址 | https://studyapp-production-b848.up.railway.app |
| 技术栈 | Python FastAPI + SQLite + 原生 HTML/CSS/JS SPA |
| 用户认证 | JWT（`python-jose` + `bcrypt`） |
| 部署方式 | GitHub + Railway 自动部署 |
| 公网部署现状 | 已通过 Railway + GitHub 仓库自动部署并可访问 |

---

## 当前结论

项目已完成，当前处于可维护、可继续迭代状态。
当前已具备以下能力：

1. 用户注册、登录、鉴权隔离
2. 预设书库浏览、加入学习、书籍详情查看
3. 学习计划生成、查看、完成标记
4. 后台书籍 / 章节 / 知识点管理
5. 通知设置
6. 统一日志系统
7. Git 仓库管理与 Railway 公网部署
8. 本地 AI 自动分析架构
9. Railway 新环境空库时自动补种两本预设数学书
10. 书籍详情页可按真实知识点数量显示“全部知识点”和“生成计划”
11. 多书交叉学习调度已接入计划生成主流程，`book_ids` > 1 时启用交叉调度
12. 学习计划主流程已固定分流：单书严格走旧 `generate_plan()`，多书唯一走新 scheduler pipeline
13. 已新增最小回归测试，锁定单书/多书分流逻辑

---

## 当前公网数据

当前 Railway 公网实例已恢复两本预设书：
1. 《高等数学上册 知识图谱_全书版》：7 章，124 个知识点
2. 《高等数学（下册）知识图谱全书版（同济体系）》：5 章，50 个知识点

当前已验证：

1. `/api/books/preset` 可返回两本书
2. `/api/books/{book_id}/chapters` 可返回章节及 `knowledge_point_count`
3. `/api/analysis/knowledge-points/{chapter_id}` 可返回真实知识点数据
4. 书籍详情页“全部知识点”按钮已按知识点数量启用
5. 学习计划支持多书勾选创建
6. 本次调度升级后，单书旧逻辑、多书新调度的主流程已在代码中固定

---

## 当前产品页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 我的学习 | `my-learning` | 用户已加入学习的书籍列表 |
| 书库 | `library` | 预设书库展示和加入学习 |
| 学习计划 | `plans` | 计划生成、查看与管理 |
| 设置 | `settings` | 本地自动分析说明与通知设置 |
| 后台管理 | `admin` | 管理预设书籍、章节、知识点 |
| 书籍详情 | `book-detail` | 查看章节与知识点结果 |

---

## AI 架构现状

当前系统已从“前端触发 DeepSeek 分析”切换为“后端自动本地分析”。

### 当前规则

1. 不再要求用户输入 API Key
2. 不再依赖外部 DeepSeek API
3. 创建章节、批量导入时自动执行分析
4. 优先使用 Ollama 本地模型
5. 若本地模型不可用，自动使用规则分析 fallback
6. 前端仅展示分析结果，不再触发 AI

---

## 当前维护建议

1. 后续新开 Codex 项目时，直接进入该 Git 仓库根目录即可继续维护
2. 日常修改优先更新 `CURRENT_STATE.md` 和 `NEXT_TASKS.md`
3. 若继续上线，保持 `main` 分支推送到 GitHub，由 Railway 自动部署
4. 若 Docker 环境没有 Ollama，系统会自动走 fallback，不影响运行
5. Railway 若重建数据库，启动时会自动恢复预设书库
6. 当前公网后台管理接口仍未加鉴权，下一步建议优先补安全保护
7. 学习计划接口已支持 `book_ids`，单书与多书分流规则已固定并已补最小回归测试

## 2026-06-18 更新
- 学习计划分流已固定为：单书走旧 generate_plan，多书走新 scheduler pipeline。
- 已补最小回归测试，锁定分流行为。

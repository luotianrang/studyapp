# 当前项目状态
> 最后更新：2026-06-18
> 日常维护优先阅读本文档和 `NEXT_TASKS.md`
---

## 基本信息

| 项目 | 内容 |
|------|------|
| 项目名称 | 学习助手 StudyApp |
| 代码路径 | `C:/Users/28618/Desktop/学习app` |
| 启动方式 | 双击 `start.bat`，或 `py -3.13 -m uvicorn backend.main:app --host 0.0.0.0 --port 8899` |
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
14. 多书 scheduler 已升级为 capacity-aware scheduling：按分钟容量分配，不再只是排序系统
15. review protection layer 已接入容量分配层：review 先排、延迟受限、容量紧张时优先保护 review
16. 超长学习任务已切换为 session-based splitting：优先同日连续安排，超出日容量时跨天拆分，限制 session 过碎
17. StudyPlan 已拆分 `total_days` 与 `effective_days` 语义：前者保留用户请求天数，后者记录实际生成天数
18. 本地 Python 3.13 与 pytest 已验证可用，调度相关测试当前通过

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
7. 本次公网已上线新的 capacity-aware scheduler、review protection layer 与 `effective_days` 返回字段

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
8. 计划接口现同时返回 `total_days`（用户请求）与 `effective_days`（实际计划天数），兼容旧字段
9. 本地测试命令当前推荐使用 `py -3.13 -m pytest`

## 2026-06-18 更新
- 学习计划分流已固定为：单书走旧 generate_plan，多书走新 scheduler pipeline。
- 已补最小回归测试，锁定分流行为。

## 2026-06-18 更新
- 多书学习调度已接入 Spaced Repetition，支持学习+复习一体化排序。
- 单书仍走旧 generate_plan，多书走新 scheduler pipeline。

## 2026-06-18 更新
- 多书调度已升级为 capacity-aware scheduler：按分钟容量分配，支持 session-based splitting，避免单日过载。
- review protection layer 已上线：review 先排、容量紧张时优先保护 review，超过 1 天延迟后强制优先处理。
- StudyPlan 新增 `effective_days`，用于表示实际生成天数；`total_days` 保持用户请求语义不变。
- 已在本地用 `py -3.13 -m pytest` 跑通调度相关 11 条测试。

## 2026-06-18 Update (UTF-8 Append)
- Added a planning layer before scheduling to estimate total workload from learning load plus spaced-review load.
- Plan generation is now primarily driven by `daily_minutes`; the system auto-derives `recommended_days` and uses that horizon for scheduling.
- Existing scheduler architecture remains in place: interleaved learning/review, capacity-aware day filling, review protection, and session splitting are preserved.
- `StudyPlan.total_days` now stores the auto-derived plan duration, while `effective_days` still reflects the realized scheduled span.
- Local verification passed: `py -3.13 -m pytest backend/tests/test_planning_layer.py backend/tests/test_spaced_repetition_integration.py backend/tests/test_plan_service_scheduler_routing.py`

## 2026-06-19 Update (UTF-8 Append)
- Upgraded the study-planning internals with a learning state machine while preserving the existing API surface and scheduler entrypoints.
- Added `backend/services/scheduler/learning_state_machine.py` to model `UNLEARNED -> LEARNING -> LEARNED -> REVIEW_QUEUE -> MASTERED`.
- Multi-book planning now uses two scheduler-side stores: `unlearned_store` for ordered chapter progression and `learned_store` for review-driven items.
- Learning tasks now follow strict `book -> chapter -> knowledge_point` order; the scheduler no longer skips ahead to later chapters for new learning.
- Review generation now uses deterministic forgetting-curve anchors (`day 1`, `3`, `7`, `14`, `30`) and mixes review with learning on the same day.
- Historical learned items can enter `REVIEW_QUEUE` based on due/overdue review state instead of score-only random placement.
- `generate_interleaved_plan()` still keeps the existing architecture, but now respects at least the requested horizon so planned review anchors are not truncated away.
- Local verification passed: `py -3.13 -m pytest backend/tests/test_spaced_repetition_integration.py backend/tests/test_plan_service_scheduler_routing.py backend/tests/test_planning_layer.py`

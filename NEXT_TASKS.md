# 后续任务

> 最后更新：2026-06-18

---

## 当前状态

项目已完成，目前没有必须继续开发的阻塞任务。
当前文档用途调整为：
1. 记录后续维护事项
2. 记录潜在优化项
3. 作为新一轮迭代的入口清单

---

## 已完成

- [x] 用户注册 / 登录 / JWT 鉴权
- [x] 所有核心 API 接入 `user_id` 隔离
- [x] 书库、我的学习、书籍详情主流程打通
- [x] 学习计划基础功能完成
- [x] 后台书籍 / 章节 / 知识点管理完成
- [x] 通知设置完成
- [x] 页面样式与滚动布局问题修复
- [x] 后端工程化分层重构完成
- [x] 统一日志系统完成
- [x] GitHub 仓库建立并纳入版本管理
- [x] Railway 公网部署完成
- [x] Railway 公网空数据库自动恢复两本预设书
- [x] 本地 AI 自动分析架构完成
- [x] 移除用户侧 DeepSeek API Key 配置
- [x] 后台自动分析与 fallback 规则分析接入完成
- [x] 项目状态 Markdown 文件纳入 Git 跟踪
- [x] 书籍详情页“全部知识点”按真实知识点数量显示
- [x] 公网两本预设书知识点数据恢复完整
- [x] 多书交叉学习调度已接入计划生成主流程
- [x] 单书/多书分流已固定：单书旧 `generate_plan()`，多书新 scheduler pipeline
- [x] 新增最小回归测试，锁定分流逻辑
- [x] 本地 markdown 状态文件已同步更新
- [x] 多书 scheduler 已升级为 capacity-aware scheduling（按分钟容量约束，而非按任务数限制）
- [x] review protection layer 已接入容量分配层
- [x] StudyPlan 新增 `effective_days`，修复 `total_days` 与实际生成计划不一致的问题
- [x] 本地 Python 3.13 / pytest 已修复并验证可用

---

## 优先待办

- [ ] 给公网 `/api/admin/*` 后台管理接口补登录鉴权和权限保护
- [ ] 补充 README，统一说明本地运行、部署方式、AI 架构和维护流程
- [ ] 统一清理前端历史编码问题，确保所有文档与页面均为 UTF-8

---

## 可选优化

- [ ] 增加完整的在线 DOCX 上传接口，并复用现有本地分析链路
- [ ] 为 `analysis_result` 增加更细的前端展示模块，如摘要、标签、难度卡片
- [ ] 为 AI 自动分析链路补充更完整的接口测试和回归测试
- [ ] 在线上环境接入可控的本地模型服务方案，而不只依赖 fallback
- [ ] 如需长期稳定持久化，给 Railway 配置持久卷或迁移到独立数据库
- [ ] 视需要把 scheduler 的 session 长度、review delay 上限等参数抽为配置项

---

## 维护提醒

1. 后续如继续开发，请优先更新本文件和 `CURRENT_STATE.md`
2. 需要上线时，推荐流程为：修改 -> 测试 -> `git commit` -> `git push origin main`
3. Railway 如保持连接 GitHub 仓库，将随 `main` 自动部署
4. 不再新增任何依赖用户输入外部 API Key 的功能设计
5. 如果 Railway 使用临时文件系统，重启后仍可能丢失本地 SQLite 数据，但预设书库会自动补回
6. 当前公网最需要优先处理的是后台未鉴权风险，而不是功能缺失

## 2026-06-18 更新
- [x] 学习计划主流程分流修正：单书旧逻辑，多书新调度。
- [x] 已补最小回归测试，覆盖单书/多书路由。

## 2026-06-18 更新
- [x] 多书学习+复习一体化调度已接入并上线。
- [x] 单书/多书主流程分流已锁定。

## 2026-06-18 更新
- [x] 多书调度已升级为 capacity-aware + review-protected scheduler，并已补 session-based splitting 回归测试。
- [x] 计划接口已新增 `effective_days`，保留 `total_days` 为用户请求语义。
- [x] 已使用 `py -3.13 -m pytest` 验证调度相关 11 条测试通过。

## 2026-06-18 Update (UTF-8 Append)
- [x] Added planning layer before scheduler to estimate total workload and auto-derive plan duration from `daily_minutes`.
- [x] Switched plan generation semantics from user-selected days to system-derived `recommended_days` / `final_days`.
- [x] Preserved interleaved scheduler, spaced repetition, review protection, and capacity-aware day allocation.
- [ ] Consider exposing `recommended_days` and `explanation` directly in `PlanResponse` for frontend display.

## 2026-06-19 Update (UTF-8 Append)
- [x] Added a learning state machine layer without changing the public API or scheduler entrypoints.
- [x] Split scheduler task preparation into ordered `unlearned_store` and review-oriented `learned_store`.
- [x] Enforced strict chapter-order learning progression for new learning tasks.
- [x] Switched review generation to deterministic forgetting-curve anchors (`1/3/7/14/30` days) with same-day learning/review mixing preserved.
- [x] Added regression tests covering state-machine stores, chapter-order progression, deterministic review anchors, and mixed daily plans.
- [ ] Expose learning-state or review-anchor metadata to the frontend only if a later UI iteration needs it; keep the current API unchanged for now.

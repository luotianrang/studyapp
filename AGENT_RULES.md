# Agent 开发规范

> 本文档包含开发和会话交接规范。每个新会话应阅读一次。
> 日常开发只需 CURRENT_STATE.md + NEXT_TASKS.md。

---

## 会话交接规范

### 新对话开始时
1. 阅读 CURRENT_STATE.md 和 NEXT_TASKS.md（必读）
2. 如需历史上下文或报错参考，按需阅读 PROJECT_RECORD.md 对应章节
3. 向用户确认已理解项目状态

### 完成功能后
1. 更新 CURRENT_STATE.md（产品形态、文件结构、数据库模型等）
2. 更新 NEXT_TASKS.md（移除已完成项，添加新发现的待办）
3. 在 PROJECT_RECORD.md 追加版本历史

### 遇到报错后
1. 在 PROJECT_RECORD.md「报错与修复」部分记录
2. 格式：报错编号、现象、原因、修复方案（具体到文件和行号）
3. 如修复涉及重要注意事项，同步到 AGENT_RULES.md「重要注意事项」

### 必须记录的修改
- 数据库模型变更（models.py）→ 记录 migration 方案
- 前端路由/页面变更 → 更新 CURRENT_STATE.md 文件结构
- API 接口变更 → 更新 CURRENT_STATE.md 关键 API 端点
- start.bat 修改 → 验证无 BOM 且行尾为 CRLF
- 删除或新增文件 → 更新 CURRENT_STATE.md 文件结构
- 重大文件结构变更 → 在 PROJECT_RECORD.md「文件结构变更记录」追加说明

---

## 常用操作

### 启动服务器
```
双击 start.bat
或：python -m uvicorn backend.main:app --host 0.0.0.0 --port 8899
```

### 重置数据库
```
del data\studyapp.db
然后重启服务器即可自动重建
```

### 验证服务
```
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8899/api/health').read().decode())"
```

---

## 重要注意事项

1. start.bat 必须是纯 ASCII + CRLF。修改后验证：首字节非 EF BB BF，每行结尾 0D 0A
2. api.js 所有方法必须在 `const api = {}` 内部，URL 用模板字符串（反引号）
3. Python 文件使用普通双引号 `"` 而非 `\"` 转义写法
4. 数据库 model 变更后需手动删除 `data/studyapp.db` 让服务器重建
5. BookResponse schema 没有 `file_type` 和 `file_size` 字段
6. 侧边栏 `data-route` 属性值和 `router.js` 注册的路由名必须一致
7. 预设书查询：`GET /api/books/preset`；我的学习查询：`GET /api/books/my-learning`
8. 知识点接口：`GET /api/analysis/knowledge-points/{chapter_id}`
9. 当前无多用户，user_id 固定为 1
10. apply_patch 的 Add File 模式会在行首添加一个空格，需要额外注意

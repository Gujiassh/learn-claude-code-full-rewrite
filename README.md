# learn-claude-code-full-rewrite

面向 `learn-claude-code` 的全量重写工程（分阶段推进）。

本仓库目标：
- 以独立代码库完成 0->1 到生产级机制的全量重写
- 每个阶段有可运行代码、可验证测试、可追溯阶段记录
- 阶段文档长期保存，避免“只写代码不留档”

## 当前状态

- 阶段：`阶段-01 基础内核`
- 已完成：
  - `AgentLoop` 核心循环
  - `ToolRegistry` 工具注册与调用
  - `PhaseLog` 阶段记录写入
  - 基础单测

## 项目结构

- `src/full_rewrite/runtime.py`：阶段-01 运行时内核
- `src/full_rewrite/phase_log.py`：阶段记录写入能力
- `tests/`：回归测试
- `docs/重写总计划.md`：全量重写阶段图
- `docs/阶段记录/`：阶段执行记录

## 本地运行

```bash
cd learn-claude-code-full-rewrite
python3 -m pip install -e .[dev]
python3 -m pytest -q
```

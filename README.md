# learn-claude-code-full-rewrite

面向 `learn-claude-code` 的全量重写工程（分阶段推进）。

本仓库目标：
- 以独立代码库完成 0->1 到生产级机制的全量重写
- 每个阶段有可运行代码、可验证测试、可追溯阶段记录
- 阶段文档长期保存，避免“只写代码不留档”

## 当前状态

- 阶段：`阶段-08 生产化收口（已完成）`
- 已完成：
  - `AgentLoop` 核心循环
  - `ToolRegistry` 工具注册与调用
  - `PhaseLog` 阶段记录写入
  - `TaskBoard` 任务系统（依赖、领取、完成、持久化）
  - `BackgroundJobRunner` 后台任务执行与状态追踪
  - `TeamCoordinator` + `TeamMailbox` 多代理消息协同
  - `ContextGovernor` 上下文压缩与恢复
  - `SecurityPolicy` + `AuditTrail` 安全闸门与审计
  - `ObservabilityHub` 可观测性统计与报告
  - `RewriteAPI` + `rewrite-agent`/`rewrite-api` 入口
  - 全量测试与烟雾脚本

## 项目结构

- `src/full_rewrite/runtime.py`：阶段-01 运行时内核
- `src/full_rewrite/phase_log.py`：阶段记录写入能力
- `src/full_rewrite/task_board.py`：阶段-02 任务系统
- `src/full_rewrite/background_jobs.py`：阶段-03 背景执行
- `src/full_rewrite/team_coordination.py`：阶段-04 多代理协同
- `src/full_rewrite/context_governance.py`：阶段-05 上下文治理
- `src/full_rewrite/security_policy.py`：阶段-06 安全与权限
- `src/full_rewrite/observability.py`：阶段-07 可观测性
- `src/full_rewrite/cli.py` + `src/full_rewrite/api.py`：阶段-08 生产化收口
- `tests/`：回归测试
- `docs/重写总计划.md`：全量重写阶段图
- `docs/阶段记录/`：阶段执行记录

## 本地运行

```bash
cd learn-claude-code-full-rewrite
python3 -m pip install -e .[dev]
python3 -m pytest -q
```

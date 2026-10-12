# tests/
> L2 | 父级: ../CLAUDE.md
成员清单
predicate_probe.m: predicate_probe 的隔离回归检查。
test_analytics.py: test_analytics 的隔离回归检查。
test_apps.py: test_apps 的隔离回归检查。
test_benchmark.py: test_benchmark 的隔离回归检查。
test_client.py: HTTP 重连与显示选择；覆盖最后一项、显式刷新、非法列表及操作不重放。
test_controller.py: test_controller 的隔离回归检查。
test_fallback.py: test_fallback 的隔离回归检查。
test_latency.py: test_latency 的隔离回归检查。
test_local_wda_patch.py: 真实临时 Git 仓库验证补丁准入、保留未知修改及构建过期判定。
test_packaging.py: test_packaging 的隔离回归检查。
test_preview_recovery.py: test_preview_recovery 的隔离回归检查。
test_protocol.py: test_protocol 的隔离回归检查。
test_readiness_cli.py: test_readiness_cli 的隔离回归检查。
test_recovery.py: test_recovery 的隔离回归检查。
test_registration.py: test_registration 的隔离回归检查。
test_screen.py: test_screen 的隔离回归检查。
test_screen_protocol.py: test_screen_protocol 的隔离回归检查。
test_setup.py: 生命周期回归；进程与源码指纹使用替身，不触碰真实设备。
test_state_directory.py: test_state_directory 的隔离回归检查。
test_tool_loading.py: MCP 公共命名与技能引用校验；内部 WDA 工程说明不冒充工具名。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

test_display.py: 显示增删与会话切换、无动作/无截图约束、认证暂停竞态及跨进程操作锁回归。

test_observation_budget.py: 上游 0.3.10 控件观察预算回归。

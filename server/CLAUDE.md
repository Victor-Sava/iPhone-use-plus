# server/
> L2 | 父级: ../CLAUDE.md

analytics.py: analytics 的服务实现。
iphone_use.py: MCP 与 Runtime 调度；锁屏/镜像空树作为观测状态，保留真实认证错误及预览暂停。
wda_apps.py: wda_apps 的服务实现。
wda_client.py: WDA 会话与通信；初始化/READY 选择显示列表最后一项，不重复手机动作。
wda_controller.py: wda_controller 的服务实现。
wda_image.py: wda_image 的服务实现。
wda_screen.py: wda_screen 的服务实现。
wda_setup.py: wda_setup 的服务实现。
wda_text.py: wda_text 的服务实现。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

wda_setup.py 校验 WDA 上游提交及 tooling/wda-mirroring.patch 完整差异，并把实际补丁摘要写入构建记录；补丁改变后旧构建失效。

wda_display.py: WDA 服务内的有界轮询；复用当前会话、竞争同一操作锁，按显示列表最后一项更新设置，只恢复匹配的 device_locked 暂停；认证暂停不探测设备。

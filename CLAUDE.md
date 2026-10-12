# iPhone Use - 通过 USB/Wi-Fi 连接真实 iPhone 的 Codex 本地插件

Python 3.9+ 标准库 MCP + Node.js USB 通信 + WebDriverAgent 16.14.0 + Xcode + TypeScript 屏幕组件

<directory>
server/ - MCP 工具、手机操作与 WDA 生命周期；经本机回环地址访问 USB 转发。
scripts/ - 官方安装、打包、检查和工具备用入口；安装使用 install.sh。
skills/ - iphone-use-setup 负责初始化，iphone-use 负责就绪后的手机任务。
tooling/ - USB 转发与屏幕流依赖，使用固定的依赖锁文件。
ui/ - 手机屏幕组件源码与构建配置。
assets/ - 安装时直接使用的屏幕资源和项目图像。
tests/ - 上游工程检查；不能替代真机 READY 验收。
dist/ - 安装脚本生成的暂存插件，非源码维护入口。
docs/ - 本机安装记录与后续操作指引，见 docs/CLAUDE.md。
</directory>

<config>
.codex-plugin/plugin.json - Codex 插件清单，当前安装版本 0.3.10。
.agents/plugins/marketplace.json - 本地插件市场入口。
.mcp.json / mcp.json - 上游提供的同名 iphone_use MCP 服务声明。
docs/local-setup.md - 本机安装与真机验收证据、运行路径、续期方式和手机设置记录。
</config>

运行状态、设备标识与签名配置保存在 ~/.local/share/iphone-use，不能写入源码仓库。
Codex 实际使用 ~/.codex/plugins/cache/iphone-use-local/iphone-use/0.3.8 中的安装副本。
进入手机任务前必须在当前会话取得 pua_ready 的 ready=true；安装成功或端口开放不足以证明可用。
法则: 极简·稳定·导航·版本精确

手机操作工具优先级见 skills/iphone-use/SKILL.md：所有操作均优先 PUA；个别操作无法完成且苹果镜像已连接时，仅用 Computer Use 补做该步和必要验收，下一步回到 PUA 优先；切换前核对结果以免重复提交。

无线传输：tooling/device-connection.mjs 统一控制与视频通道；运行目录 wireless.json 保存选定设备的 udid/host，移除文件回到 USB。地址变化需更新；不改变构建签名配置。

本地 WDA 改造：tooling/wda-mirroring.patch 保存镜像坐标路由与显式应用上下文改造；server/wda_setup.py 精确校验补丁并按摘要使旧构建失效。

显示自动跟随：WDA 启动工作中的 DisplayMonitor 每两秒检查显示拓扑，更新截图/输入目标并恢复对应锁屏暂停；不依赖模型再次调用 READY，不执行手机动作。

README.plus.md - 可随仓库发布的增强说明、补丁安装、无线配置与验收边界；docs/ 内本机记录继续仅保留本地。

.gitattributes - 补丁文件保留 unified diff 的上下文空格，避免 Git 把补丁格式误报为源码尾随空白。

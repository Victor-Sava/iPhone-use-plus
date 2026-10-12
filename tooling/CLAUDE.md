# tooling/
> L2 | 父级: ../CLAUDE.md
forward.mjs: 回环控制端口代理，通过共享传输连接设备。
screen-stream.mjs: MJPEG 视频流子进程，向 ScreenHub 输出 JPEG。
device-connection.mjs: USB/Wi-Fi socket 选择；运行目录 wireless.json 绑定 UDID 和私网 IPv4，缺失时使用 USB，配置错误不静默连接其他设备。
package.json: Node 运行依赖与版本要求。
package-lock.json: 固定 USB 库依赖版本。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

wda-mirroring.patch: 固定 WDA 提交上的显示路由补丁；setup 只允许完全一致的已跟踪变更，构建记录补丁摘要。

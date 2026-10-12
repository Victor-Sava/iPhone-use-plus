# iPhone Use Plus

基于 [zhongerxin/iPhone-use](https://github.com/zhongerxin/iPhone-use) 0.3.10 的本地增强版本，保留上游许可证与原有安装入口。

## 增强内容

- 移除 Runtime 的锁屏/镜像空树前置拒绝；真实认证错误仍暂停预览并交由用户处理。
- 会话初始化和 READY 按 WDA 显示列表最后一项选择截图与视频来源，不固定显示编号。
- WDA 补丁让镜像输入与截图使用同一显示；元素点击使用控件树同源的 wdFrame。
- 镜像前台应用复用当前上下文，避免重复 activate 打断镜像。
- 控制代理和 MJPEG 预览支持 USB/Wi-Fi。
- 服务内 DisplayMonitor 每两秒跟随显示变化，仅恢复对应的锁屏暂停；认证暂停不自动解除，不重放手机操作。

## 安装增强后的手机端

按主 README 安装插件并完成设备、签名及 WDA 源码配置。固定 WDA 版本为 16.14.0，提交为 `d17782422d55ff1e5e0ceb74eb1fd509cc0c35b6`。

在构建前，对配置中的 WDA 源码目录应用本仓库 `tooling/wda-mirroring.patch`：

```sh
# 将下列路径替换为自己的插件仓库与配置中的 source_dir。
git -C /path/to/WebDriverAgent apply --check /path/to/iPhone-use-plus/tooling/wda-mirroring.patch
git -C /path/to/WebDriverAgent apply /path/to/iPhone-use-plus/tooling/wda-mirroring.patch
```

已应用时不要重复应用，也不要覆盖其他源码修改。之后沿用 setup 的 build → start → READY。构建器校验上游提交和完整补丁差异，补丁变化后必须重新构建。fetch 保留用户改动，不会自动覆盖已打补丁的目录。

源码、安装包都携带补丁；仅重装 Mac 插件不会自动替换手机上已经安装的 WDA。

## Wi-Fi 配置

在私有运行目录（默认 `~/.local/share/iphone-use`）创建 `wireless.json`，填写当前已配对设备的 UDID 与同一局域网中的 IPv4 地址：

```json
{"udid":"YOUR_DEVICE_UDID","host":"192.168.1.100"}
```

文件权限设为 `600`。控制与视频通道共用该配置；移除文件后使用 USB。设备标识必须匹配当前配置，地址变化需要更新配置。首次安装、配对、信任及签名仍按 Xcode 流程完成。

## 验证范围与限制

真机已验证锁屏且镜像连接时的截图、坐标/控件点击、滑动、中文输入和 Home，以及拔线后的 Wi-Fi 控制。镜像关闭后可唤起应用操作，但实测会唤亮实体屏。关闭镜像且保持实体屏完全不发光尚未实现。

镜像重连已验证自动切换显示与恢复锁屏预览，无需再次调用 READY；认证暂停由原有人工接管流程处理。新应用的系统 activate 仍可能打断镜像，优先通过桌面或搜索图标进入应用。

目前仍是单设备配置，多手机对话切换尚未实现。手机重启后的无线冷启动不属于上述拔线验证范围。WDA 的 locked 标记不等同于实体屏是否发光。

## 本地检查

```sh
python3 -m unittest discover -s tests
python3 scripts/package.py --validate-only
cd ui
npm ci
npm test
npm run build
```

运行目录、设备标识、签名配置、证书和日志不进入源码仓库。

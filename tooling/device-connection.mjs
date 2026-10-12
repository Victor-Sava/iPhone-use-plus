/**
 * [INPUT]: 依赖运行目录 wireless.json、node:net 与 appium-ios-device。
 * [OUTPUT]: connectDevicePort 为控制与视频流建立同一设备的 USB 或 Wi-Fi socket。
 * [POS]: tooling 的共享传输入口；无线配置绑定 UDID，未配置时保留 USB。
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
import net from 'node:net';
import {readFile} from 'node:fs/promises';

export function validateWireless(config, udid) {
  if (config.udid !== udid) throw new Error('Wireless target does not match the selected device.');
  const host = config.host;
  if (net.isIP(host ?? '') !== 4) throw new Error('Wireless host must be a private IPv4 address.');
  const [a, b] = host.split('.').map(Number);
  if (!(a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168))) {
    throw new Error('Wireless host must be a private IPv4 address.');
  }
  return host;
}

export async function connectDevicePort(udid, port) {
  let config;
  try {
    config = JSON.parse(await readFile(new URL('../../wireless.json', import.meta.url), 'utf8'));
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    const {default: iosDevice} = await import('appium-ios-device');
    return iosDevice.utilities.connectPort(udid, port);
  }
  const host = validateWireless(config, udid);
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({host, port});
    const timer = setTimeout(() => socket.destroy(new Error('Wireless connection timed out.')), 5000);
    socket.once('error', error => { clearTimeout(timer); reject(error); });
    socket.once('connect', () => { clearTimeout(timer); resolve(socket); });
  });
}

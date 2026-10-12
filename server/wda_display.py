"""[INPUT]: WDA 状态/显示/设置接口、operation.lock 与 ScreenHub 暂停事务。
[OUTPUT]: DisplayMonitor，周期跟随列表最后一个显示并条件恢复锁屏预览。
[POS]: server 服务生命周期的后台观察器；复用现有会话，不创建会话或执行手机动作。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from __future__ import annotations

import fcntl
import os
from pathlib import Path
import re
import time

from wda_client import WDAClient, WDAError
from wda_screen import ScreenHub

DISPLAY_POLL_SECONDS = 2
DISPLAY_PROBE_SECONDS = 1.5


class DisplayMonitor:
    def __init__(self, state_dir, base_url):
        self.state_dir = Path(state_dir)
        self.client = WDAClient(base_url, timeout=DISPLAY_PROBE_SECONDS)
        # 此实例只操作共享暂停状态，不启动或捕获屏幕流。
        self.screen = ScreenHub(state_dir)
        self.next_probe = 0
        self.last_result = None

    def close(self):
        self.client.close()
        self.screen.close()

    def _authentication_paused(self):
        state = self.screen.pause_status()
        return state['paused'] and state['pause_reason'] != 'device_locked'

    def _request(self, method, path, deadline, payload=None):
        # pause 不拿操作锁，因此每次请求前再检查；已在途的只读请求可能先完成。
        if self._authentication_paused():
            raise WDAError('preview_paused', 'Authentication preview pause is active.')
        return self.client.request(method, path, payload, timeout=self.client.remaining(deadline))

    def _probe(self):
        if self._authentication_paused():
            return {'state': 'authentication_paused'}
        pause_id = self.screen.locked_pause_id()
        deadline = time.monotonic() + DISPLAY_PROBE_SECONDS
        status = self._request('GET', '/status', deadline)
        sid = status.get('sessionId')
        if ((status.get('value') or {}).get('ready') is not True
                or not isinstance(sid, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,128}', sid)):
            return {'state': 'waiting_for_session'}
        screens = self._request('GET', '/wda/screens', deadline).get('value')
        if not isinstance(screens, list) or not screens:
            return {'state': 'waiting_for_display'}
        selected = screens[-1]
        if not isinstance(selected, dict) or type(selected.get('displayId')) is not int:
            raise WDAError('invalid_response', 'Last WDA display has no integer displayId.')
        display_id = selected['displayId']
        endpoint = '/session/' + sid + '/appium/settings'
        settings = self._request('GET', endpoint, deadline).get('value')
        if not isinstance(settings, dict):
            raise WDAError('invalid_response', 'Missing WDA session settings.')
        if settings.get('currentDisplayId') != display_id:
            self._request('POST', endpoint, deadline, {'settings': {'currentDisplayId': display_id}})
        resumed = False
        if pause_id:
            # 虚拟显示可用时不依赖可能滞后的锁屏通知。主显示须另有解锁证明。
            usable = selected.get('isMain') is False
            if not usable:
                usable = self._request('GET', '/wda/locked', deadline).get('value') is False
            if usable:
                resumed = self.screen.resume_after_unlock(pause_id)
        return {'state': 'following', 'session_id': sid, 'display_id': display_id,
                'preview_resumed': resumed}

    def tick(self):
        """非阻塞竞争操作锁；忙时让出，本轮网络有总时限。只返回状态变化。"""
        now = time.monotonic()
        if now < self.next_probe:
            return None
        self.next_probe = now + DISPLAY_POLL_SECONDS
        descriptor = None
        try:
            descriptor = os.open(self.state_dir / 'operation.lock', os.O_CREAT | os.O_RDWR, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return None
            result = self._probe()
        except WDAError as error:
            result = {'state': 'authentication_paused' if error.code == 'preview_paused' else 'unavailable',
                      'reason': error.code}
        except (OSError, ValueError, TypeError) as error:
            result = {'state': 'unavailable', 'reason': type(error).__name__}
        finally:
            if descriptor is not None:
                os.close(descriptor)
        if result == self.last_result:
            return None
        self.last_result = result
        return result

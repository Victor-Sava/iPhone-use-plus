"""[INPUT]: DisplayMonitor、真实暂停文件与模拟 WDA 服务。
[OUTPUT]: 显示重连、会话变更、操作互斥及认证竞态回归。
[POS]: tests 后台显示跟随测试，不启动真实设备或捕获屏幕。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import fcntl
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from wda_display import DisplayMonitor
from wda_client import WDAError


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.monitor = DisplayMonitor(self.temp.name, 'http://127.0.0.1:18100')
        self.addCleanup(self.monitor.close)
        self.calls = []
        self.sid = 'test-session'
        self.screens = [{'displayId': 1, 'isMain': True}, {'displayId': 7, 'isMain': False}]
        self.settings = {'currentDisplayId': 1, 'waitForIdleTimeout': 0}
        self.locked = True
        mock = patch.object(self.monitor.client, 'request', side_effect=self.request)
        mock.start()
        self.addCleanup(mock.stop)

    def request(self, method, path, payload=None, timeout=None):
        self.calls.append((method, path, payload))
        self.assertGreater(timeout, 0)
        self.assertLessEqual(timeout, 1.5)
        if path == '/status':
            return {'sessionId': self.sid, 'value': {'ready': True}}
        if path == '/wda/screens':
            return {'value': self.screens}
        if path == '/wda/locked':
            return {'value': self.locked}
        self.assertEqual(path, '/session/' + self.sid + '/appium/settings')
        if method == 'POST':
            self.assertEqual(set(payload['settings']), {'currentDisplayId'})
            self.settings.update(payload['settings'])
        return {'value': dict(self.settings)}

    def tick(self):
        self.monitor.next_probe = 0
        return self.monitor.tick()

    def writes(self):
        return [call for call in self.calls if call[0] == 'POST']

    def test_connect_disconnect_reconnect_follows_last_not_max(self):
        self.screens = [{'displayId': 99, 'isMain': True}, {'displayId': 3, 'isMain': False}]
        self.assertEqual(self.tick()['display_id'], 3)
        self.screens = [{'displayId': 99, 'isMain': True}]
        self.assertEqual(self.tick()['display_id'], 99)
        self.screens.append({'displayId': 8, 'isMain': False})
        self.assertEqual(self.tick()['display_id'], 8)
        self.assertEqual(len(self.writes()), 3)
        self.assertEqual(self.settings['waitForIdleTimeout'], 0)

    def test_same_display_does_not_rewrite_settings_or_capture(self):
        self.tick()
        self.assertIsNone(self.tick())
        self.assertEqual(len(self.writes()), 1)
        self.assertFalse(any('source' in p or 'screenshot' in p for _, p, _ in self.calls))

    def test_new_session_is_followed_without_creating_session(self):
        self.tick()
        self.sid = 'replacement-session'
        self.settings['currentDisplayId'] = None
        self.assertEqual(self.tick()['session_id'], self.sid)
        self.assertEqual(self.writes()[-1][1], '/session/replacement-session/appium/settings')

    def test_no_session_is_not_created(self):
        self.sid = None
        self.assertEqual(self.tick()['state'], 'waiting_for_session')
        self.assertEqual(len(self.calls), 1)

    def test_mirror_reconnect_resumes_only_matching_lock_pause(self):
        self.monitor.screen.set_paused(True, reason='device_locked')
        self.assertTrue(self.tick()['preview_resumed'])
        self.assertFalse(self.monitor.screen.paused())
        self.assertFalse(any(p == '/wda/locked' for _, p, _ in self.calls))

    def test_main_display_does_not_resume_while_locked(self):
        self.screens = self.screens[:1]
        self.monitor.screen.set_paused(True, reason='device_locked')
        self.assertFalse(self.tick()['preview_resumed'])
        self.assertTrue(self.monitor.screen.paused())
        self.locked = False
        self.assertTrue(self.tick()['preview_resumed'])

    def test_authentication_or_legacy_pause_does_not_probe(self):
        self.monitor.screen.set_paused(True)
        self.assertEqual(self.tick()['state'], 'authentication_paused')
        self.assertEqual(self.calls, [])
        (Path(self.temp.name) / 'screen-state.json').write_text('{"paused":true}')
        self.tick()
        self.assertEqual(self.calls, [])
        self.assertTrue(self.monitor.screen.paused())

    def test_authentication_started_during_probe_is_preserved(self):
        self.monitor.screen.set_paused(True, reason='device_locked')
        original = self.request
        def racing(method, path, payload=None, timeout=None):
            result = original(method, path, payload, timeout)
            if method == 'POST':
                self.monitor.screen.set_paused(True)
            return result
        with patch.object(self.monitor.client, 'request', side_effect=racing):
            self.assertFalse(self.tick()['preview_resumed'])
        self.assertEqual(self.monitor.screen.pause_status()['pause_reason'], 'authentication')

    def test_new_lock_pause_during_probe_is_not_cleared(self):
        self.monitor.screen.set_paused(True, reason='device_locked')
        original = self.request
        def racing(method, path, payload=None, timeout=None):
            result = original(method, path, payload, timeout)
            if method == 'POST':
                self.monitor.screen.set_paused(True, reason='device_locked')
            return result
        with patch.object(self.monitor.client, 'request', side_effect=racing):
            self.assertFalse(self.tick()['preview_resumed'])
        self.assertTrue(self.monitor.screen.paused())

    def test_busy_phone_operation_is_never_interrupted(self):
        with (Path(self.temp.name) / 'operation.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.assertIsNone(self.tick())
        self.assertEqual(self.calls, [])
        self.assertEqual(self.tick()['display_id'], 7)

    def test_empty_invalid_and_unreachable_retry_later(self):
        self.screens = []
        self.assertEqual(self.tick()['state'], 'waiting_for_display')
        self.screens = [{'displayId': True}]
        self.assertEqual(self.tick()['reason'], 'invalid_response')
        with patch.object(self.monitor.client, 'request', side_effect=WDAError('pua_unreachable', 'offline')):
            self.assertEqual(self.tick()['reason'], 'pua_unreachable')
        self.screens = [{'displayId': 5, 'isMain': False}]
        self.assertEqual(self.tick()['display_id'], 5)

    def test_poll_interval_is_bounded(self):
        self.tick()
        count = len(self.calls)
        self.assertIsNone(self.monitor.tick())
        self.assertEqual(len(self.calls), count)


if __name__ == '__main__':
    unittest.main()

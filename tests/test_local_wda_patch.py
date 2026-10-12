"""[INPUT]: SetupManager 与临时 Git 仓库。
[OUTPUT]: 固定源码补丁准入及过期构建拒绝的真实文件测试。
[POS]: tests 本地 WDA 构建契约，补充生命周期中的进程替身测试。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import wda_setup


class LocalPatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'wda'
        self.source.mkdir()
        (self.source / 'WebDriverAgent.xcodeproj').mkdir()
        (self.source / 'WebDriverAgent.xcodeproj/project.pbxproj').write_text('fixture\n')
        self.file = self.source / 'gesture.m'
        self.file.write_text('original\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
        pin = patch.object(wda_setup, 'WDA_COMMIT', self.git('rev-parse', 'HEAD').strip())
        pin.start()
        self.addCleanup(pin.stop)
        plugin = patch.object(wda_setup, 'PLUGIN_ROOT', self.root / 'plugin')
        plugin.start()
        self.addCleanup(plugin.stop)
        (self.root / 'plugin/tooling').mkdir(parents=True)
        self.file.write_text('selected display\n')
        self.patch_file = self.root / 'plugin/tooling/wda-mirroring.patch'
        self.patch_file.write_text(self.git('diff', 'HEAD', '--binary'))
        self.config = {'source_dir': str(self.source)}
        self.manager = wda_setup.SetupManager(self.root / 'state')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.source, text=True, stderr=subprocess.PIPE)

    def test_exact_patch_and_staged_patch_are_accepted(self):
        self.assertEqual(self.manager._source(self.config), self.source)
        self.git('add', 'gesture.m')
        self.assertEqual(self.manager._source(self.config), self.source)

    def test_extra_change_is_rejected_and_preserved(self):
        self.file.write_text('unexpected extra change\n')
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            self.manager._source(self.config)
        self.assertEqual(self.file.read_text(), 'unexpected extra change\n')

    def test_missing_patch_rejects_modified_source(self):
        self.patch_file.unlink()
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            self.manager._source(self.config)

    def test_patch_change_invalidates_existing_build(self):
        marker = {'config_fingerprint': wda_setup._fingerprint(self.config),
                  'commit': wda_setup.WDA_COMMIT,
                  'source_patch_hash': self.manager._source_patch_hash(self.config)}
        wda_setup._write_json(self.manager.state_dir / 'build.json', marker)
        self.manager._require_build(self.config)
        self.file.write_text('next selected display implementation\n')
        self.patch_file.write_text(self.git('diff', 'HEAD', '--binary'))
        self.manager._source(self.config)
        with self.assertRaisesRegex(ValueError, 'build successfully'):
            self.manager._require_build(self.config)

    def test_clean_upstream_retains_legacy_marker_compatibility(self):
        self.file.write_text('original\n')
        self.manager._source(self.config)
        self.assertIsNone(self.manager._source_patch_hash(self.config))
        wda_setup._write_json(self.manager.state_dir / 'build.json', {
            'config_fingerprint': wda_setup._fingerprint(self.config), 'commit': wda_setup.WDA_COMMIT})
        self.manager._require_build(self.config)


if __name__ == '__main__':
    unittest.main()

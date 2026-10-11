import os
import pathlib
import pty
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'backup'


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.opt = self.root / 'opt'
        (self.opt / 'etc/nfqws2').mkdir(parents=True)
        (self.opt / 'etc/nfqws2/config').write_text('application config')
        self.mount = self.root / 'mnt/Kingston16G'
        self.mount.mkdir(parents=True)
        self.dest = self.mount / 'backup'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.command('logger', 'exit 0')
        self.command('readlink', 'printf "%s\\n" "$2"')
        self.command('opkg', 'echo "arch aarch64-test 100"')
        self.command('ndmc', '''case "$2" in
        'show running-config') echo 'router config';;
        *) dst=${2##* }; dst=${dst#Kingston16G:}; printf firmware > "''' + str(self.mount) + '''/$dst";;
        esac''')
        self.mounts = self.root / 'mounts'
        self.mounts.write_text(f'/dev/test {self.mount} exfat rw 0 0\n')
        text = SCRIPT.read_text().replace('/tmp/mnt', str(self.root / 'mnt'))
        text = text.replace('/proc/mounts', str(self.mounts)).replace('/opt', str(self.opt))
        text = text.replace('PATH=' + str(self.opt) + '/bin:' + str(self.opt) + '/sbin:/sbin:/bin:/usr/sbin:/usr/bin',
                            f'PATH={self.bin}:/usr/bin:/bin:/usr/sbin:/sbin')
        text = text.replace('/tmp/entware-backup.lock', str(self.root / 'lock'))
        self.script = self.root / 'script'
        self.script.write_text(text)

    def command(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)

    def run_backup(self):
        return subprocess.run(['/bin/sh', str(self.script)], capture_output=True, text=True)

    def snapshots(self):
        return sorted(p for p in self.dest.glob('20*') if p.is_dir())

    def test_repeat_preserves_two_complete_snapshots(self):
        for _ in range(2):
            result = self.run_backup()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.snapshots()), 2)
        for snapshot in self.snapshots():
            self.assertTrue((snapshot / 'etc/nfqws2/config').is_file())
            self.assertFalse((snapshot / 'etc/nfqws2/nfqws2').exists())
            self.assertTrue(list(snapshot.glob('config-*.gz')))
            self.assertTrue(list(snapshot.glob('firmware-*')))
            archive = next(snapshot.glob('*.tar.gz'))
            self.assertEqual(subprocess.run(['tar', '-tzf', str(archive)], capture_output=True).returncode, 0)

    def test_archive_failure_keeps_existing_snapshot(self):
        self.assertEqual(self.run_backup().returncode, 0)
        before = {str(p): p.read_bytes() for p in self.snapshots()[0].rglob('*') if p.is_file()}
        self.command('tar', 'printf broken > "$2"; exit 2')
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Backup finished', result.stdout)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.snapshots()[0].rglob('*') if p.is_file()})
        self.assertEqual(len(self.snapshots()), 1)
        self.assertFalse(list(self.dest.glob('.incomplete-*')))

    def test_changed_file_warning_keeps_valid_archive(self):
        self.command('tar', 'printf payload | gzip > "$2"; exit 1')

        result = self.run_backup()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.snapshots()), 1)
        archive = next(self.snapshots()[0].glob('*.tar.gz'))
        self.assertEqual(subprocess.run(['gzip', '-t', str(archive)]).returncode, 0)

    def test_architecture_name_with_dot_is_preserved(self):
        self.command('opkg', 'echo "arch aarch64-k3.10 100"')

        result = self.run_backup()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('arch: aarch64-k3.10', result.stdout)
        self.assertTrue(next(self.snapshots()[0].glob('aarch64-k3.10-installer-*.tar.gz')).is_file())

    def test_interactive_archive_uses_pv_when_available(self):
        marker = self.root / 'pv-called'
        self.command('pv', f'printf called > "{marker}"; cat')

        master, slave = pty.openpty()
        try:
            result = subprocess.Popen(
                ['/bin/sh', str(self.script)],
                stdin=subprocess.DEVNULL,
                stdout=slave,
                stderr=slave,
            )
            os.close(slave)
            while True:
                try:
                    if not os.read(master, 4096):
                        break
                except OSError:
                    break
            self.assertEqual(result.wait(), 0)
        finally:
            os.close(master)

        self.assertEqual(marker.read_text(), 'called')

    def test_cleanup_preserves_unrelated_directories(self):
        self.dest.mkdir()
        old = self.dest / '2020-01-01'
        keep = self.dest / '2020-01-01-personal'
        old.mkdir(); keep.mkdir()
        deceptive = self.dest / '2020-01-01-123456-personal-123'
        deceptive.mkdir()
        os.utime(deceptive, (1, 1))
        for p in (old, keep, self.dest):
            os.utime(p, (1, 1))
        result = self.run_backup()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(old.exists())
        self.assertTrue(keep.exists())
        self.assertTrue(deceptive.exists())

    def test_symlink_destination_is_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        self.dest.symlink_to(outside, target_is_directory=True)
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_existing_lock_is_preserved(self):
        lock = self.root / 'lock'
        lock.mkdir()
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(lock.is_dir())
        self.assertFalse(self.dest.exists())

    def test_missing_firmware_aborts_and_releases_lock(self):
        self.command('ndmc', 'case "$2" in "show running-config") echo config;; esac')
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshots(), [])
        self.assertFalse(list(self.dest.glob('.incomplete-*')))
        self.assertFalse((self.root / 'lock').exists())

    def test_firmware_written_before_ndmc_failure_is_removed(self):
        self.command('ndmc', '''case "$2" in
        'show running-config') echo 'router config';;
        *) dst=${2##* }; dst=${dst#Kingston16G:}; printf partial > "''' + str(self.mount) + '''/$dst"; exit 1;;
        esac''')

        result = self.run_backup()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshots(), [])
        self.assertEqual(list(self.dest.glob('.firmware-*')), [])
        self.assertFalse(list(self.dest.glob('.incomplete-*')))

    def test_empty_config_aborts(self):
        self.command('ndmc', 'exit 0')
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshots(), [])

    def test_missing_router_cli_aborts_requested_backup(self):
        (self.bin / 'ndmc').unlink()
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshots(), [])

    def test_unmounted_directory_is_rejected(self):
        self.mounts.write_text('')
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.dest.exists())


if __name__ == '__main__':
    unittest.main()

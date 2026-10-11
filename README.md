# Regular Entware and Keenetic firmware backup


![Bash](https://img.shields.io/badge/Bash-89e051.svg?style=for-the-badge&logo=bash&logoColor=white)
[![Licence](https://img.shields.io/github/license/ykmn/ff-Logger?style=for-the-badge)](./LICENSE)
![Entware](https://img.shields.io/badge/Entware-0097dc.svg?style=for-the-badge&logo=Entware&logoColor=white)


This script allows you to:

* complete daily backup of Entware of your Keenetic router

* Keenetic running configuration and firmware

* backup some apps and services' configurations

Connect a USB Flash drive formatted in exFAT and labeled as "Kingston16G" to an available USB port. Feel free to change the drive volume label and replace `USB_LABEL="Kingston16G"` in the script.

Backups are stored to `/backup` folder on root of USB drive. The script creates it automatically.
Daily backups are stored in `YYYY-MM-DD` subfolders. Repeated runs on the same day use `YYYY-MM-DD-HHMMSS-PID`. Each run is assembled in a temporary directory and published only after all requested backups succeed.

Set 1 or 0 in the Configuration section variables to backup or skip:

* IsNFQWS1=1: backup [nfqws-keenetic](https://github.com/Anonym-tsk/nfqws-keenetic) configuration from /opt/etc/nfqws

* IsNFQWS2=1: backup [nfqws2-keenetic](https://github.com/nfqws/nfqws2-keenetic) configuration from /opt/etc/nfqws2

* IsSKeen=1: backup [SKeen](https://github.com/jinndi/SKeen/) configuration from /opt/etc/skeen

* IsXKeen=1: backup [XKeen](https://github.com/jameszeroX/XKeen) configuration from /opt/etc/xkeen

* IsXKeenUI=1: backup the [XKeen-UI](https://github.com/umarcheh001/Xkeen-UI) folder from /opt/etc/xkeen-ui

* IsMihomo=1: backup [Mihomo](https://github.com/MetaCubeX/mihomo) configuration file /opt/etc/mihomo/config.yaml

* The complete Entware archive is always created as `<architecture>-installer-YYYY-MM-DD.tar.gz`. It excludes `/opt/tmp` and `/opt/var/run`.

* IsConf=1: backup Keenetic running configuration. Saves a compressed copy in every daily backup.

* IsFirm=1: backup Keenetic firmware. Saves a copy in every daily backup.

## Installation

Prerequisites: install `cron` (plus `tar` and `gzip` if unavailable):
```bash
opkg update
opkg install cron tar gzip
/opt/etc/init.d/S10cron status
```

Download the script, set executive permissions:
```bash
wget -O /opt/etc/cron.daily/backup https://github.com/ykmn/Backup-Entware/raw/refs/heads/main/backup
chmod +x /opt/etc/cron.daily/backup
```

Plug in USB drive and check its availability:
```bash
ls -la /tmp/mnt
```
If the USB-drive subfolder is mounted, you are good to go. Notice the volume label and
change `USB_LABEL=` variable accordingly.

Run script manually:
```bash
/opt/etc/cron.daily/backup
```

If scripts finishes without errors, you're good to go. It will be launched daily.

Cleanup uses directory modification time and `find -mtime +DAYS` (whole 24-hour periods), with `DAYS=8` by default. Only directories matching the exact snapshot naming formats are removed; other directories and the backup root are preserved. Unchanged configuration and firmware are included in every run, which increases disk usage. `config-cur` and `firmware-cur` remain available as the latest copies.

The script checks `/proc/mounts` and estimates required space as twice the `/opt` size plus 64 MiB. This is an estimate; write failures still abort the run. `USB_LABEL` supports letters, digits, underscores and hyphens. `BACKUP_DIR` must be a normalized path inside that mount, with no symlink components.

Concurrent runs are blocked by `/tmp/entware-backup.lock`. Normal exits and handled signals release it. After a forced termination, confirm that no backup is running before removing a stale lock with `rmdir /tmp/entware-backup.lock`. A reboot normally clears `/tmp`. Leftover `.incomplete-*` directories after an unhandled termination are not completed backups and are not automatically pruned.

Local regression checks (Python 3; router commands are simulated, filesystem operations and archiving are real):
```bash
sh -n backup
python3 -m unittest discover -s tests -v
```

This script based on [@gvan](https://forum.keenetic.ru/profile/6560-gvan/) script published at [Keenetic Community](https://forum.keenetic.ru/topic/1356-%D0%BF%D0%B5%D1%80%D0%B8%D0%BE%D0%B4%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%BE%D0%B5-%D1%80%D0%B5%D0%B7%D0%B5%D1%80%D0%B2%D0%BD%D0%BE%D0%B5-%D0%BA%D0%BE%D0%BF%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-entware-%D0%BA%D0%BE%D0%BD%D1%84%D0%B8%D0%B3%D0%B0-%D0%B8-%D0%BF%D1%80%D0%BE%D1%88%D0%B8%D0%B2%D0%BA%D0%B8/).

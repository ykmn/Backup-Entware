# Regular Entware and Keenetic firmware backup


![Bash](https://img.shields.io/badge/Bash-89e051.svg?style=for-the-badge&logo=bash&logoColor=white)
[![Licence](https://img.shields.io/github/license/ykmn/ff-Logger?style=for-the-badge)](./LICENSE)
![Entware](https://img.shields.io/badge/Entware-0097dc.svg?style=for-the-badge&logo=Entware&logoColor=white)


This script allows you to:

* complete daily backup of Entware of your Keenetic router

* Keenetic running configuration and firmware

* backup some apps and services' configurations 

Connect a USB Flash drive formatted in exFAT and labeled as "Backups" to an available USB port. Feel free to change the drive volume label and replace `LABEL=Backups` in the script.

Backups are stored to `/backup` folder on root of USB drive. You have to create it first.
Daily backups are stored in `YYYY-MM-DD` subfolders.

Set 1 or 0 in the Configuration section variables to backup or skip:

* isNFQWS1=1: backup [nfqws-keenetic](https://github.com/Anonym-tsk/nfqws-keenetic) configuration from /opt/etc/nfqws

* isNFQWS2=1: backup [nfqws2-keenetic](https://github.com/nfqws/nfqws2-keenetic) configuration from /opt/etc/nfqws2

* isSKeen=1: backup [SKeen](https://github.com/jinndi/SKeen/) configuration from /opt/etc/skeen

* isMihomo=1: backup [Mihomo](https://github.com/MetaCubeX/mihomo) configuration from /opt/etc/mihomo

* IsEnt=1: backup Entware file system to Entware-YYYY-MM-DD.tgz file. You can use it to fully restore your Entware on a new USB Flash drive, just put this file to /install folder.

* IsConf=1: backup Keenetic running configuration. Saves a new copy only if there were changes.

* IsFirm=1: backup Keenetic firmware. Saves a new copy only if firmware was changed.

## Installation

Prerequisites: install `pv` and `cron`:
```bash
opkg update
opkg install pv cron
/opt/etc/init.d/S10cron status
```

Clone this repo:
```bash
cd ~
git clone https://github.com/ykmn/Backup-Entware.git
```

Copy `backup` script to the cron daily folder, set execute permission:
```bash
cp ~/Backup-Entware/backup /opt/etc/cron.daily
chmod +x /opt/etc/cron.daily/backup
```

Plug in USB drive and check its availability:
```bash
ls -la /tmp/mnt
```
If the USB-drive subfolder is mounted, you are good to go. Notice the volume label and
change `LABEL=` variable accordingly.

Run script manually:
```bash
/opt/etc/cron.daily/backup
```

If scripts finishes without errors, you're good to go. It will be launched daily.

Backups will be stored for 8 days (changeable at `DAYS=8`)

This script based on [@gvan](https://forum.keenetic.ru/profile/6560-gvan/) script published at [Keenetic Community](https://forum.keenetic.ru/topic/1356-%D0%BF%D0%B5%D1%80%D0%B8%D0%BE%D0%B4%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%BE%D0%B5-%D1%80%D0%B5%D0%B7%D0%B5%D1%80%D0%B2%D0%BD%D0%BE%D0%B5-%D0%BA%D0%BE%D0%BF%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-entware-%D0%BA%D0%BE%D0%BD%D1%84%D0%B8%D0%B3%D0%B0-%D0%B8-%D0%BF%D1%80%D0%BE%D1%88%D0%B8%D0%B2%D0%BA%D0%B8/).

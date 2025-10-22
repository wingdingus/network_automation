# network_automation

## main.py

Execute show and run commands on network devices and save output to file.

### Required files:

- creds.txt - device credentials e.g. admin,password
- devices.txt - device ip addresses, one per line.
- cmd.json - json file containing show and config commands.

## cfg_backup.py

Configuration backup script with changes since yesterday output to file.

### Required files:

- creds.txt - device credentials e.g. admin,password
- devices.txt - device ip addresses, one per line.

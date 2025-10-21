# network_automation

## main.py

execute show and run commands on network devices and save output to file, useful for configuration backups.

### Required files:

- creds.txt - device credentials.
- devices.txt = device ip addresses.
- cmd.json = json file containing show and config commands, example below:

  {
  "show": [
  "show ip int brief | exclude unassigned",
  "show version | include Version",
  "show version | include uptime",
  "show running-config"
  ],
  "config": [
  "ntp server 192.168.127.2",
  "ip route 0.0.0.0 0.0.0.0 192.168.127.2"
  ]
  }

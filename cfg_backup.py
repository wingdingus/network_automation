import sys
import os
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetMikoTimeoutException
import threading
from termcolor import colored
from datetime import timedelta, datetime as dt
import filecmp
from difflib import unified_diff

TODAY = dt.now().date()
YESTERDAY = TODAY - timedelta(1)

# get ip addresses of devices from file.
def get_devices():
    with open("devices.txt", 'r') as f:
        devices = f.read().splitlines()
    return devices

# check if the ip addresses are valid.
def is_ip_valid(device_list):
    print(colored("\nValidating ip addresses:", 'white'))
    for ip in device_list:
        octets = ip.split('.')
        if len(octets) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in octets) and (1 <= int(octets[0]) <= 223) and (int(octets[0]) != 127) and (int(octets[0] != 169 and int(octets[1]) != 254)):
            print(colored(f"{ip} is a valid IP address.", 'green'))
        else:
            print(colored(f"{ip} is NOT a valid IP address.", 'red'))
            sys.exit()

# test device reachability.
def device_reachable(device_list):
    print(colored("\nTesting reachability:", 'white'))
    for device in device_list:
        response = os.popen(f"ping -c 2 {device}").read()
        if not "100% packet loss" in response:
            print(colored(f"{device} is reachable.", 'green'))
        else:
            print(colored(f"{device} is not reponding.", 'red'))

# check if required files exists.
def check_files_exist(file_list):
    print(colored("\nChecking for required files:", 'white'))
    for file in file_list:
        if os.path.isfile(file):
            print(colored(f"{file} file found.", 'green'))
        else:
            print(colored(f"{file} file not found."), 'red')
            sys.exit()

# connect to device and execute commands.
def get_running_cfg(creds_file, device_list):
    with open(creds_file, 'r') as f:
        creds = f.read().splitlines()
    username, password = creds[0].split(',')
    backups_list = []
    for device in device_list:
        cisco_device = {
            'device_type': 'cisco_ios',
            'host': device,
            'username': username,
            'password': password,
        }

        print(colored(f"Backing up {device}:", 'white'))
        try:
            session = ConnectHandler(**cisco_device)
            
            output = session.send_command("show running-config")
            filename = f"cfgfiles/{TODAY}_{device}"
            with open(f"{filename}.cfg", 'w') as f:
                f.writelines(f"{output}\n")
            backups_list.append(filename)
            print(colored("Backup complete.", 'green'))
            session.disconnect()
            print()
    
        except (NetmikoAuthenticationException, NetMikoTimeoutException):
            print(colored("Authentication failed or ssh timeout.", 'red'))
    cfg_diff(backups_list)

# get the config difference between today and yesterday.  Output the difference to file.
def cfg_diff(backups_list):
    for name in backups_list:
        yesterday_file = f"cfgfiles/{YESTERDAY}_{name.split('_')[1]}.cfg"
        today_file = f"{name}.cfg"

        with open(today_file, 'r') as a:
            cfg_today = a.read()
        with open(yesterday_file, 'r') as b:
            cfg_yesterday = b.read()

        if filecmp.cmp(today_file, yesterday_file):
            continue
        else:
            diff = unified_diff(cfg_yesterday.splitlines(), cfg_today.splitlines(), lineterm='', n=0)
            with open(f"cfgfiles/{TODAY}_{name.split('_')[1]}_diff.cfg", 'w') as f:
                f.write('\n'.join(list(diff)))

# multithreading function.
def create_threads(list, function):
    threads = []
    for device in list:
        th = threading.Thread(target=function, args=(device,))
        th.start()
        threads.append(th)

    for th in threads:
        th.join()


if __name__ == "__main__":

    # check for required files.
    file_list = []
    creds_file = "creds.txt"
    file_list.append(creds_file)

    device_file = "devices.txt"
    file_list.append(device_file)

    check_files_exist(file_list)

    # get list of device ip addresses.
    device_list = get_devices()

    # check ip addresses are valid.
    is_ip_valid(device_list)

    # ping devices.
    device_reachable(device_list)

    # use multithreading to execute commands.
    create_threads(device_list, get_running_cfg(creds_file, device_list))


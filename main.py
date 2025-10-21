import sys
import os
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetMikoTimeoutException
from datetime import datetime
import threading
import json
from termcolor import colored

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

# check if command is valid and output results to file.
def check_output(output, cmd, device):
    if "% Invalid input" in output:
        if cmd[:4] == "show":
            print(colored(f"Invalid command: {cmd}", 'red'))
        else:
            output_lines = output.splitlines()
            index = next((i for i, line in enumerate(output_lines) if "% Invalid input" in line), -1)
            error_line = f"Invalid command: {output_lines[index-2].split('#', 1)[1]}\n"
            print(colored(error_line, 'red'))
            with open("config_error_log.log", 'a') as f:
                now = datetime.now()
                f.writelines(f"{str(now)} {output_lines[index-2].split('#', 1)[0]} {error_line}\n")
            return False
                
    elif cmd[:4] == "show":
        with open(f"{device}.txt", 'a') as f:
            now = datetime.now()
            f.writelines(f"{str(now)}\n")
            f.writelines(f"{output}\n")
        print(colored(f"{cmd} - success.", 'green'))
    
    else:
        print("Configuration successful.")
        print(colored(f"{cmd} - success.", 'green'))
        return True


# connect to device and execute commands.
def run_commands(creds_file, cmd_file, device_list):
    print(colored("\nExecuting commands:", 'white'))
    with open(creds_file, 'r') as f:
        creds = f.read().splitlines()
    username, password = creds[0].split(',')

    with open(cmd_file, 'r') as f:
        commands = json.load(f)
    show = commands["show"]
    config = commands["config"]
    
    for device in device_list:
        config = commands["config"]
        cisco_device = {
            'device_type': 'cisco_ios',
            'host': device,
            'username': username,
            'password': password,
        }

        print(colored(f"Sending commands to {device}:", 'white'))
        try:
            session = ConnectHandler(**cisco_device)
            
            for cmd in show if show else []:
                output = session.send_command(cmd)
                check_output(output, cmd, device)
            if config:
                output = session.send_config_set(config)
                config_ok = check_output(output, config, device)
                if config_ok:
                    print(colored("Saving config.", 'white'))
                    session.save_config()
            session.disconnect()
            print()
    
        except (NetmikoAuthenticationException, NetMikoTimeoutException):
            print(colored("Authentication failed or ssh timeout.", 'red'))

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

    cmd_file = "cmd.json"
    file_list.append(cmd_file)

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
    create_threads(device_list, run_commands(creds_file, cmd_file, device_list))


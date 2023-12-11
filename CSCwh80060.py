#!/usr/bin/env pthon3
import connecthandlerc9800
import parsedtextfsmc9800
import json
import datetime
import sys

########################################################################################################################

""" Defining the connection to the access point """
def ap_connecthandler(host,login,password,secret):
    ap = {
        'host': host,
        'device_type': 'cisco_ios',
        'username': login,
        'password': password,
        'port': 22,
        'secret': secret,
    }

    return ap

""" Checking the connection availability of the access point """
def aps_with_no_access(check_ap):
    for ap in list_of_aps_with_no_access:
        if ap['IP_Address'] == check_ap['IP_Address']:
            return True
    return False

""" Executing commands on access points """
def execute_command_on_ap(ap_details, command):
    try:
        output = connecthandlerc9800.connecthandlerc9800(ap_connecthandler(ap_details['IP_Address'], login, password, secret), command)
        return output
    except Exception:
        list_of_aps_with_no_access.append({'AP_Name': ap_details['AP_Name'], 'IP_Address': ap_details['IP_Address']})
        return None

""" Executing commands on the WLC """
def connect_to_wlc(device,command):
    command_output = connecthandlerc9800.connecthandlerc9800(device, command)
    return command_output

""" Parsing data into a more readable format """
def parse_and_process_data(template,command_output):
    parsed_data = parsedtextfsmc9800.parsedtextfsm(template, command_output)
    return parsed_data

""" Classifying access points as those that are affected by the bug """
def affected_ap(dot11Radio_slot_vlan, flexconnect_wlan):
    for vlan in dot11Radio_slot_vlan:
        if vlan['Vlan'] == '0':
            for wlan in flexconnect_wlan:
                if (vlan['SSIDs'] == wlan['SSID'] and wlan['Switching'] == 'Local' and wlan['State'] == 'UP'):
                    return True
                else:
                    return False
        else:
            False

""" Formatting the time difference into hours, minutes, and seconds."""
def format_duration(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

""" Analyzing the progress of the script's operation """
def progress_percentage(current_ap,all_aps):
    global start_percentage, start_time
    percentage = int(round(current_ap / all_aps, 1) * 100)
    if percentage > start_percentage:
        start_percentage = percentage
        current_time = datetime.datetime.now()
        elapsed_time = current_time - start_time
        formatted_time = format_duration(elapsed_time)
        print(f"Processed {percentage}% of APs. Time passed: {formatted_time}")

########################################################################################################################

""" This part of the script defines whether it should be executed for all APs or only for those that have the Monitor role set for slot 0.  """

answear = input("\nXOR APs with Monitor role type 1 (default) \nAll APs type 2\nWhich APs want to check:")

if answear == '':
    answear = '1'
elif answear == '2':
    message = "Please note: This script may take a while to complete. Thank you for your patience!"
    message_length = len(message)
    border = "#" * (message_length + 4)

    print(border)
    print("#" + " " * (message_length + 2) + "#")
    print("# " + message + " #")
    print("#" + " " * (message_length + 2) + "#")
    print(border)

elif answear not in ['1', '2']:
    print("You typed something wrong! Script is being terminated!")
    sys.exit()

print('\nPlease provide the connection parameters for the WLC:')
wlc = {
    'host': input("Provide the WLC IP address: "),
    'device_type': 'cisco_ios',
    'username': input("Enter your username: "),
    'password': input("Enter your password: "),
    'port': 22,
    'secret': input("Enter your secret password: "),
}

print('\nPlease provide the connection parameters for the access points:')
login = input("Enter AP login: ")
password = input("Enter AP password: ")
secret = input("Enter AP secret (optional if different than password): ") or password

########################################################################################################################

start_time = datetime.datetime.now()
""" Gathering a list of APs along with their IP addresses.  """

send_command_ap_summary = 'show ap summary'
ap_summary_template = 'wlc_c9800_show_ap_summary'

output_ap_summary = connect_to_wlc(wlc, send_command_ap_summary)
parsed_output_ap_summary = parse_and_process_data(ap_summary_template, output_ap_summary)

ap_list_name_ip = [{'AP_Name':d['AP_Name'],'IP_Address':d['IP_Address']} for d in parsed_output_ap_summary if 'AP_Name' in d and 'IP_Address' in d]

""" Defining commands and templates that will be further used in the code for access points to 
identify those affected by the bug. """

send_command_controllers_dot11Radio_0_vlan = 'show controllers dot11Radio 0 vlan'
send_command_controllers_dot11Radio_1_vlan = 'show controllers dot11Radio 1 vlan'
send_command_flexconnect_wlan = 'show flexconnect wlan'

controllers_dot11Radio_slot_vlan_template = 'ap_c9k_show_controllers_dot11Radio_slot_vlan'
flexconnect_wlan_template = 'ap_c9k_show_flexconnect_wlan'

list_of_aps_with_no_access = []
affected_ap_list_name_ip = []
current_ap = 0
start_percentage = 0

if answear == '1':
    """ Filtering APs in Monitor mode """

    send_command_ap_monitor_mode = 'show ap do dual-band summary extended | i Monitor'
    ap_dot11_dual_band_summary_extended_template = 'wlc_c9800_show_ap_dot11_dual-band_summary_extended'

    command_output_ap_monitor_mode = connect_to_wlc(wlc, send_command_ap_monitor_mode)
    parsed_command_output_ap_monitor_mode = parse_and_process_data(ap_dot11_dual_band_summary_extended_template, command_output_ap_monitor_mode)

    filtered_ap_list_name_ip = [
        {'AP_Name': dict1['AP_Name'], 'IP_Address': dict1['IP_Address']}
        for dict1 in ap_list_name_ip
        for dict2 in parsed_command_output_ap_monitor_mode
        if dict1['AP_Name'] == dict2['AP_Name']
    ]

    """ Checking if APs with XOR radio in Monitor mode are experiencing the problem. This is the first and fundamental 
    way of verifying whether we are encountering the bug. No such behavior was observed yet for APs whose radios were not 
    operating in monitor mode. Just in case, the second part of the code ( answear == 2 ) can also check if the 
    bug is present on other APs."""

    for ap in filtered_ap_list_name_ip:
        current_ap += 1
        progress_percentage(current_ap, len(ap_list_name_ip))

        if aps_with_no_access(ap) is False:
            command_output_controllers_dot11Radio_1_vlan = execute_command_on_ap(ap, send_command_controllers_dot11Radio_1_vlan)
            if command_output_controllers_dot11Radio_1_vlan is None:
                continue
        else:
            continue

        parsed_command_output_controllers_dot11Radio_1_vlan = parse_and_process_data(controllers_dot11Radio_slot_vlan_template,command_output_controllers_dot11Radio_1_vlan)

        if len(parsed_command_output_controllers_dot11Radio_1_vlan) == 0:
            continue
        else:
            command_output_flexconnect_wlan = execute_command_on_ap(ap, send_command_flexconnect_wlan)
            parsed_command_output_flexconnect_wlan = parse_and_process_data(flexconnect_wlan_template,command_output_flexconnect_wlan)
            if affected_ap(parsed_command_output_controllers_dot11Radio_1_vlan, parsed_command_output_flexconnect_wlan) is True:
                affected_ap_list_name_ip.append(ap)
                continue
            else:
                continue


elif answear == '2':
    """ Checking all access points for the occurrence of the problem. """

    for ap in ap_list_name_ip:
        current_ap += 1
        progress_percentage(current_ap, len(ap_list_name_ip))

        if aps_with_no_access(ap) is False:
            command_output_controllers_dot11Radio_0_vlan = execute_command_on_ap(ap, send_command_controllers_dot11Radio_0_vlan)
            if command_output_controllers_dot11Radio_0_vlan is None:
                continue
        else:
            continue
        parsed_command_output_controllers_dot11Radio_0_vlan = parse_and_process_data(controllers_dot11Radio_slot_vlan_template,command_output_controllers_dot11Radio_0_vlan)

        command_output_controllers_dot11Radio_1_vlan = execute_command_on_ap(ap,send_command_controllers_dot11Radio_1_vlan)
        parsed_command_output_controllers_dot11Radio_1_vlan = parse_and_process_data(controllers_dot11Radio_slot_vlan_template,command_output_controllers_dot11Radio_1_vlan)

        if len(parsed_command_output_controllers_dot11Radio_0_vlan) == 0:
            continue
        else:
            command_output_flexconnect_wlan = execute_command_on_ap(ap, send_command_flexconnect_wlan)
            parsed_command_output_flexconnect_wlan = parse_and_process_data(flexconnect_wlan_template,command_output_flexconnect_wlan)
            if affected_ap(parsed_command_output_controllers_dot11Radio_0_vlan, parsed_command_output_flexconnect_wlan) is True:
                affected_ap_list_name_ip.append(ap)
                continue
            else:
                continue


        if len(parsed_command_output_controllers_dot11Radio_1_vlan) == 0:
            continue
        else:
            command_output_flexconnect_wlan = execute_command_on_ap(ap, send_command_flexconnect_wlan)
            parsed_command_output_flexconnect_wlan = parse_and_process_data(flexconnect_wlan_template,command_output_flexconnect_wlan)
            if affected_ap(parsed_command_output_controllers_dot11Radio_1_vlan, parsed_command_output_flexconnect_wlan) is True:
                affected_ap_list_name_ip.append(ap)
                continue
            else:
                continue

else:
    sys.exit()

    """ Saving the results to a file. """

end_time = datetime.datetime.now()

elapsed_time = end_time - start_time
formatted_time = format_duration(elapsed_time)
formatted_time = format_duration(elapsed_time)

timestamp = end_time.strftime("%d_%b_%Y_%H_%M_%S")

aps_with_no_access_json = 'aps_with_no_access_json_'+ str(wlc['host'] + f'_date_{timestamp}')

with open(aps_with_no_access_json, 'wt') as file:
    json.dump(list_of_aps_with_no_access, file, indent = 4)

affected_aps_json = 'affected_aps_json_wlc_' + str(wlc['host'] + f'_date_{timestamp}')

with open(affected_aps_json,'wt') as file:
    json.dump(affected_ap_list_name_ip,file, indent=4)

print("\nCode execution ended. Time passed: ", formatted_time, '\n')
print(f'File created and saved for affected APs by CSCwh80060 bug: {affected_aps_json}')
print(f'File created with APs not checked because of connection issues: {aps_with_no_access_json}')
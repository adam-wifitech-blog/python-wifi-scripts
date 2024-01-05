#!/usr/bin/env pthon3
import connecthandlerc9800 as chc9800
from parsedtextfsmc9800 import parsedtextfsm
import socket
import datetime
import json

########################################################################################################################

""" Defining the list of access points to be checked"""
def ap_list(wlc,command,template):
    wlc_command_output = chc9800.connecthandlerc9800(wlc,command)
    parsed_wlc_command_output = parsedtextfsm(template,wlc_command_output)
    ap_list = list(map(lambda d: {k: d[k] for k in ['AP_Name', 'IP_Address'] if k in d}, parsed_wlc_command_output))
    return ap_list

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

""" Formatting the time difference into hours, minutes, and seconds."""
def format_duration(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

########################################################################################################################

"""" Data for connecting to the controller. """

wlc = {
    'host': input("Provide the WLC IP address: "),
    'device_type': 'cisco_ios',
    'username': input("Enter WLC username: "),
    'password': input("Enter WLC password: "),
    'port': 22,
    'secret': input("Enter WLC secret password: "),
}

ap_summary_command = 'show ap summary'
ap_summary_template = 'wlc_c9800_show_ap_summary'

""" List of APs that will be checked for the possibility of establishing an SSH connection. """
ap_list = ap_list(wlc,ap_summary_command,ap_summary_template)

ap_no_access = []
start_percentage, start_time = 0, datetime.datetime.now()
current_ap = 0

"""Filter APs to which you cannot connect via SSH."""
for ap in ap_list:
    current_ap += 1
    progress_percentage(current_ap, len(ap_list))
    is_alive = chc9800.test_tcp_connection(ap['IP_Address'])
    if not is_alive:
        ap_no_access.append(ap)

""" Saving the results to a file. """

current_time = datetime.datetime.now()
timestamp = current_time.strftime("%d_%b_%Y_%H_%M_%S")
file_name = f'ap_no_access_date_{timestamp}'

with open(file_name, 'wt') as file:
    json.dump(ap_no_access, file, indent = 4)

end_time = datetime.datetime.now()

elapsed_time = end_time - start_time
formatted_time = format_duration(elapsed_time)

print("\nCode execution ended. Time passed: ", formatted_time, '\n')
print(f'File created and saved. Name: {file_name}')

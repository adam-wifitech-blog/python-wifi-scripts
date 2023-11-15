#!/usr/bin/env python3
import connecthandlerc9800
import parsedtextfsmc9800
import json
import time


device = {
    'host': (input("Provide the device's IP address: ")),
    'device_type': 'cisco_ios',
    'username': (input("Enter your username: ")),
    'password': (input("Enter your password: ")),
    'port': 22,
    'secret': (input("Enter your secret password: ")),
}

# Record the start time of the script.
start_time = time.time()

# Define the command and the TextFSM template for parsing its output.
send_command = 'show wireless client summary detail ipv4'
client_summary_detail_ipv4_template = 'wlc_c9800_show_wireless_client_summary_detail_ipv4'

# Execute the command and get its output.
send_command_output = connecthandlerc9800.connecthandlerc9800(device, send_command)

# Parse the command output using the specified TextFSM template.
parsed_text_client_summary_detail_ipv4 = parsedtextfsmc9800.parsedtextfsm(client_summary_detail_ipv4_template, send_command_output)

# Filter out clients with APIPA addresses and store them in a list.
apipa = []
for el in parsed_text_client_summary_detail_ipv4:
    if el['IP_Address'].startswith('169.254'):
        apipa.append(el)

# Save the list of clients with APIPA addresses to a JSON file.
with open("apipa_file_json", 'wt') as f:
    json.dump(apipa, f, indent=4)

# Calculate and print the total execution time of the script.
end_time = time.time()
minutes = (end_time - start_time) // 60
seconds = (end_time - start_time) % 60
print("Script time execution:", int(minutes), "minutes", round(seconds, 1), 'seconds')
print(f'File created and saved: apipa_file_json')

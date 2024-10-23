import csv
import requests
import json
import base64
import argparse

WIGLE_API_NAME = "AID4822f68df9ff7dbcf8f4d040786b4cab"
WIGLE_API_TOKEN = "d27bb92b65039fc0d15340ac85fc8ab3"

# Function to get only Wifi records
def filter_csv(inputFile, outputFile):
    # Read csv and remove null bytes
    with open(inputFile, 'r', encoding='utf-8', errors='replace') as infile:
        content = infile.read().replace('\0', '') 
    
    with open(outputFile, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(content.splitlines())
        writer = csv.writer(outfile)

        for row in reader:
            # Skip bluetooth records
            if not any("BT" in cell or "BLE" in cell for cell in row):
                writer.writerow(row)

# Function to create api call header
def get_basic_auth_header(api_name, api_token):
    credentials = f"{api_name}:{api_token}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded_credentials}"

# Function to make a request
def fetch_wifi_details(ssid):
    url = "https://api.wigle.net/api/v2/network/detail"
    headers = {
        'Authorization': get_basic_auth_header(WIGLE_API_NAME, WIGLE_API_TOKEN)
    }
    params = {
        'netid': ssid  # Send ssid to get detail of network
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 400:
        print(f"Failed to fetch data for SSID {ssid}: Request body error")
        return None
    elif response.status_code == 401:
        print(f"Failed to fetch data for SSID {ssid}: Not authenticated")
        return None
    elif response.status_code == 403:
        print(f"Failed to fetch data for SSID {ssid}: Commercial request made for non-commercial resource")
        return None
    elif response.status_code == 404:
        print(f"Failed to fetch data for SSID {ssid}: No network records matching search criteria found")
        return None
    elif response.status_code == 429:
        print(f"Failed to fetch data for SSID {ssid}: Too many queries today")
        return False
    else:
        print(f"Failed to fetch data for SSID {ssid}: {response.status_code}")
        return None

def downloadData(knownAPs, outputCsv, wifiFile, knownAPsFile):
    # Load any existing wifi data to append new data
    try:
        with open(wifiFile, 'r') as json_file:
            wifiData = json.load(json_file)
    except FileNotFoundError:
        wifiData = []

    newAPs = []

    with open(outputCsv, 'r', encoding='utf-8') as outfile:
        reader = csv.reader(outfile, delimiter=',')

        for row in reader:
            print(f'Now on: {row[0]}')
            if row[0] == 'WigleWifi-1.6' or row[0] == 'MAC': # skip header rows
                continue

            if row[0] not in knownAPs:
                knownAPs.append(row[0])
                newAPs.append(row[0])
                
                wifiDetails = fetch_wifi_details(row[0])
                if wifiDetails is False:
                    break
                if wifiDetails:
                    wifiData.append(wifiDetails)

    # Save wifi data to the file
    with open(wifiFile, 'w') as json_file:
        json.dump(wifiData, json_file, indent=4)
        #print(f"Data saved to {wifiData}")

    if newAPs:
        with open(knownAPsFile, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows([[ap] for ap in newAPs])  # Append new known APs
        print(f"New known APs saved to {knownAPsFile}")

def reformat(mac_address):
    return ''.join(mac_address).replace(",", "")

if __name__ == "__main__": 

    parser = argparse.ArgumentParser(description='DataPuller')
    parser.add_argument('inputCsv',type=str) # Data collected from Wigle app

    args = parser.parse_args()

    inputCsv = args.inputCsv  
    outputCsv = 'output.csv'  
    knownAPsFile = 'knownAPs.csv' # To prevent duplicit calls because of api call limit
    wifiData = 'wifiData.json'

    # Clear output file
    f = open(outputCsv, 'w+')
    f.close()

    with open(knownAPsFile, newline='') as csvfile:
        knownAPs = [reformat(row) for row in csv.reader(csvfile)]

    filter_csv(inputCsv, outputCsv)
    downloadData(knownAPs, outputCsv, wifiData, knownAPsFile)



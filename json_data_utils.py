import json

import requests


def get_data_path():
    # Data folder
    data_path = "data/"

    return data_path


def download_data(url):
    response = requests.get(url)
    status_code = response.status_code

    if status_code == 200:
        data = response.json()
    else:
        print('Faulty response status code = ' + str(status_code) + ' for url = ' + url)
        data = None

    return data, status_code


def save_data(json_filename, json_data):
    # Make sure the json data is using double quotes instead of single quotes
    # Reference: https://stackoverflow.com/a/8710579/
    json_data_as_str = json.dumps(json_data)

    with open(json_filename, 'w', encoding="utf8") as out_json_file:
        print(json_data_as_str, file=out_json_file)

    return


def load_data(json_filename):
    with open(json_filename, 'r', encoding="utf8") as in_json_file:
        data = json.load(in_json_file)

    return data


if __name__ == '__main__':
    print('Nothing to do.')

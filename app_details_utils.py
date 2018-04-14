import pathlib

from json_data_utils import download_data, save_data, load_data


def download_app_details(app_id):
    url = 'http://store.steampowered.com/api/appdetails?appids=' + app_id
    (data, status_code) = download_data(url)
    success_flag = bool(data is not None)

    downloaded_app_details = {}

    if success_flag:
        downloaded_app_details = data[app_id]['data']
        success_flag = data[app_id]['success']

    return downloaded_app_details, success_flag


def get_json_filename_for_app_details(app_id):
    # Objective: return the filename of the app details corresponding to the input appID

    # Data folder
    # noinspection SpellCheckingInspection
    data_path = "data/appdetails/"

    # Reference of the following line: https://stackoverflow.com/a/14364249
    pathlib.Path(data_path).mkdir(parents=True, exist_ok=True)

    # Database filename
    json_base_filename = 'appID_' + app_id + '.json'

    # Database filename
    json_filename = data_path + json_base_filename

    return json_filename


def load_app_details(app_id):
    json_filename = get_json_filename_for_app_details(app_id)

    try:
        loaded_app_details = load_data(json_filename)
        success_flag = True
    except FileNotFoundError:
        (loaded_app_details, success_flag) = download_app_details(app_id)
        if success_flag:
            save_data(json_filename, loaded_app_details)

    return loaded_app_details, success_flag


if __name__ == '__main__':
    appID = '440'
    (app_details, is_success) = load_app_details(appID)

import pathlib

from json_data_utils import download_data, save_data, load_data


def download_app_details(app_id):
    url = 'http://store.steampowered.com/api/appdetails?appids=' + app_id
    (data, status_code) = download_data(url)

    downloaded_app_details = {}

    if data is not None:
        downloaded_app_details = data[app_id]['data']

    return downloaded_app_details


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
    except FileNotFoundError:
        loaded_app_details = download_app_details(app_id)
        save_data(json_filename, loaded_app_details)

    return loaded_app_details


if __name__ == '__main__':
    appID = '440'
    app_details = load_app_details(appID)

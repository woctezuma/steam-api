import pathlib
import time

from json_data_utils import download_data, save_data, load_data


def download_steam_catalog():
    url = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/'
    (data, status_code) = download_data(url)

    downloaded_steam_catalog = {}

    if data is not None:

        # noinspection SpellCheckingInspection
        for app in data['applist']['apps']:
            # noinspection SpellCheckingInspection
            app_id = str(app['appid'])
            app_name = app['name']

            downloaded_steam_catalog[app_id] = {}
            downloaded_steam_catalog[app_id]['name'] = app_name

    return downloaded_steam_catalog


# noinspection SpellCheckingInspection
def get_json_filename_for_steam_catalog():
    # Objective: return the filename of the Steam catalog

    # Data folder
    data_path = "data/"

    # Reference of the following line: https://stackoverflow.com/a/14364249
    pathlib.Path(data_path).mkdir(parents=True, exist_ok=True)

    # Get current day as yyyymmdd format
    date_format = "%Y%m%d"
    current_date = time.strftime(date_format)

    json_base_filename = current_date + "_steam_catalog.json"

    # Database filename
    json_filename = data_path + json_base_filename

    return json_filename


def load_steam_catalog():
    json_filename = get_json_filename_for_steam_catalog()

    try:
        loaded_steam_catalog = load_data(json_filename)
    except FileNotFoundError:
        loaded_steam_catalog = download_steam_catalog()
        save_data(json_filename, loaded_steam_catalog)

    return loaded_steam_catalog


if __name__ == '__main__':
    steam_catalog = load_steam_catalog()

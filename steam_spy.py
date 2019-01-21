import logging
import pathlib
import time

import steampi.api
import steampi.json_utils
import steamspypi

from steam_catalog_utils import load_steam_catalog


def get_previously_seen_app_ids_of_games():
    log_filename = steampi.json_utils.get_data_path() + 'successful_appIDs.txt'

    return log_filename


def get_previously_seen_app_ids_of_non_games():
    log_filename = steampi.json_utils.get_data_path() + 'faulty_appIDs.txt'

    return log_filename


def load_text_file(file_name):
    try:
        with open(file_name, "r") as f:
            file_content = set([line.strip() for line in f])
    except FileNotFoundError:
        file_content = []
        pathlib.Path(file_name).touch()
    return file_content


def load_previously_seen_app_ids(include_faulty_app_ids=True):
    previously_seen_app_ids = set()

    success_filename = get_previously_seen_app_ids_of_games()
    error_filename = get_previously_seen_app_ids_of_non_games()

    filename_list = [success_filename]
    if include_faulty_app_ids:
        filename_list.append(error_filename)

    for appid_log_file_name in filename_list:
        parsed_app_ids = load_text_file(appid_log_file_name)
        previously_seen_app_ids = previously_seen_app_ids.union(parsed_app_ids)

    return previously_seen_app_ids


def scrape_steam_data(import_my_own_steam_catalog=True, try_again_faulty_app_ids=False, focus_on_probable_games=False):
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.DEBUG)
    log = logging.getLogger(__name__)

    query_rate_limit = 200  # Number of queries which can be successfully issued during a 4-minute time window
    wait_time = (4 * 60) + 10  # 4 minutes plus a cushion
    successful_status_code = 200  # Status code for a successful HTTP response

    query_count = 0

    if import_my_own_steam_catalog:
        (steam_catalog, is_success, query_status_code) = load_steam_catalog()

        if not is_success:
            raise AssertionError()
        if query_status_code is not None:
            query_count += 1
    else:
        steam_catalog = steamspypi.load()

    all_app_ids = list(steam_catalog.keys())

    if import_my_own_steam_catalog and focus_on_probable_games:
        # Caveat: this is not foolproof!
        # The following is merely a way to focus on appIDs which are very likely linked to a game (and not a DLC, etc.).
        #
        # Most of Steam games have an appID which ends with a '0'.
        # For instance, 99.8% (27421/27468) of games in the offical SteamSpy database have an appID ending with a '0'.
        #
        # In comparison, in my home-made Steam catalog, 71.8% (52741/73453) of appIDs end with a '0'.
        # Before we download the app details, we do not know whether they are linked to games, DLC, videos, etc.
        all_app_ids = [app_id for app_id in all_app_ids if app_id.endswith('0')]

    include_faulty_app_ids = not try_again_faulty_app_ids
    previously_seen_app_ids = load_previously_seen_app_ids(include_faulty_app_ids=include_faulty_app_ids)

    unseen_app_ids = set(all_app_ids).difference(previously_seen_app_ids)

    unseen_app_ids = sorted(unseen_app_ids, key=int)

    success_filename = get_previously_seen_app_ids_of_games()
    error_filename = get_previously_seen_app_ids_of_non_games()

    for appID in unseen_app_ids:

        if query_count >= query_rate_limit:
            log.info("query count is %d ; limit %d reached. Wait for %d sec", query_count, query_rate_limit, wait_time)
            time.sleep(wait_time)
            query_count = 0

        (_, is_success, query_status_code) = steampi.api.load_app_details(appID)
        if query_status_code is not None:
            query_count += 1

        while (query_status_code is not None) and (query_status_code != successful_status_code):
            log.info("query count is %d ; HTTP response %d. Wait for %d sec", query_count, query_status_code, wait_time)
            time.sleep(wait_time)
            query_count = 0

            (_, is_success, query_status_code) = steampi.api.load_app_details(appID)
            if query_status_code is not None:
                query_count += 1

        appid_log_file_name = success_filename
        if (query_status_code is not None) and not is_success:
            if not (query_status_code == successful_status_code):
                raise AssertionError()
            appid_log_file_name = error_filename

        with open(appid_log_file_name, "a") as f:
            f.write(appID + '\n')


if __name__ == '__main__':
    print('Scraping data from the web')
    scrape_steam_data(import_my_own_steam_catalog=True, try_again_faulty_app_ids=False, focus_on_probable_games=True)

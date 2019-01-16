import logging
import pathlib
import time

import steampi.api
import steampi.json_utils

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


def load_previously_seen_app_ids():
    previously_seen_app_ids = set()

    success_filename = get_previously_seen_app_ids_of_games()
    error_filename = get_previously_seen_app_ids_of_non_games()

    for appid_log_file_name in [success_filename, error_filename]:
        parsed_app_ids = load_text_file(appid_log_file_name)
        previously_seen_app_ids = previously_seen_app_ids.union(parsed_app_ids)

    return previously_seen_app_ids


def scrape_steam_data():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.DEBUG)
    log = logging.getLogger(__name__)

    query_rate_limit = 200  # Number of queries which can be successfully issued during a 4-minute time window
    wait_time = (4 * 60) + 10  # 4 minutes plus a cushion
    successful_status_code = 200  # Status code for a successful HTTP response

    query_count = 0

    (steam_catalog, is_success, query_status_code) = load_steam_catalog()

    if not is_success:
        raise AssertionError()
    if query_status_code is not None:
        query_count += 1

    all_app_ids = list(steam_catalog.keys())

    previously_seen_app_ids = load_previously_seen_app_ids()

    unseen_app_ids = set(all_app_ids).difference(previously_seen_app_ids)

    unseen_app_ids = sorted(unseen_app_ids, key=lambda x: int(x))

    success_filename = get_previously_seen_app_ids_of_games()
    error_filename = get_previously_seen_app_ids_of_non_games()

    for appID in unseen_app_ids:

        if query_count >= query_rate_limit:
            log.info("query count is %d ; limit %d reached. Wait for %d sec", query_count, query_rate_limit, wait_time)
            time.sleep(wait_time)
            query_count = 0

        (app_details, is_success, query_status_code) = steampi.api.load_app_details(appID)
        if query_status_code is not None:
            query_count += 1

        while (query_status_code is not None) and (query_status_code != successful_status_code):
            log.info("query count is %d ; HTTP response %d. Wait for %d sec", query_count, query_status_code, wait_time)
            time.sleep(wait_time)
            query_count = 0

            (app_details, is_success, query_status_code) = steampi.api.load_app_details(appID)
            if query_status_code is not None:
                query_count += 1

        appid_log_file_name = success_filename
        if (query_status_code is not None) and not is_success:
            if not (query_status_code == successful_status_code):
                raise AssertionError()
            appid_log_file_name = error_filename

        with open(appid_log_file_name, "a") as f:
            f.write(appID + '\n')


def aggregate_steam_data(verbose=True):
    success_filename = get_previously_seen_app_ids_of_games()

    parsed_app_ids = load_text_file(success_filename)

    parsed_app_ids = sorted(parsed_app_ids, key=lambda x: int(x))

    all_possible_info_type = []

    steam_database = {}
    all_categories = {}
    all_genres = {}

    for appID in parsed_app_ids:
        (app_details, is_success, query_status_code) = steampi.api.load_app_details(appID)

        if app_details['type'] == 'game':

            # Keep track of the kind of info which can be found through Steam API
            for available_info in app_details.keys():
                if available_info not in all_possible_info_type:
                    all_possible_info_type.append(available_info)

            steam_database[appID] = {}
            steam_database[appID]['name'] = app_details['name']
            steam_database[appID]['steam_appid'] = app_details['steam_appid']
            steam_database[appID]['required_age'] = app_details['required_age']
            steam_database[appID]['is_free'] = app_details['is_free']

            try:
                steam_database[appID]['developers'] = app_details['developers']
            except KeyError:
                steam_database[appID]['developers'] = None

            steam_database[appID]['publishers'] = app_details['publishers']

            try:
                steam_database[appID]['price_overview'] = app_details['price_overview']['initial']
            except KeyError:
                steam_database[appID]['price_overview'] = None

            steam_database[appID]['platforms'] = app_details['platforms']

            try:
                steam_database[appID]['metacritic'] = app_details['metacritic']['score']
            except KeyError:
                steam_database[appID]['metacritic'] = None

            try:
                steam_database[appID]['categories'] = [categorie['id'] for categorie in app_details['categories']]

                d = {}
                for elem in app_details['categories']:
                    k = elem['id']
                    v = elem['description']
                    d[k] = v
                all_categories.update(d)

            except KeyError:
                steam_database[appID]['categories'] = []

            try:
                steam_database[appID]['genres'] = [int(genre['id']) for genre in app_details['genres']]

                d = {}
                for elem in app_details['genres']:
                    k = int(elem['id'])
                    v = elem['description']
                    d[k] = v
                all_genres.update(d)

            except KeyError:
                steam_database[appID]['genres'] = []

            try:
                steam_database[appID]['recommendations'] = app_details['recommendations']['total']
            except KeyError:
                steam_database[appID]['recommendations'] = 0

            try:
                steam_database[appID]['achievements'] = app_details['achievements']['total']
            except KeyError:
                steam_database[appID]['achievements'] = 0

            release_info = app_details['release_date']
            steam_database[appID]['release_date'] = {}
            steam_database[appID]['release_date']['date'] = release_info['date']
            steam_database[appID]['release_date']['is_released'] = not (release_info['coming_soon'])

            try:
                steam_database[appID]['dlc'] = len(app_details['dlc'])
            except KeyError:
                steam_database[appID]['dlc'] = 0

            steam_database[appID]['demos'] = bool('demos' in app_details)

            steam_database[appID]['controller_support'] = bool('controller_support' in app_details)

            try:
                steam_database[appID]['drm_notice'] = app_details['drm_notice']
            except KeyError:
                steam_database[appID]['drm_notice'] = None

            steam_database[appID]['ext_user_account_notice'] = bool('ext_user_account_notice' in app_details)

    if verbose:
        print('All possible pieces of information which can be fetched via Steam API:')
        print('\n'.join(all_possible_info_type))
        print()

    return steam_database, all_categories, all_genres


def get_steam_database_filename():
    steam_database_filename = steampi.json_utils.get_data_path() + 'steamspy.json'

    return steam_database_filename


def get_steam_categories_filename():
    steam_categories_filename = steampi.json_utils.get_data_path() + 'categories.json'

    return steam_categories_filename


def get_steam_genres_filename():
    steam_genres_filename = steampi.json_utils.get_data_path() + 'genres.json'

    return steam_genres_filename


if __name__ == '__main__':
    print('Scraping data from the web')
    scrape_steam_data()

    print('Aggregating data locally')
    (steamspy_database, categories, genres) = aggregate_steam_data()

    print('Saving')
    steampi.json_utils.save_json_data(get_steam_database_filename(), steamspy_database)
    steampi.json_utils.save_json_data(get_steam_categories_filename(), categories)
    steampi.json_utils.save_json_data(get_steam_genres_filename(), genres)

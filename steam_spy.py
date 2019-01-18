import asyncio
import json
import pathlib
import time

import aiohttp
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


async def fetch(session, url, params=None):
    successful_status_code = 200  # Status code for a successful HTTP response

    if params is None:
        params = {}

    async with session.get(url, params=params) as response:
        if response.status == successful_status_code:
            result = await response.json()
        else:
            result = None
        return result


async def fetch_steam_data(app_id_batch):
    # Reference: https://stackoverflow.com/a/50312981

    steam_url = 'http://store.steampowered.com/api/appdetails'

    tasks = []
    async with aiohttp.ClientSession() as session:
        for app_id in app_id_batch:
            params = {'appids': str(app_id)}
            tasks.append(fetch(session, steam_url, params))
        jsons = await asyncio.gather(*tasks)

    return jsons


def save_steam_data_to_disk(app_id_batch, jsons):
    print('Saving results to disk.')

    counter = 0
    for (app_id, json_data) in zip(app_id_batch, jsons):
        if json_data is not None:
            json_filename = 'data/appdetails/appID_' + str(app_id) + '.json'
            with open(json_filename, 'w', encoding='utf8') as f:
                print(json.dumps(json_data), file=f)

            appid_log_file_name = get_previously_seen_app_ids_of_games()
            counter += 1
        else:
            appid_log_file_name = get_previously_seen_app_ids_of_non_games()

        with open(appid_log_file_name, "a") as f:
            f.write(str(app_id) + '\n')

    print('{}/{} app details have been saved to disk.'.format(counter, len(app_id_batch)))

    return counter


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    # Reference: https://stackoverflow.com/a/312464
    for i in range(0, len(l), n):
        yield l[i:i + n]


def scrape_steam_data():
    query_rate_limit = 50  # Number of queries which can be successfully issued during a 1-minute time window
    wait_time = 60 + 2.5  # 1 minute plus a cushion

    (steam_catalog, _, _) = load_steam_catalog()

    all_app_ids = list(steam_catalog.keys())

    previously_seen_app_ids = load_previously_seen_app_ids()

    unseen_app_ids = set(all_app_ids).difference(previously_seen_app_ids)

    unseen_app_ids = sorted(unseen_app_ids, key=int)

    for app_id_batch in chunks(unseen_app_ids, query_rate_limit):
        loop = asyncio.get_event_loop()
        jsons = loop.run_until_complete(fetch_steam_data(app_id_batch))
        counter = save_steam_data_to_disk(app_id_batch, jsons)

        if counter == 0:
            break

        print('Query limit {} reached. Wait for {} seconds.'.format(query_rate_limit, wait_time))
        time.sleep(wait_time)

    return


def aggregate_steam_data(verbose=True):
    success_filename = get_previously_seen_app_ids_of_games()

    parsed_app_ids = load_text_file(success_filename)

    parsed_app_ids = sorted(parsed_app_ids, key=int)

    all_possible_info_type = []

    steam_database = {}
    all_categories = {}
    all_genres = {}

    for appID in parsed_app_ids:
        app_details, _, _ = steampi.api.load_app_details(appID)

        if app_details['type'] == 'game':

            # Keep track of the kind of info which can be found through Steam API
            for available_info in app_details:
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

import asyncio
import json
import pathlib

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


async def fetch_on_cooldown(wait_time):
    print('Waiting for {} seconds.'.format(wait_time))
    await asyncio.sleep(wait_time)
    print('Resuming.')

async def fetch_steam_data(app_id_batch, wait_time):
    # Reference: https://stackoverflow.com/a/50312981

    steam_url = 'http://store.steampowered.com/api/appdetails'

    tasks = []
    async with aiohttp.ClientSession() as session:
        for app_id in app_id_batch:
            params = {'appids': str(app_id)}
            tasks.append(fetch(session, steam_url, params))
        jsons = await asyncio.gather(*tasks)

    return jsons


async def save_steam_data_to_disk(app_id_batch, jsons):
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


async def save_steam_data_to_disk_and_wait(app_id_batch, jsons, wait_time):
    task_save = asyncio.create_task(save_steam_data_to_disk(app_id_batch, jsons))
    task_cooldown = asyncio.create_task(fetch_on_cooldown(wait_time))

    counter = await task_save
    await task_cooldown

    return counter


def scrape_steam_data():
    query_rate_limit = 200  # Number of queries which can be successfully issued during a 4-minute time window
    wait_time = (4 * 60) + 10  # 4 minutes plus a cushion

    (steam_catalog, _, _) = load_steam_catalog()

    all_app_ids = list(steam_catalog.keys())

    previously_seen_app_ids = load_previously_seen_app_ids()

    unseen_app_ids = set(all_app_ids).difference(previously_seen_app_ids)

    unseen_app_ids = sorted(unseen_app_ids, key=int)

    total_counter = 0
    for app_id_batch in chunks(unseen_app_ids, query_rate_limit):
        jsons = asyncio.run(
            fetch_steam_data(app_id_batch, wait_time)
        )
        counter = asyncio.run(
            save_steam_data_to_disk_and_wait(app_id_batch, jsons, wait_time)
        )

        if counter == 0:
            print('Total: {} app details have been saved to disk.'.format(total_counter))
            break
        else:
            total_counter += counter

    return


if __name__ == '__main__':
    print('Scraping data from the web')
    scrape_steam_data()

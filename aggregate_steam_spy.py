import steampi.api
import steampi.json_utils

from steam_spy import get_previously_seen_app_ids_of_games, load_text_file


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

        if app_details is None or 'type' not in app_details:
            print(
                'AppID {} does not have a "type" key, so we cannot check whether it matches a game.'.format(
                    appID,
                ),
            )
            continue

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
                steam_database[appID]['price_overview'] = app_details['price_overview'][
                    'initial'
                ]
            except KeyError:
                steam_database[appID]['price_overview'] = None

            steam_database[appID]['platforms'] = app_details['platforms']

            try:
                steam_database[appID]['metacritic'] = app_details['metacritic']['score']
            except KeyError:
                steam_database[appID]['metacritic'] = None

            try:
                steam_database[appID]['categories'] = [
                    categorie['id'] for categorie in app_details['categories']
                ]

                d = {}
                for elem in app_details['categories']:
                    k = elem['id']
                    v = elem['description']
                    d[k] = v
                all_categories.update(d)

            except KeyError:
                steam_database[appID]['categories'] = []

            try:
                steam_database[appID]['genres'] = [
                    int(genre['id']) for genre in app_details['genres']
                ]

                d = {}
                for elem in app_details['genres']:
                    k = int(elem['id'])
                    v = elem['description']
                    d[k] = v
                all_genres.update(d)

            except KeyError:
                steam_database[appID]['genres'] = []

            try:
                steam_database[appID]['recommendations'] = app_details[
                    'recommendations'
                ]['total']
            except KeyError:
                steam_database[appID]['recommendations'] = 0

            try:
                steam_database[appID]['achievements'] = app_details['achievements'][
                    'total'
                ]
            except KeyError:
                steam_database[appID]['achievements'] = 0

            release_info = app_details['release_date']
            steam_database[appID]['release_date'] = {}
            steam_database[appID]['release_date']['date'] = release_info['date']
            steam_database[appID]['release_date']['is_released'] = not (
                release_info['coming_soon']
            )

            try:
                steam_database[appID]['dlc'] = len(app_details['dlc'])
            except KeyError:
                steam_database[appID]['dlc'] = 0

            steam_database[appID]['demos'] = bool('demos' in app_details)

            steam_database[appID]['controller_support'] = bool(
                'controller_support' in app_details,
            )

            try:
                steam_database[appID]['drm_notice'] = app_details['drm_notice']
            except KeyError:
                steam_database[appID]['drm_notice'] = None

            steam_database[appID]['ext_user_account_notice'] = bool(
                'ext_user_account_notice' in app_details,
            )

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
    print('Aggregating data locally')
    (steamspy_database, categories, genres) = aggregate_steam_data()

    print('Saving')
    steampi.json_utils.save_json_data(get_steam_database_filename(), steamspy_database)
    steampi.json_utils.save_json_data(get_steam_categories_filename(), categories)
    steampi.json_utils.save_json_data(get_steam_genres_filename(), genres)

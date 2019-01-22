import json
import re

import steampi.api

from steam_spy import load_text_file, get_previously_seen_app_ids_of_games


def aggregate_game_descriptions_from_steam_data(output_filename='aggregate.json', verbose=True):
    try:
        with open(output_filename, "r") as f:
            aggregate = json.load(f)
    except FileNotFoundError:
        aggregate = dict()

    # Variable used for debugging
    app_id_errors = list()

    game_description_label = 'about_the_game'

    successful_app_id_filename = get_previously_seen_app_ids_of_games()

    parsed_app_ids = load_text_file(successful_app_id_filename)

    parsed_app_ids = set(parsed_app_ids).difference(aggregate.keys())

    for app_id in sorted(parsed_app_ids, key=int):
        app_details, _, _ = steampi.api.load_app_details(app_id)

        try:
            app_name = app_details['name']
        except KeyError:
            if verbose:
                print('Name not found for appID = {}'.format(app_id))
                app_id_errors.append(app_id)
            continue
        except TypeError:
            if verbose:
                print('File empty for appID = {}'.format(app_id))
                app_id_errors.append(app_id)
            continue

        try:
            app_type = app_details['type']
        except KeyError:
            if verbose:
                print('Missing type for appID = {} ({})'.format(app_id, app_name))
                app_id_errors.append(app_id)
            continue

        if app_type == 'game':
            try:
                supported_languages = app_details['supported_languages']
            except KeyError:
                if verbose:
                    print('Missing information regarding language support for appID = {} ({})'.format(app_id, app_name))
                    app_id_errors.append(app_id)
                continue

            parsed_supported_languages = re.split(r'\W+', supported_languages)
            if 'English' in parsed_supported_languages:
                app_description = app_details[game_description_label]

                if len(app_description) > 0:
                    aggregate[app_id] = dict()
                    aggregate[app_id]['name'] = app_name
                    aggregate[app_id]['text'] = app_description
            else:
                if verbose:
                    print('English not supported for appID = {} ({})'.format(app_id, app_name))
                continue

    if verbose:
        print('\nList of appIDs which were associated with erroneous or incomplete JSON app details:\n')
        print(app_id_errors)

    with open(output_filename, "w") as f:
        json.dump(aggregate, f)


if __name__ == '__main__':
    print('Aggregating game descriptions')
    aggregate_game_descriptions_from_steam_data()

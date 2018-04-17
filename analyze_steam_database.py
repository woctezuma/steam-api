import datetime

import matplotlib.pyplot as plt
import numpy as np

from json_data_utils import load_data
from steam_spy import get_steam_database_filename, get_steam_categories_filename, get_steam_genres_filename


def load_aggregated_database():
    steam_database = load_data(get_steam_database_filename())
    all_categories = load_data(get_steam_categories_filename())
    all_genres = load_data(get_steam_genres_filename())

    return steam_database, all_categories, all_genres


def get_description_keywords(steam_database, verbose=False):
    description_keywords = set()
    for appID in steam_database:
        current_keywords = steam_database[appID].keys()
        description_keywords = description_keywords.union(current_keywords)

    description_keywords = sorted(description_keywords)

    if verbose:
        print('\nDescription keywords:')
        print('\n'.join(description_keywords))

    return description_keywords


def build_steam_calendar(steam_database, verbose=False):
    # Objective: build a calendar of game releases, as a dict: datetime -> list of appIDs

    release_calendar = dict()
    weird_release_dates = set()
    weird_counter = 0

    for appID in steam_database:
        release_info = steam_database[appID]['release_date']

        is_released = release_info['is_released']
        release_date_as_str = release_info['date']

        if not is_released:
            continue

        release_date_as_str = release_date_as_str.replace(',', '')  # "Nov 11, 2017" == "Nov 11 2017"
        release_date_as_str = release_date_as_str.replace('сен.', 'September')  # Specifically for appID=689740

        try:
            # Reference: https://stackoverflow.com/a/6557568/
            release_date_as_datetime = datetime.datetime.strptime(release_date_as_str, '%b %d %Y')
        except ValueError:
            try:
                release_date_as_datetime = datetime.datetime.strptime(release_date_as_str, '%d %b %Y')
            except ValueError:
                try:
                    release_date_as_datetime = datetime.datetime.strptime(release_date_as_str, '%B %d %Y')
                except ValueError:
                    try:
                        release_date_as_datetime = datetime.datetime.strptime(release_date_as_str, '%d %B %Y')
                    except ValueError:
                        try:
                            release_date_as_datetime = datetime.datetime.strptime(release_date_as_str, '%b %Y')
                        except ValueError:
                            weird_release_dates.add(release_date_as_str)
                            weird_counter += 1
                            if verbose:
                                if weird_counter == 1:
                                    print('\nGames being sold with weird release dates:')
                                if steam_database[appID]['price_overview'] is not None:
                                    if not (steam_database[appID]['is_free']):
                                        sentence = 'appID={0:6}\t' + steamspy_database[appID]['name']
                                        print(sentence.format(appID))
                            continue

        try:
            release_calendar[release_date_as_datetime].append(appID)
        except KeyError:
            release_calendar[release_date_as_datetime] = [appID]

    weird_release_dates = sorted(weird_release_dates)

    if verbose:
        print('\nWeird release dates:')
        print('\n'.join(weird_release_dates))

    return release_calendar, weird_release_dates


def plot_time_series_num_releases(release_calendar):
    x = []
    y = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:
        app_ids = release_calendar[release_date]

        value = len(app_ids)

        x.append(release_date)
        y.append(value)

    plt.plot(x, y)
    plt.title('Number of Steam releases per day')
    plt.show()

    return


def plot_time_series_median_price(release_calendar, steam_database):
    x = []
    y = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:
        app_ids = release_calendar[release_date]

        prices = [steam_database[app_id]['price_overview'] for app_id in app_ids
                  if steam_database[app_id]['price_overview'] is not None]
        if len(prices) == 0:
            continue
        value = np.median(prices)

        x.append(release_date)
        y.append(value)

    plt.plot(x, y)
    plt.title('Median price of Steam releases per day')
    plt.show()

    return


if __name__ == '__main__':
    steamspy_database, categories, genres = load_aggregated_database()

    keywords = get_description_keywords(steamspy_database, verbose=True)

    steam_calendar, weird_dates = build_steam_calendar(steamspy_database, verbose=False)

    plot_time_series_num_releases(steam_calendar)

    plot_time_series_median_price(steam_calendar, steamspy_database)

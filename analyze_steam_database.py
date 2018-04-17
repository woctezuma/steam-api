import datetime
import pathlib

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
                                        sentence = 'appID={0:6}\t' + steam_database[appID]['name']
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


def get_full_plot_filename(base_plot_filename):
    output_folder = 'plots/'
    pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)

    file_extension = '.png'
    full_plot_filename = output_folder + base_plot_filename + file_extension

    return full_plot_filename


def plot_time_series_num_releases(release_calendar):
    x = []
    y = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:
        app_ids = release_calendar[release_date]

        value = len(app_ids)

        x.append(release_date)
        y.append(value)

    fig, ax = plt.subplots(dpi=300)

    plt.plot(x, y)
    plt.title('Number of games released on Steam each month')
    plt.xlabel('Date')
    plt.ylabel('Number of game releases')

    plt.tight_layout()
    plt.grid()
    base_plot_filename = 'num_releases'
    fig.savefig(get_full_plot_filename(base_plot_filename), bbox_inches='tight')
    plt.close(fig)

    return


def plot_time_series_price(release_calendar, steam_database, statistic_str='Median'):
    x = []
    y = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:
        app_ids = release_calendar[release_date]

        prices_in_cents = [steam_database[app_id]['price_overview'] for app_id in app_ids
                           if steam_database[app_id]['price_overview'] is not None]
        if len(prices_in_cents) == 0:
            continue

        if statistic_str == 'Median':
            price_summary_in_cents = np.median(prices_in_cents)
        else:
            price_summary_in_cents = np.average(prices_in_cents)

        price_summary_in_euros = price_summary_in_cents / 100
        value = price_summary_in_euros

        x.append(release_date)
        y.append(value)

    fig, ax = plt.subplots(dpi=300)

    plt.plot(x, y)
    plt.title(statistic_str + ' price of games released on Steam each month')
    plt.xlabel('Date')
    plt.ylabel(statistic_str + ' price (in €)')

    plt.tight_layout()
    plt.grid()
    base_plot_filename = statistic_str.lower() + '_price'
    fig.savefig(get_full_plot_filename(base_plot_filename), bbox_inches='tight')
    plt.close(fig)

    return


def simplify_calendar(release_calendar):
    # Objective: merge daily dates into monthly dates

    merged_calendar = dict()
    for release_date in release_calendar:
        merged_release_date = datetime.date(release_date.year, release_date.month, 1)
        try:
            merged_calendar[merged_release_date].extend(release_calendar[release_date])
        except KeyError:
            merged_calendar[merged_release_date] = release_calendar[release_date]

    return merged_calendar


def remove_current_date(release_calendar):
    # Objective: remove partial data just before plotting time-series

    now = datetime.datetime.now()

    this_day = datetime.date(now.year, now.month, now.day)

    this_month = datetime.date(this_day.year, this_day.month, 1)

    # Start by copying the dictionary
    # Reference: https://stackoverflow.com/a/5844692
    filtered_calendar = dict(release_calendar)
    try:
        del filtered_calendar[this_day]
    except KeyError:
        try:
            del filtered_calendar[this_month]
        except KeyError:
            print('No recent date could be removed from the calendar.')

    return filtered_calendar


if __name__ == '__main__':
    steamspy_database, categories, genres = load_aggregated_database()

    keywords = get_description_keywords(steamspy_database, verbose=True)

    steam_calendar, weird_dates = build_steam_calendar(steamspy_database, verbose=False)

    steam_calendar = simplify_calendar(steam_calendar)

    steam_calendar = remove_current_date(steam_calendar)

    plot_time_series_num_releases(steam_calendar)

    plot_time_series_price(steam_calendar, steamspy_database, 'Median')

    plot_time_series_price(steam_calendar, steamspy_database, 'Average')

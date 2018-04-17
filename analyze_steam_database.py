import datetime
import pathlib

import numpy as np
# Reference: https://stackoverflow.com/a/3054314
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

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

    fig = Figure(dpi=300)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.plot(x, y)
    ax.set_title('Number of games released on Steam each month')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of game releases')

    ax.grid()
    base_plot_filename = 'num_releases'
    fig.savefig(get_full_plot_filename(base_plot_filename), bbox_inches='tight')

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

    fig = Figure(dpi=300)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.plot(x, y)
    ax.set_title(statistic_str + ' price of games released on Steam each month')
    ax.set_xlabel('Date')
    ax.set_ylabel(statistic_str + ' price (in €)')

    ax.grid()
    base_plot_filename = statistic_str.lower() + '_price'
    fig.savefig(get_full_plot_filename(base_plot_filename), bbox_inches='tight')

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


def plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, statistic_str='Median',
                                                      description_keyword='achievements',
                                                      legend_keyword=None):
    if legend_keyword is None:
        legend_keyword = 'number of ' + description_keyword

    x = []
    y = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:
        app_ids = release_calendar[release_date]

        descriptive_variable_of_interest = [int(steam_database[app_id][description_keyword]) for app_id in app_ids
                                            if steam_database[app_id][description_keyword] is not None]
        if len(descriptive_variable_of_interest) == 0:
            continue

        if statistic_str == 'Median':
            value = np.median(descriptive_variable_of_interest)
        else:
            value = np.average(descriptive_variable_of_interest)

        x.append(release_date)
        y.append(value)

    fig = Figure(dpi=300)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.plot(x, y)
    ax.set_title(statistic_str + ' ' + legend_keyword + ' among monthly Steam releases')
    ax.set_xlabel('Date')
    ax.set_ylabel(statistic_str + ' ' + legend_keyword)

    ax.grid()
    base_plot_filename = statistic_str.lower() + '_num_' + description_keyword
    fig.savefig(get_full_plot_filename(base_plot_filename), bbox_inches='tight')

    return


def generic_converter(my_boolean):
    # Objective: output either 0 or 1, with an input which is likely a boolean, but might be a str or an int.

    # Convert boolean to int
    x = int(my_boolean)
    # If my_boolean was a str or an int, then x is now an int, which we binarize.
    x = int(x > 0)
    return x


def plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database,
                                                      description_keyword='controller_support',
                                                      legend_keyword=None):
    if legend_keyword is None:
        sentence_prefixe_for_proportion = 'Proportion of games with '
        legend_keyword = sentence_prefixe_for_proportion + description_keyword

    x = []
    y = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:
        app_ids = release_calendar[release_date]

        descriptive_variable_of_interest = [generic_converter(steam_database[app_id][description_keyword])
                                            for app_id in app_ids
                                            if steam_database[app_id][description_keyword] is not None]
        if len(descriptive_variable_of_interest) == 0:
            continue

        value = np.average(descriptive_variable_of_interest)

        x.append(release_date)
        y.append(value)

    fig = Figure(dpi=300)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.plot(x, y)
    ax.set_title(legend_keyword + ' among monthly Steam releases')
    ax.set_xlabel('Date')
    ax.set_ylabel(legend_keyword)

    ax.grid()
    base_plot_filename = 'proportion_' + description_keyword
    fig.savefig(get_full_plot_filename(base_plot_filename), bbox_inches='tight')

    return


def fill_in_platform_support(steam_database):
    for app_id in steam_database:
        steam_database[app_id]['windows_support'] = steam_database[app_id]['platforms']['windows']
        steam_database[app_id]['mac_support'] = steam_database[app_id]['platforms']['mac']
        steam_database[app_id]['linux_support'] = steam_database[app_id]['platforms']['linux']

    return steam_database


if __name__ == '__main__':
    steamspy_database, categories, genres = load_aggregated_database()

    steamspy_database = fill_in_platform_support(steamspy_database)

    keywords = get_description_keywords(steamspy_database, verbose=True)

    steam_calendar, weird_dates = build_steam_calendar(steamspy_database, verbose=False)

    steam_calendar = simplify_calendar(steam_calendar)

    steam_calendar = remove_current_date(steam_calendar)

    plot_time_series_num_releases(steam_calendar)

    plot_time_series_price(steam_calendar, steamspy_database, 'Median')

    plot_time_series_price(steam_calendar, steamspy_database, 'Average')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Median', 'achievements')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Average', 'achievements')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Average', 'dlc')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Median', 'metacritic',
                                                      'Metacritic score')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Average', 'metacritic',
                                                      'Metacritic score')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Median', 'recommendations')

    plot_time_series_for_numeric_variable_of_interest(steam_calendar, steamspy_database, 'Average', 'recommendations')

    sentence_prefixe = 'Proportion of games with '

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'controller_support',
                                                      sentence_prefixe + 'controller support')

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'demos',
                                                      sentence_prefixe + 'a demo')

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'ext_user_account_notice',
                                                      sentence_prefixe + '3rd-party account')

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'required_age',
                                                      sentence_prefixe + 'age check')

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'windows_support',
                                                      sentence_prefixe + 'Windows support')

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'mac_support',
                                                      sentence_prefixe + 'Mac support')

    plot_time_series_for_boolean_variable_of_interest(steam_calendar, steamspy_database, 'linux_support',
                                                      sentence_prefixe + 'Linux support')

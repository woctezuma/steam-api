import datetime
import pathlib

import matplotlib.dates as mdates
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


def get_x_y_time_series(release_calendar,
                        steam_database=None,
                        description_keyword=None,
                        starting_year=None):
    x_list = []
    y_raw_list = []

    all_release_dates = sorted(list(release_calendar.keys()))

    for release_date in all_release_dates:

        if starting_year is not None and release_date.year < starting_year:
            # Skip release dates prior to the input starting year
            continue

        app_ids = release_calendar[release_date]

        if description_keyword is None:
            selected_app_ids = app_ids
        else:
            selected_app_ids = [app_id for app_id in app_ids if steam_database[app_id][description_keyword] is not None]

        if len(selected_app_ids) == 0:
            continue

        x_list.append(release_date)
        y_raw_list.append(selected_app_ids)

    return (x_list, y_raw_list)


def plot_x_y_time_series(x_list, y_list,
                         chosen_title=None,
                         chosen_ylabel=None,
                         base_plot_filename=None,
                         month_formatting=False,
                         is_variable_of_interest_numeric=True,
                         max_ordinate=None):
    fig = Figure(dpi=300)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.plot(x_list, y_list)
    if chosen_title is not None:
        ax.set_title(chosen_title)
    ax.set_xlabel('Date')
    if chosen_ylabel is not None:
        ax.set_ylabel(chosen_ylabel)

    if month_formatting:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))

    ax.grid()

    if not (is_variable_of_interest_numeric):
        if max_ordinate is None:
            max_ordinate = np.min([1.0, np.max(y_list) * 1.1])
        ax.set_ylim(0, max_ordinate)

    if base_plot_filename is not None:
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


def plot_time_series_for_numeric_variable_of_interest(release_calendar,
                                                      steam_database=None,
                                                      statistic_str=None,
                                                      description_keyword=None,
                                                      legend_keyword=None,
                                                      starting_year=None,
                                                      is_variable_of_interest_numeric=True,
                                                      max_ordinate=None):
    # Get x: dates and y: a set of appIDs of games released for each date in x
    (x, y_raw) = get_x_y_time_series(release_calendar, steamspy_database, description_keyword, starting_year)

    # Compute the value of interest y from y_raw
    y = []
    for app_ids in y_raw:
        if description_keyword is not None:
            if is_variable_of_interest_numeric:
                g = lambda v: int(v)
            else:
                g = lambda v: generic_converter(v)
            features = [g(steam_database[app_id][description_keyword]) for app_id in app_ids]
        else:
            features = app_ids

        if statistic_str == 'Median':
            f = lambda v: np.median(v)
        elif statistic_str == 'Average':
            f = lambda v: np.average(v)
        elif statistic_str == 'Sum':
            f = lambda v: np.sum(v)
        else:
            f = lambda v: len(v)

        value = f(features)

        if description_keyword == 'price_overview':
            # Convert from cents to euros
            value = value / 100

        y.append(value)

    # Plot legend
    if description_keyword is None:
        my_title = 'Number of games released on Steam each month'
        my_ylabel = 'Number of game releases'
        my_plot_filename = 'num_releases'
    elif description_keyword == 'price_overview':
        my_title = statistic_str + ' price of games released on Steam each month'
        my_ylabel = statistic_str + ' price (in €)'
        my_plot_filename = statistic_str.lower() + '_price'
    else:
        if is_variable_of_interest_numeric and (statistic_str == 'Median' or statistic_str == 'Average'):
            statistic_legend = statistic_str + ' '
        else:
            statistic_legend = ''

        if legend_keyword is None:
            if is_variable_of_interest_numeric:
                legend_keyword = 'number of ' + description_keyword
            else:
                sentence_prefixe_for_proportion = 'Proportion of games with '
                legend_keyword = sentence_prefixe_for_proportion + description_keyword

        my_title = statistic_legend + legend_keyword + ' among monthly Steam releases'
        my_ylabel = statistic_legend + legend_keyword
        if is_variable_of_interest_numeric:
            my_plot_filename = 'num_' + description_keyword
            if len(statistic_str) > 0:
                my_plot_filename = statistic_str.lower() + '_' + my_plot_filename
        else:
            my_plot_filename = 'proportion_' + description_keyword

    if starting_year is not None:
        my_plot_filename = my_plot_filename + '_from_' + str(starting_year)

    month_formatting = bool(starting_year is not None)

    # Plot
    plot_x_y_time_series(x, y, my_title, my_ylabel, my_plot_filename, month_formatting, is_variable_of_interest_numeric,
                         max_ordinate)

    return


def generic_converter(my_boolean):
    # Objective: output either 0 or 1, with an input which is likely a boolean, but might be a str or an int.

    # Convert boolean to int
    x = int(my_boolean)
    # If my_boolean was a str or an int, then x is now an int, which we binarize.
    x = int(x > 0)
    return x


def plot_time_series_for_boolean_variable_of_interest(release_calendar,
                                                      steam_database,
                                                      description_keyword='controller_support',
                                                      legend_keyword=None,
                                                      starting_year=None,
                                                      max_ordinate=1.0):
    statistic_str = 'Average'
    is_variable_of_interest_numeric = False

    plot_time_series_for_numeric_variable_of_interest(release_calendar,
                                                      steam_database,
                                                      statistic_str,
                                                      description_keyword,
                                                      legend_keyword,
                                                      starting_year,
                                                      is_variable_of_interest_numeric,
                                                      max_ordinate)

    return


def fill_in_platform_support(steam_database):
    for app_id in steam_database:
        steam_database[app_id]['windows_support'] = steam_database[app_id]['platforms']['windows']
        steam_database[app_id]['mac_support'] = steam_database[app_id]['platforms']['mac']
        steam_database[app_id]['linux_support'] = steam_database[app_id]['platforms']['linux']

    return steam_database


def fill_in_drm_support(steam_database):
    for app_id in steam_database:
        steam_database[app_id]['drm_support'] = bool(steam_database[app_id]['drm_notice'] is not None)

    return steam_database


def plot_every_time_series_based_on_steam_calendar(release_calendar, steam_database):
    plot_time_series_for_numeric_variable_of_interest(release_calendar)  # Plot number of releases

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Median', 'price_overview')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Average', 'price_overview')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Median', 'achievements')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Average', 'achievements')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Average', 'dlc')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Median', 'metacritic',
                                                      'Metacritic score')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Average', 'metacritic',
                                                      'Metacritic score')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Median', 'recommendations')

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Average', 'recommendations')

    sentence_prefixe = 'Proportion of games with '

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'controller_support',
                                                      sentence_prefixe + 'controller support')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'demos',
                                                      sentence_prefixe + 'a demo')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'ext_user_account_notice',
                                                      sentence_prefixe + '3rd-party account')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'required_age',
                                                      sentence_prefixe + 'age check')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'windows_support',
                                                      sentence_prefixe + 'Windows support')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'mac_support',
                                                      sentence_prefixe + 'Mac support')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'linux_support',
                                                      sentence_prefixe + 'Linux support')

    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'drm_support',
                                                      sentence_prefixe + '3rd-party DRM')

    return


def plot_durante_request(release_calendar, steam_database):
    # Reference: https://www.resetera.com/posts/6862653/

    chosen_starting_year = 2016
    chosen_max_ordinate = None

    sentence_prefixe = 'Proportion of games with '

    # noinspection PyTypeChecker
    plot_time_series_for_boolean_variable_of_interest(release_calendar, steam_database, 'drm_support',
                                                      sentence_prefixe + '3rd-party DRM',
                                                      chosen_starting_year,
                                                      chosen_max_ordinate)

    sentence_prefixe = 'Number of games with '

    plot_time_series_for_numeric_variable_of_interest(release_calendar, steam_database, 'Sum', 'drm_support',
                                                      sentence_prefixe + '3rd-party DRM',
                                                      chosen_starting_year)

    return


def get_steam_database(verbosity=True):
    steam_database, categories, genres = load_aggregated_database()

    steam_database = fill_in_platform_support(steam_database)

    steam_database = fill_in_drm_support(steam_database)

    # noinspection PyUnusedLocal
    keywords = get_description_keywords(steam_database, verbose=verbosity)

    return steam_database


def get_steam_calendar(steam_database, verbosity=False):
    release_calendar, weird_dates = build_steam_calendar(steam_database, verbose=verbosity)

    release_calendar = simplify_calendar(release_calendar)

    release_calendar = remove_current_date(release_calendar)

    return release_calendar


if __name__ == '__main__':
    steamspy_database = get_steam_database()

    steam_calendar = get_steam_calendar(steamspy_database)

    plot_every_time_series_based_on_steam_calendar(steam_calendar, steamspy_database)

    plot_durante_request(steam_calendar, steamspy_database)

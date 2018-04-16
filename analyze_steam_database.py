from json_data_utils import load_data
from steam_spy import get_steam_database_filename, get_steam_categories_filename, get_steam_genres_filename

if __name__ == '__main__':
    print('Loading')
    steamspy_database = load_data(get_steam_database_filename())
    categories = load_data(get_steam_categories_filename())
    genres = load_data(get_steam_genres_filename())

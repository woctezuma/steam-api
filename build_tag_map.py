# Objective: create a map of Steam tags
# Reference: https://github.com/woctezuma/steam-tag-mapping/blob/master/map_tags.py

import numpy as np
import umap
# Reference: https://stackoverflow.com/a/3054314
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sklearn.manifold import TSNE

from analyze_steam_database import get_steam_database


def preprocess_data(steam_database, categories_dict, genres_dict):
    categories = list(categories_dict.values())
    genres = list(genres_dict.values())

    tags = categories
    tags.extend(genres)

    num_games = len(steam_database.keys())
    print("#games = %d" % num_games)

    num_tags = len(tags)
    print("#tags = %d" % num_tags)

    # Create a list of tags sorted in lexicographical order
    tags_list = list(tags)
    tags_list.sort()

    tag_joint_game_matrix = np.zeros([num_tags, num_games])

    game_counter = 0

    for appid in steam_database:
        categories = [categories_dict[str(i)] for i in steam_database[appid]['categories']
                      if str(i) in categories_dict]
        genres = [genres_dict[str(i)] for i in steam_database[appid]['genres']
                  if str(i) in genres_dict]

        current_tags = categories
        current_tags.extend(genres)

        for tag in current_tags:
            i = tags_list.index(tag)
            j = game_counter
            tag_joint_game_matrix[i][j] += 1

        game_counter += 1

    return tag_joint_game_matrix, tags_list


# Scale and visualize the embedding vectors
# noinspection PyPep8Naming
def plot_embedding(X, str_list, base_plot_filename=None, title=None, highlighted_tags=list(), delta_font=0.003):
    # Code copied from: plot_embedding() in https://github.com/woctezuma/steam-tag-mapping/blob/master/map_tags.py
    x_min, x_max = np.min(X, 0), np.max(X, 0)
    # noinspection PyPep8Naming
    X = (X - x_min) / (x_max - x_min)

    fig = Figure(dpi=600)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.scatter(X[:, 0], X[:, 1])
    ax.axis('off')

    # Add a label to each node. The challenge here is that we want to
    # position the labels to avoid overlap with other labels
    # References:
    # * https://stackoverflow.com/a/40729950/
    # * http://scikit-learn.org/stable/auto_examples/applications/plot_stock_market.html
    for index, (label, x, y) in enumerate(
            zip(str_list, X[:, 0], X[:, 1])):

        dx = x - X[:, 0]
        dx[index] = 1
        dy = y - X[:, 1]
        dy[index] = 1
        this_dx = dx[np.argmin(np.abs(dy))]
        this_dy = dy[np.argmin(np.abs(dx))]
        if this_dx > 0:
            horizontalalignment = 'left'
            x = x + delta_font
        else:
            horizontalalignment = 'right'
            x = x - delta_font
        if this_dy > 0:
            verticalalignment = 'bottom'
            y = y + delta_font
        else:
            verticalalignment = 'top'
            y = y - delta_font

        if label in highlighted_tags:
            my_color = "red"
        else:
            my_color = "black"

        my_font_size = "xx-small"
        my_weight = 'normal'
        my_stretch = "condensed"

        ax.text(x, y, label, color=my_color,
                horizontalalignment=horizontalalignment,
                verticalalignment=verticalalignment,
                fontdict={'family': 'serif', 'weight': my_weight, 'size': my_font_size, 'stretch': my_stretch})

    ax.set_xticks([]), ax.set_yticks([])
    if title is not None:
        ax.set_title(title)

    if base_plot_filename is not None:
        fig.savefig(base_plot_filename, bbox_inches='tight')

    return


def display_tag_map(embedding, tags_list, base_plot_filename=None, my_title=None,
                    highlighted_tags=list()):
    if len(highlighted_tags) == 0:
        highlighted_tags = ['Early Access', 'Free to Play', 'In-App Purchases', 'Steam Trading Cards',
                            'Violent', 'Gore']

    plot_embedding(embedding, tags_list, base_plot_filename, my_title, highlighted_tags)

    return


def compute_tag_map(tag_joint_game_matrix, embedding_name='t-SNE'):
    if embedding_name == 't-SNE':
        embedding = TSNE(n_components=2, random_state=0, verbose=2, init='pca', metric='correlation')
    else:
        embedding = umap.UMAP(n_neighbors=20, min_dist=0.15, metric='correlation', verbose=True)

    embedded_data = embedding.fit_transform(tag_joint_game_matrix)

    return embedded_data


def main():
    steamspy_database, all_categories_dict, all_genres_dict = get_steam_database(verbosity=False)

    joint_matrix, tags_list_sorted = preprocess_data(steamspy_database, all_categories_dict, all_genres_dict)

    method_name = 't-SNE'  # Either 't-SNE' or 'u-MAP'
    tag_embedding = compute_tag_map(joint_matrix, embedding_name=method_name)

    plot_filename = 'tag_map.png'
    plot_title = '{} plot of categories (in black) and genres (in red)'.format(method_name)
    red_tags = list(all_genres_dict.values())

    display_tag_map(tag_embedding, tags_list_sorted, plot_filename, plot_title, red_tags)

    return True


if __name__ == '__main__':
    main()

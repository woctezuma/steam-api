# Steam API

[![Build status][Build image]][Build]
[![Updates][Dependency image]][PyUp]
[![Python 3][Python3 image]][PyUp]
[![Code coverage][Codecov image]][Codecov]

  [Build]: https://travis-ci.org/woctezuma/steam-api
  [Build image]: https://travis-ci.org/woctezuma/steam-api.svg?branch=master

  [PyUp]: https://pyup.io/repos/github/woctezuma/steam-api/
  [Dependency image]: https://pyup.io/repos/github/woctezuma/steam-api/shield.svg
  [Python3 image]: https://pyup.io/repos/github/woctezuma/steam-api/python-3-shield.svg

  [Codecov]: https://codecov.io/gh/woctezuma/steam-api
  [Codecov image]: https://codecov.io/gh/woctezuma/steam-api/branch/master/graph/badge.svg

This repository contains Python code to download data through Steam API.

## Data

Data is available as a snapshot in [another repository](https://github.com/woctezuma/steam-api-data).

## Usage

-   To download an exhaustive list of Steam app ids, along with their app names, run:
```bash
python steam_catalog_utils.py
```

-   To download app details of Steam games, run:
```bash
python steam_spy.py
```

-   To aggregate all the data contained in app details, run:
```bash
python aggregate_steam_spy.py
```

-   To specifically aggregate store descriptions, contained in app details, run:
```bash
python aggregate_game_text_descriptions.py
```

- To plot data for each store attribute, categorie, and genre, run:

```bash
python analyze_steam_database.py
```

- To visualize categories and genres, with a 2D embedding (t-SNE ([author's FAQ][tsne-author], [wikipedia][tsne-wiki]) or [UMAP][umap-code]), run:

```bash
python build_tag_map.py
```

## Results

### Store attributes

Outputs for each Steam store attribute can be found in [`plots/`](https://github.com/woctezuma/steam-api/wiki/Store-attributes).

Confidence intervals can be found in [`plots_with_confidence_interval/`](https://github.com/woctezuma/steam-api/wiki/Store-attributes-with-interval).

### Categories and genres

Outputs for each categorie and genre can be found in [`plots_categories_and_genres/`](https://github.com/woctezuma/steam-api/wiki/Categories).

Confidence intervals can be found in [`plots_categories_and_genres_with_confidence_interval/`](https://github.com/woctezuma/steam-api/wiki/Categories-with-interval).

### Visualization of categories and genres

![t-SNE plot of Steam categories and genres](https://raw.githubusercontent.com/wiki/woctezuma/steam-api/tag_map.png)

## Addendum

If you like these stats, [check out my other repository](https://github.com/woctezuma/humble-monthly) with a focus on Humble Monthly bundles.

[tsne-author]: <https://lvdmaaten.github.io/tsne/>
[tsne-wiki]: <https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding>
[umap-code]: <https://github.com/lmcinnes/umap>

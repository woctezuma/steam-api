import unittest

import analyze_steam_database
import build_tag_map
import steam_catalog_utils


class TestSteamCatalogUtilsMethods(unittest.TestCase):
    def test_main(self):
        assert steam_catalog_utils.main()


class TestAnalyzeSteamDatabaseMethods(unittest.TestCase):
    def test_main(self):
        assert analyze_steam_database.main()


class TestBuildTagMapMethods(unittest.TestCase):
    def test_main(self):
        assert build_tag_map.main()


if __name__ == '__main__':
    unittest.main()

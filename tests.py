import unittest

import analyze_steam_database
import build_tag_map
import steam_catalog_utils


class TestSteamCatalogUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(steam_catalog_utils.main())


class TestAnalyzeSteamDatabaseMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(analyze_steam_database.main())


class TestBuildTagMapMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(build_tag_map.main())


if __name__ == '__main__':
    unittest.main()

import unittest

import analyze_steam_database
import app_details_utils
import build_tag_map
import json_data_utils
import steam_catalog_utils


class TestJsonDataUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(json_data_utils.main())


class TestSteamCatalogUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(steam_catalog_utils.main())


class TestAppDetailsUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(app_details_utils.main())


class TestAnalyzeSteamDatabaseMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(analyze_steam_database.main())


class TestBuildTagMapMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(build_tag_map.main())


if __name__ == '__main__':
    unittest.main()

""" sensors test """

import unittest
import json
import os

from pstryk_api.entity import PstrykPricingDataUpdateCoordinator

DIR = os.path.dirname(__file__)

class SensorsTest(unittest.TestCase):
    """  """
    def test_parse_data(self):
        with open(DIR + "/1-input.json", "r") as f:
            input = json.load(f)
        with open(DIR + "/1-expected.json", "r") as f:
            expected = json.load(f)

        output = PstrykPricingDataUpdateCoordinator.parse_data(input)

        with open(DIR + "/1-dump.json", "w") as f:
            json.dump(output, f)

        output = json.loads(json.dumps(output))

        self.maxDiff = None
        self.assertEqual(output, expected)

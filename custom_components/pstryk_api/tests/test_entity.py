""" sensors test """

import unittest
import json
import os
from datetime import datetime
import dateutil.tz

from pstryk_api.entity import PstrykPricingDataUpdateCoordinator

DIR = os.path.dirname(__file__)

class SensorsTest(unittest.TestCase):
    """ Sensors Test """

    def test_parse_data(self):
        """ Test parse_data() """
        with open(DIR + "/1-input.json", "r", encoding="utf-8") as f:
            inp = json.load(f)
        with open(DIR + "/1-expected.json", "r", encoding="utf-8") as f:
            expected = json.load(f)

        now = datetime(year=2025, month=6, day=16, hour=10, minute=11, second=12, tzinfo=dateutil.tz.tzlocal())
        output = PstrykPricingDataUpdateCoordinator.parse_data(inp, now)

        with open(DIR + "/1-dump.json", "w", encoding="utf-8") as f:
            json.dump(output, f)

        output = json.loads(json.dumps(output))

        self.maxDiff = None
        self.assertEqual(output, expected)

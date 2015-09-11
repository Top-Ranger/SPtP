# Copyright (C)2014,2015 Philipp Naumann
# Copyright (C)2014,2015 Marcus Soll
#
# This file is part of SPtP.
#
# SPtP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPtP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SPtP. If not, see <http://www.gnu.org/licenses/>.

import unittest
import comparator

class TestComparator(unittest.TestCase):
    def setUp(self):
        self.comparator = comparator.Comparator('./tests/comparator/input/', './tests/comparator/output/', 0.7, True)

    def test_comparison(self):
        try:
            self.comparator.run()
        except comparator.ComparatorError:
            self.fail('Test failed with ComparatorError')
        except:
            self.fail('Test failed with unknown exception')
        self.assertEqual(set(self.comparator.passed.keys()), {'correct1', 'correct2'})
        self.assertEqual(set(self.comparator.failed.keys()), {'incorrect1', 'incorrect2'})
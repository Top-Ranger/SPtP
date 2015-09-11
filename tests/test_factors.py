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

from factors import *


class TestFactors(unittest.TestCase):
    def setUp(self):
        self.factors = Factors()

    def test_constructor(self):
        self.assertEqual(len(self.factors.factors), 0)

    def test_load(self):
        self.factors.load_file('tests/factors.txt')
        self.assertEqual(len(self.factors.factors), 3)
        self.assertEqual(self.factors.factors['One'], 1.0)
        self.assertEqual(self.factors.factors['Two'], 2.0)
        self.assertEqual(self.factors.factors['Half'], 0.5)

    def test_get_factor(self):
        self.factors.load_file('tests/factors.txt')
        self.assertEqual(self.factors.get_factor('One'), 1.0)
        self.assertEqual(self.factors.get_factor('Two'), 2.0)
        self.assertEqual(self.factors.get_factor('Half'), 0.5)
        self.assertEqual(self.factors.get_factor('Certainly not existing key'), 1.0)


if __name__ == '__main__':
    unittest.main()

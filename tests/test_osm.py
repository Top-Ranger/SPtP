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
import xml.etree.ElementTree

from osm import *


class TestOSM(unittest.TestCase):
    def setUp(self):
        self.osm = OSM(xml.etree.ElementTree.parse('tests/0001.osm').getroot())

    def test_nodes(self):
        self.assertEqual(len(self.osm.nodes), 3)
        self.assertEqual(self.osm.nodes['186271859'].point.x, 5.3376846)
        self.assertEqual(self.osm.nodes['186271859'].point.y, 50.9306591)

        self.assertEqual(self.osm.nodes['186271860'].point.x, 5.3377928, 'Position of lon and lat switched')
        self.assertEqual(self.osm.nodes['186271860'].point.y, 50.9312018, 'Position of lon and lat switched')

        self.assertEqual(self.osm.nodes['186271861'].point.x, 5.3380414, 'Position of id switched')
        self.assertEqual(self.osm.nodes['186271861'].point.y, 50.9319672, 'Position of id switched')

    def test_ways(self):
        self.assertEqual(len(self.osm.ways), 1)
        self.assertEqual(self.osm.ways['18003119'].name, '18003119')
        self.assertEqual(self.osm.ways['18003119'].tags, {'source': 'osm', 'test': 'test', 'cake': 'lie'})
        self.assertEqual(list(self.osm.ways['18003119'].polygon.exterior.coords), [(5.3376846, 50.9306591), (5.3377928, 50.9312018), (5.3380414, 50.9319672), (5.3376846, 50.9306591)])

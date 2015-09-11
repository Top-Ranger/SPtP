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

from kml import *
from geometry import *


class TestKML(unittest.TestCase):
    def setUp(self):
        self.kml = KML(xml.etree.ElementTree.parse('tests/0001.kml').getroot())

    def test_points(self):
        self.assertEqual(len(self.kml.nodes), 1)
        self.assertEqual(self.kml.nodes['0002'].name, '0002')
        self.assertEqual(self.kml.nodes['0002'].point.x, 7.00000000)
        self.assertEqual(self.kml.nodes['0002'].point.y, 7.00000000)

    def test_polygon(self):
        self.assertEqual(len(self.kml.ways), 1)
        self.assertEqual(self.kml.ways['0001'].name, '0001')
        self.assertEqual(list(self.kml.ways['0001'].polygon.exterior.coords), [(1.00000000, 1.00000000), (2.00000000, 1.00000000), (1.00000000, 2.00000000), (1.00000000, 1.00000000)])


class TestKMLBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = KMLBuilder()

    def test_constructor(self):
        self.assertEqual(self.builder._placemarks, [])

    def test_run(self):
        node = Node('0002', {'tests': 'tests', 'cake': 'lie'}, shapely.geometry.Point(2.1, 1.2))
        way = Way('0001', {'tests': 'tests', 'cake': 'lie'}, shapely.geometry.Polygon([(1, 1), (2, 2), (1, 2)]))

        self.builder.add_placemark(node)
        self.builder.add_placemark(way)

        built = self.builder.run()
        tree = xml.etree.ElementTree.fromstring(built)
        kml = KML(tree)

        self.assertEqual(len(kml.nodes), 1)
        self.assertEqual(kml.nodes['0002'].name, '0002')
        self.assertEqual(kml.nodes['0002'].point.x, 2.10000000)
        self.assertEqual(kml.nodes['0002'].point.y, 1.20000000)

        self.assertEqual(len(kml.ways), 1)
        self.assertEqual(kml.ways['0001'].name, '0001')
        self.assertEqual(list(kml.ways['0001'].polygon.exterior.coords), [(1.00000000, 1.00000000), (2.00000000, 2.00000000), (1.00000000, 2.00000000), (1.00000000, 1.00000000)])


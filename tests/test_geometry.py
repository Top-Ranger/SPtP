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

import shapely

from geometry import *


class TestNode(unittest.TestCase):
    def setUp(self):
        self.node = Node('2', {'test': 'test', 'cake': 'lie'}, shapely.geometry.Point(2.1, 1.2))

    def test_constructor(self):
        self.assertEqual(self.node.name, '2')
        self.assertEqual(self.node.tags, {'test': 'test', 'cake': 'lie'})
        self.assertEqual(self.node.point.xy, shapely.geometry.Point(2.1, 1.2).xy)

    def test_json_serializable(self):
        json = self.node.json_serializable()
        self.assertEqual(json['name'], '2')
        self.assertEqual(json['tags'], {'test': 'test', 'cake': 'lie'})
        self.assertEqual(json['point'], [1.2, 2.1])


class TestWay(unittest.TestCase):
    def setUp(self):
        self.way = Way('3', {'test': 'test', 'cake': 'lie'}, shapely.geometry.Polygon([(1, 1), (2, 2), (1, 2)]))

    def test_constructor(self):
        self.assertEqual(self.way.name, '3')
        self.assertEqual(self.way.tags, {'test': 'test', 'cake': 'lie'})
        self.assertEqual(list(self.way.polygon.exterior.coords), [(1., 1.), (2., 2.), (1., 2.), (1., 1.)])

    def test_json_serializable(self):
        json = self.way.json_serializable()
        self.assertEqual(json['name'], '3')
        self.assertEqual(json['tags'], {'test': 'test', 'cake': 'lie'})
        self.assertEqual(json['polygon'], [[1., 1.], [2., 2.], [2., 1.], [1., 1.]])
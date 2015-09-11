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

from classifier import *
from location import *
from osm import *


class TestClassifier(unittest.TestCase):
    def setUp(self):
        self.location = Location('2', shapely.geometry.Point(1.0, 1.0))
        self.location.add_image('tests/0002.jpg')
        osm = OSM(xml.etree.ElementTree.parse('tests/0002.osm').getroot())
        self.location.add_osm(osm)
        self.classifiers = get_classifiers_list(location=self.location)

    def test_instance(self):
        for classifier in self.classifiers:
            self.assertIsInstance(classifier, Classifier)

    def test_name(self):
        for classifier in self.classifiers:
            self.assertIsNotNone(classifier.name())

    def test_unique_name(self):
        set_classifier = set()
        for classifier in self.classifiers:
            set_classifier.add(classifier.name())
        self.assertEqual(len(set_classifier), len(self.classifiers), 'Failure: Some classifier have the same name')

    def test_classify(self):
        for classifier in self.classifiers:
            points = classifier.classify()
            for key in points:
                self.assertTrue(points[key] <= 100, 'Failure in %s: Points (%i) exceed 100' % (classifier.name(), points[key]))
                self.assertTrue(points[key] >= -100, 'Failure in %s: Points (%i) less than -100' % (classifier.name(), points[key]))
                self.assertIn(key, ['osm_100', 'osm_200', 'osm_300'], 'Failure in %s: Unknown key %s' % (classifier.name(), key))
            self.assertEqual(len(points), 3, 'Failure in %s: Wrong number of entries' % classifier.name())

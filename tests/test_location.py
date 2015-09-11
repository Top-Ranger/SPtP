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

import shapely.geometry
import PIL.Image
import PIL.ExifTags

from location import *


class TestLocation(unittest.TestCase):
    def setUp(self):
        self.location = Location('1', shapely.geometry.Point(2.1, 1.2))

    def test_constructor(self):
        self.assertEqual(self.location.name, '1')
        self.assertEqual(self.location.point.xy, shapely.geometry.Point(2.1, 1.2).xy)
        self.assertEqual(self.location.surs, {})
        self.assertEqual(self.location.image, None)
        self.assertEqual(self.location.exif_tags, None)
        self.assertEqual(self.location.osm, None)

    def test_add_image(self):
        self.location.add_image('tests/0001.jpg', scale_down=False)
        self.assertEqual(self.location.image, PIL.Image.open('tests/0001.jpg'))
        self.assertEqual(self.location.exif_tags, {'whitebalance': 0, 'datetimeoriginal': '2014:10:27 08:42:56', 'flashpixversion': b'0100', 'meteringmode': 1, 'focallength': (4, 1), 'flash': 0, 'model': 'Jolla', 'exifoffset': 146, 'exifversion': b'0230', 'make': 'Jolla', 'fnumber': (12, 5), 'orientation': 1, 'isospeedratings': 100, 'xresolution': (72, 1), 'aperturevalue': (334328577, 132351334), 'exposuretime': (139, 100000), 'yresolution': (72, 1), 'datetime': '2014:10:27 08:42:56', 'none': 100})


class TestFileParser(unittest.TestCase):
    def setUp(self):
        self.parser = LocationsFileParser('tests/surs.txt')

    def test_constructor(self):
        self.assertEqual(len(self.parser.locations), 1, 'Too many locations found!')
        location = self.parser.locations['1']
        self.assertEqual(location.name, '1')
        self.assertEqual(location.point.xy, shapely.geometry.Point(2.1, 1.2).xy)
        self.assertEqual(len(location.surs), 2)
        self.assertEqual(location.surs['smoking'], 'no')
        self.assertEqual(location.surs['swimming'], 'yes')
        self.assertEqual(location.image, None)
        self.assertEqual(location.exif_tags, None)
        self.assertEqual(location.osm, None)

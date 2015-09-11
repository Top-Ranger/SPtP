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

import PIL.Image

from image_processor import *


class TestImageProcessor(unittest.TestCase):
    def test_constructor(self):
        with self.assertRaises(ValueError):
            ImageProcessor('This is not an instance of PIL.Image.Image')

    def test_outside(self):
        self.assertTrue(ImageProcessor(PIL.Image.open('tests/0003.jpg')).outside())
        self.assertTrue(ImageProcessor(PIL.Image.open('tests/0004.jpg')).outside())
        self.assertFalse(ImageProcessor(PIL.Image.open('tests/0005.jpg')).outside())
        self.assertFalse(ImageProcessor(PIL.Image.open('tests/0006.jpg')).outside())

    def test_aggregate_histogram(self):
        image_processor = ImageProcessor(PIL.Image.open('tests/0003.jpg'))
        self.assertEqual((1.0, 1.0, 1.0), image_processor.aggregate_histogram((0, 0, 0)))
        self.assertEqual((0.0, 0.0, 0.0), image_processor.aggregate_histogram((256, 256, 256)))
        with self.assertRaises(ValueError):
            ImageProcessor(PIL.Image.open('tests/0007.jpg')).outside()
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

import PIL.Image


class ImageProcessor:
    def __init__(self, image):
        """
        This class implements simple image processing methods.

        :param image: The image to process
        :type image: PIL.Image, currently only RGB(A).
        :raise: ValueError: if the image is not an instance of PIL.Image.Image
        :return: None
        """
        if image is None:
            self.image = None
            return

        if not isinstance(image, PIL.Image.Image):
            raise ValueError('Not a PIL.Image.Image')
        self.image = image
        self.top, self.bottom = self._split_image()

    def _split_image(self):
        """
        Splits the image vertically in half:

        :return: top, bottom as PIL.Image.Image tuple
        :rtype: (PIL.Image.Image, PIL.Image.Image)
        """
        if self.image is None:
            return None, None

        w, h = self.image.size
        top = self.image.crop((0, 0, w, h // 2))
        bottom = self.image.crop((0, h // 2, w, h))
        return top, bottom

    def aggregate_histogram(self, minimum_values=(200, 200, 200)):
        """
        Computes the quotients of
          sum(count(pixels with color rgb(r, ?, ?))) for r >= minimum_values[0],
          sum(count(pixels with color rgb(?, g, ?))) for g >= minimum_values[1],
          sum(count(pixels with color rgb(?, ?, b))) for b >= minimum_values[2]
        and the total number of pixels (i. e. "how red/green/blue an image is") using the image's histogram.

        :param minimum_values: (minimum red value, minimum green value, minimum blue value). Default: (200, 200, 200), empirically chosen
        :type minimum_values: (int,int,int)
        :raise ValueError: if the image is not RGB(A)
        :return: Red, green and blue ratios as tuple
        :rtype: (float,float,float)
        """
        if self.image is None:
            return None, None, None

        if not self.image.mode in ('RGB', 'RGBA'):
            raise ValueError('RGB(A) only')

        histogram = self.image.histogram()
        assert len(histogram) == 3 * 256 or len(histogram) == 4 * 256
        w, h = self.image.size
        p = w * h
        r = histogram[0:256]
        g = histogram[256:256 * 2]
        b = histogram[256 * 2:256 * 3]
        return sum(r[minimum_values[0]:]) / p, sum(g[minimum_values[1]:]) / p, sum(b[minimum_values[2]:]) / p

    def outside(self):
        """
        Simplistically classifies the image as "outside" if its top half is "mostly blue" and/or its bottom half is "mostly green"!

        :return: True if "outside", False if not "outside" or image is None
        :rtype: bool
        """
        if self.image is None:
            return False

        outside = False

        # Is top half "mostly blue"?
        top_processor = ImageProcessor(self.top)
        r, g, b = top_processor.aggregate_histogram()
        if b > r and b > g:
            outside = True

        # Is bottom half "mostly green"?
        bottom_processor = ImageProcessor(self.bottom)
        r, g, b = bottom_processor.aggregate_histogram()
        if g > r and g > b:
            outside = True

        return outside
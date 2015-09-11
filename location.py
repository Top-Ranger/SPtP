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

import re

import PIL.Image
import PIL.ExifTags
import shapely.geometry
import json


class Location:
    def __init__(self, name, point):
        """
        This class represents a location with SURs.

        :param name: Name of location
        :type name: string
        :param point: Position of location
        :type point: shapely.geometry.Point
        :return: None
        """
        self.name = name
        self.point = point
        self.surs = {}
        self.ways = {}
        self.nodes = {}
        self.osm = None
        self.generated = None
        self.image = None
        self.gps_info = {}
        self.exif_tags = None

    def json_serializable(self):
        """
        Generates a JSON serializable representation of self. self.osm, self.image,
        self.gps_info and self.exif_tags are omitted!

        :return: JSON serializable representation of self
        :rtype: dict
        """
        return {
            'name': self.name,
            'point': [self.point.y, self.point.x],
            'surs': self.surs,
            'nodes': {name: node.json_serializable() for (name, node) in self.nodes.items()},
            'ways': {name: way.json_serializable() for (name, way) in self.ways.items()},
        }

    def add_nodes(self, prefix, nodes):
        """
        Updates self.nodes with given nodes prefixing the key.

        :param prefix: Key prefix
        :param nodes: Nodes to be added
        :type nodes: dict {string, geometry.Node}
        :return: None
        """
        new_nodes = {prefix + k: v for (k, v) in nodes.items()}
        self.nodes.update(new_nodes)

    def add_ways(self, prefix, ways):
        """
        Updates self.ways with given ways prefixing the key.

        :param prefix: Key prefix
        :param ways: Ways to be added
        :type ways: dict {string, geometry.Way}
        :return: None
        """
        new_ways = {prefix + k: v for (k, v) in ways.items()}
        self.ways.update(new_ways)

    def add_osm(self, osm):
        """
        Sets self.osm and updates self.nodes and self.ways with key prefix 'osm_'.

        :param osm: instance of osm.OSM
        :return: None
        """
        self.osm = osm
        self.add_nodes('osm_', osm.nodes)
        self.add_ways('osm_', osm.ways)

    def add_generated(self, generated):
        """
        Sets self.generated and updates self.nodes and self.ways with key prefix 'gen_'.

        :param generated: instance of generated.Generated
        :return: None
        """
        self.generated = generated
        self.add_nodes('gen_', generated.nodes)
        self.add_ways('gen_', generated.ways)

    def add_image(self, image_file_path, scale_down=True):
        """
        Adds an image to the location.
        
        :param image_file_path: Path to the image
        :raise: OSError if the image cannot be opened with PIL.Image.open()
        :type image_file_path: String
        :param scale_down: Whether to scale the image down to 512px. (Default: True)
        :return: None
        """
        image = PIL.Image.open(image_file_path)

        self.exif_tags = {}
        exif = image._getexif()
        if exif is None:
            exif = {}
        for (key, value) in exif.items():
            self.exif_tags[str(PIL.ExifTags.TAGS.get(key)).lower()] = value
        if 'gpsinfo' in self.exif_tags:
            gpsinfo = self.exif_tags['gpsinfo']
            # Direction
            if 17 in gpsinfo:
                self.gps_info['direction'] = gpsinfo[17][0] / gpsinfo[17][1]

        if scale_down:
            w, h = image.size
            ratio = min(512 / w, 512 / h)
            image = image.resize((int(w * ratio), int(h * ratio)), PIL.Image.NEAREST)

        if 'orientation' in self.exif_tags.keys():
            self.image = correct_orientation(image, self.exif_tags['orientation'])
        else:
            self.image = image

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, ', '.join(['%s = %s' % (str(k), str(v)) for (k, v) in self.__dict__.items()]))


class LocationsFileParser:
    def __init__(self, data_file_path):
        """
        This class parses a locations file. A location has a name, GPS coordinates and any number
        of space usage rules (SURs). A line is expected to match the following format:
        [location uid (string)], [latitude (float)], [longitude (float)], [SUR key (string)] = [SUR "value" (string)]
        There might be additional spaces separating the values.

        Line starting with a number sign (#) will be ignored. The same is true for lines not matching
        the given format - such as the line containing the number of space usage rules which should
        be the first line of the file according to file format specification.

        The constructor parses the data file. Results are saved as locations in self.locations.

        :param data_file_path: Location of the data file
        :return: None
        """
        self.locations = {}

        with open(data_file_path) as data_file:
            for line in iter(data_file):
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = [part.strip() for part in line.split(',')]
                if not len(parts) == 4:
                    continue
                pattern = re.compile('([^=]*)=["]*([^"]*)["]*')
                match = pattern.match(parts[3])
                uid = parts[0]
                try:
                    point = shapely.geometry.Point(float(parts[2]), float(parts[1]))
                except ValueError:
                    continue
                if match is None:
                    continue
                sur_key = match.group(1)
                sur_value = match.group(2)
                if not sur_key or len(sur_key) == 0 or not sur_value or len(sur_value) == 0:
                    continue
                if not uid in self.locations:
                    self.locations[uid] = Location(uid, point)
                self.locations[uid].surs[sur_key] = sur_value


def correct_orientation(image, orientation):
    """
    Transforms an PIL image into the right position on the given orientation.
    :raise ValueError: if the image is not an instance of PIL.Image.Image
    :param image: Image to transform
    :type image: PIL.Image
    :param orientation: EXIF orientation
    :type orientation: int
    :return: Image with correct orientation
    :rtype: PIL.Image
    """

    if image is None:
        return None

    if not isinstance(image, PIL.Image.Image):
        raise ValueError('Not a PIL.Image.Image')

    # Rotation
    if orientation in {7, 8}:
        image = image.transpose(PIL.Image.ROTATE_90)
    elif orientation in {3, 4}:
        image = image.transpose(PIL.Image.ROTATE_180)
    elif orientation in {5, 6}:
        image = image.transpose(PIL.Image.ROTATE_270)

    # Flipping
    if orientation in {2, 4, 5, 7}:
        image = image.transpose(PIL.Image.FLIP_LEFT_RIGHT)

    # Return image
    return image
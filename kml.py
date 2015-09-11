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

import shapely.geometry

from osm import *
from geometry import *


class KML:
    def __init__(self, root):
        """
        This class represents a KML data structure.

        :return: None
        """
        self.nodes = {}
        self.ways = {}

        ns = root.tag.replace('}kml', '}')

        def node_text(node, default):
            """
            Returns a node's text if it is not None and node.text is not
            None, default otherwise.

            :param node: Node
            :type node: xml.etree.ElementTree.Element
            :return: Node text if set, default otherwise
            :rtype: string
            """
            return default if node is None else node.text if node.text else default

        def text_to_float_pairs(text):
            """
            Translates coordinates from KML format to float tuple.

            :param text: Coordinate string to split
            :type text: string
            :return: List of float tuples
            :rtype: [(float,float),...]
            """
            c_text_pairs = [c.split(',') for c in text.split(' ') if len(c) > 0]
            return [(float(c[0]), float(c[1])) for c in c_text_pairs]

        for placemark in root.iter(ns + 'Placemark'):
            name = node_text(placemark.find(ns + 'name'), '?')
            description = node_text(placemark.find(ns + 'description'), '?')

            node = placemark.find(ns + 'Polygon')
            if node is not None:
                coordinates_node = node.find('.//' + ns + 'coordinates')
                c_float_pairs_text = coordinates_node.text.strip().replace('\n', ' ')
                c_float_pairs = text_to_float_pairs(c_float_pairs_text)

                # Polygon type is expected to be "LinearRing"
                if len(c_float_pairs) < 3:
                    continue
                polygon = shapely.geometry.Polygon(c_float_pairs)

                tags = {'description': description}

                self.ways[name] = Way(name, tags, polygon)

            node = placemark.find(ns + 'Point')
            if node is not None:
                c_float_pairs = text_to_float_pairs(node.find('.//' + ns + 'coordinates').text)
                assert len(c_float_pairs) == 1
                point = shapely.geometry.Point(c_float_pairs[0])

                tags = {'description': description}

                self.nodes[name] = Node(name, tags, point)

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, ', '.join(['%s = %s' % (str(k), str(v)) for (k, v) in self.__dict__.items()]))


class KMLBuilder:
    def __init__(self):
        """
        This class builds a string containing the contents of a KML file.
        All placemarks which should be saved in the KML file must be added using add_placemark().

        :return: None
        """
        self._placemarks = []

    def add_placemark(self, item):
        """
        Adds a placemark to the builder.

        :param item: an instance of geometry.Node or geometry.Way
        :type item: node or way to be added
        :raise ValueError: if item is not an instance of geometry.Node or geometry.Way
        :return: None
        """
        if not isinstance(item, Node) and not isinstance(item, Way):
            raise ValueError()

        self._placemarks.append(item)

    def run(self):
        """
        Builds a KML string from objects stored in "_placemarks".
        
        :return: KML String
        :rtype: string
        """
        styles = '<Style id="poly1">\n<LineStyle>\n<width>1.5</width>\n</LineStyle>\n<PolyStyle>\n<color>7dff0000</color>\n</PolyStyle>\n</Style>\n'
        header = '%s' % styles
        kml = '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n%s' % header
        kml += '<!--\nContains information from http://www.openstreetmap.org/, which is made available\nhere under the Open Database License (ODbL) [http://opendatacommons.org/licenses/odbl/1.0/].\n-->\n'
        for item in self._placemarks:
            node_kml = None
            description = item.tags['description'] if 'description' in item.tags else ""

            # KML point
            if isinstance(item, Node):
                extended_data = '\n'
                node_kml = '<Placemark>\n<name>%s</name>\n<description>%s</description>\n' % (item.name, description)
                node_kml += '<Point>\n<coordinates>\n%f,%f\n</coordinates>\n</Point>\n' % (item.point.x, item.point.y)
                node_kml += '<ExtendedData>%s</ExtendedData>\n</Placemark>\n' % extended_data
            # KML polygon
            if isinstance(item, Way):
                coordinates = '\n'.join('%f,%f' % (p[0], p[1]) for p in item.polygon.exterior.coords)
                style_url = '#poly1'
                extended_tags = '<altitudeMode>clampToGround</altitudeMode>\n<extrude>1</extrude>\n<tessellate>1</tessellate>'
                extended_data = '\n'
                node_kml = '<Placemark>\n<name>%s</name>\n<styleUrl>%s</styleUrl>\n%s\n<description>%s</description>\n' % (item.name, style_url, extended_tags, description)
                node_kml += '<Polygon>\n<outerBoundaryIs>\n<%s>\n<coordinates>\n%s\n</coordinates>\n</%s>\n</outerBoundaryIs>\n</Polygon>\n' % ('LinearRing', coordinates, 'LinearRing')
                node_kml += '<ExtendedData>%s</ExtendedData>\n</Placemark>\n' % extended_data
            assert node_kml is not None
            kml += node_kml
        kml += '</Document>\n</kml>'
        return kml

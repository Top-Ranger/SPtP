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

from geometry import *


class OSM:
    def __init__(self, root):
        """
        This class represents an "Open Street Map" (OSM) data structure.
        The constructor extracts the contents of the OSM file stored in "root".
        The results are saved in the attributes "nodes" and "way".

        :param root: Root element of the OSM file received by xml.etree.ElementTree.parse().getroot()
        :type root: xml.etree.ElementTree.Element
        :return: None
        """

        self.nodes = {}
        self.ways = {}

        for node in root.findall('node'):
            uid = node.attrib['id']
            tags = {'source': 'osm'}
            for tag in node.findall('tag'):
                tags[tag.attrib['k']] = tag.attrib['v']
            self.nodes[uid] = Node(uid, tags, shapely.geometry.Point(float(node.attrib['lon']), float(node.attrib['lat'])))

        for way in root.findall('way'):
            uid = way.attrib['id']
            tags = {'source': 'osm'}
            for tag in way.findall('tag'):
                tags[tag.attrib['k']] = tag.attrib['v']
            points = []
            for nd in way.findall('nd'):
                point = self.nodes[nd.attrib['ref']].point
                points += [(point.x, point.y)]
            if len(points) < 3:
                continue
            polygon = shapely.geometry.Polygon(points)
            tags['source'] = 'osm'
            way = Way(uid, tags, polygon)
            self.ways[uid] = way

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, ', '.join(['%s = %s' % (str(k), str(v)) for (k, v) in self.__dict__.items()]))

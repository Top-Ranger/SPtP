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

from geometry import *


excluded_tags = {
    # (key, value)
    ('amenity', 'waste_basket'),
    ('amenity', 'telephone'),
    ('amenity', 'emergency_phone'),
    ('amenity', 'bench'),
    ('amenity', 'post_box'),
    ('amenity', 'vending_machine'),
    ('amenity', 'atm'),
    ('barrier', '*'),
    ('building', 'entrance'),
    ('crossing_ref', '*'),
    ('emergency', 'fire_hydrant'),
    ('entrance', '*'),
    ('FIXME', '*'),
    ('fixme', '*'),
    ('highway', 'bus_stop'),
    ('highway', 'traffic_signals'),
    ('highway', 'crossing'),
    ('highway', 'street_lamp'),
    ('highway', 'stop'),
    ('highway', 'speed_camera'),
    ('highway', 'give_way'),
    ('highway', 'turning_circle'),
    ('historic', 'memorial'),
    ('information', 'board'),
    ('natural', 'tree'),
    ('noexit', '*'),
    ('public_transport', 'stop_position'),
    ('railway', 'switch'),
    ('railway', 'flat_crossing'),
    ('railway', 'buffer_stop'),
    ('railway', 'signal'),
    ('railway', 'level_crossing'),
    ('railway', 'subway_entrance'),
    ('railway', 'derail'),
    ('railway', 'crossing'),
    ('railway', 'switch'),
    ('railway', 'railway_crossing'),
    ('railway', 'rail'),
    ('railway', 'abandoned'),
    ('railway', 'tram'),
    ('railway', 'disused'),
    ('railway', 'light_rail'),
    ('railway', 'abandoned'),
    ('railway:switch', '*'),
    ('traffic_sign', '*'),
}
single_tags = ['created_by', 'name', 'ele', 'level']
polygon_radii_scale = 0.00015
polygon_radii = [
    # ((key, value), radius)
    # First match will used!
    (('leisure', 'playground'), 3),
    (('leisure', '*'), 2),
    (('shop', 'bakery'), 0.5),
    (('amenity', 'place_of_worship'), 4),
    (('amenity', 'pub'), 0.5),
    (('railway', 'station'), 10),
]


class GeneratedFromOSMNode:
    def __init__(self, location):
        """
        This class provides generated polygons for a location. The constructor updates
        self.nodes and self.ways.
        :param location: instance of location.Location
        :return: None
        """
        self.nodes = {}
        self.ways = {}

        for node in location.nodes.values():
            if GeneratedFromOSMNode.exclude_node(node):
                continue

            name = 'from_node_' + node.name
            tags = node.tags
            tags['source'] = 'gen_from_osm_node'
            radius = GeneratedFromOSMNode.polygon_radius(node)
            polygon = node.point.buffer(radius * polygon_radii_scale)
            self.ways[name] = Way(name, tags, polygon)

    @staticmethod
    def tags_match(t1, t2):
        """
        Tests two tags match, i. e. if
            t1.key == '*' or t2.key == '*' or t1.key == t2.key
                and
            t1.value == '*' or t2.value == '*' or t1.value == t2.value

        :param t1: first tag
        :type t1: (key, value)
        :param t2: second tag
        :type t2: (key, value)
        :return: True or False
        """
        return (t1[0] == '*' or t2[0] == '*' or t1[0] == t2[0]) and (t1[1] == '*' or t2[1] == '*' or t1[1] == t2[1])

    @staticmethod
    def exclude_node(node):
        """
        Tests if a node is excluded for performance reasons, i. e. if
            it has less than two tags
                or
            it is not an OSM node
                or
            it has one tag and that tag in found in single_tags
                or
            one of its tags is found in excluded_tags

        :param node: node to be tested
        :type node: geometry.Node
        :return: True or False
        """
        n = len(node.tags)

        if n < 2 or (not node.tags['source'] == 'osm'):
            return True

        if n == 2 and any(tag in single_tags for tag in node.tags):
            return True

        for tag in node.tags.items():
            for excluded_tag in excluded_tags:
                if GeneratedFromOSMNode.tags_match(tag, excluded_tag):
                    return True

        return False

    @staticmethod
    def polygon_radius(node):
        """
        Performs a lookup operation on polygon_radii by all node tags and defaults to 1.

        :param node: node to get the generated polygon radius for
        :type node: geometry.Node
        :return: generated polygon radius
        :rtype: float
        """
        for tag in node.tags.items():
            for polygon_radius in polygon_radii:
                polygon_radius_tag, radius = polygon_radius
                if GeneratedFromOSMNode.tags_match(tag, polygon_radius_tag):
                    return radius

        return 1

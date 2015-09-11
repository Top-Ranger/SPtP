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

class Node:
    def __init__(self, name, tags, point):
        """
        A class representing a node.

        :param name: Node id
        :type name: string
        :param tags: Node tags
        :type tags: dict
        :param point: Node point
        :type point: shapely.geometry.Point
        :return: None
        """
        self.name = name
        self.tags = tags
        self.point = point

    def json_serializable(self):
        """
        Returns a JSON representation of the node
        :return: JSON representation
        :rtype: dict
        """
        return {
            'name': self.name,
            'tags': self.tags,
            'point': [self.point.y, self.point.x]
        }

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, ', '.join(['%s = %s' % (str(k), str(v)) for (k, v) in self.__dict__.items()]))


class Way:
    def __init__(self, name, tags, polygon):
        """
        A class representing a way.

        :raise TypeError: if "points" is not a list
        :param tags: Tags associated with the point
        :type tags: dict
        :param polygon: Polygon describing the area
        :type polygon: shapely.geometry.Polygon
        :return None:
        """
        self.name = name
        self.tags = tags
        self.polygon = polygon

    def json_serializable(self):
        """
        Returns a JSON representation of the way
        :return: JSON representation
        :rtype: dict
        """
        return {
            'name': self.name,
            'tags': self.tags,
            'polygon': [[y, x] for (x, y) in list(self.polygon.exterior.coords)]
        }

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, ', '.join(['%s = %s' % (str(k), str(v)) for (k, v) in self.__dict__.items()]))


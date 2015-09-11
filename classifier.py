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

import math
import shapely.geometry
from image_processor import *


def get_classifiers_list(location=None, exclude_slow_classifiers=False):
    """
    Returns a list with all classifiers.
    
    :param location: Location to instantiate classifier with, may be None
    :type location: location.Location
    :param exclude_slow_classifiers: Exclude classifiers with suboptimal running times (default: False)
    :type exclude_slow_classifiers: bool
    :return: List with all classifiers
    :rtype: List
    """
    classifiers = [ProximityCentroid(location), PointInPolygon(location), ProximityClosestEdge(location),
                   ProximityClosestVertex(location),
                   SUROSMMapping(location), SURDescription(location), ExifDirection(location),
                   GeneratedFromOSMNodeWeight(location), OSMWeight(location)]
    if not exclude_slow_classifiers:
        classifiers += [ImageProcessing(location)]
    return classifiers


class Classifier():
    def __init__(self, location):
        """
        This is an abstract class representing a classifier.
        A classifier is a unit which rates the polygons with points between -100 and 100.
        Each classifier takes over one specific role.
        
        :param location: Location object
        :type location: location.Location
        :return: None
        """
        self.location = location

    def name(self):
        """
        This method provides an unique name as an identifier to that special implementation of the classifier.
        This is an abstract method - you have to overwrite it.
        
        :raise NotImplementedError: if not implemented in subclass
        :return: String containing the name
        :rtype: string
        """
        raise NotImplementedError("The method name() of Classifier is not implemented")

    def classify(self):
        """
        In this method the different polygons should be rated as how likely the SUR is applied in that polygon.
        Each polygon should be rated with points (integer) between -100 (very unlikely) and 100 (very likely). 0 is neutral.

        :raises NotImplementedError: if not implemented in subclass
        :return: Dictionary with polygon UIDs as keys and polygon points as values
        :rtype: dict
        """
        raise NotImplementedError("The method classify() of Classifier is not implemented")


class ProximityCentroid(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on the distance between the location and the polygon centroids.

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "Proximity (centroid)"

    def classify(self):
        # Compute distances
        distances = {}
        for (name, way) in self.location.ways.items():
            distances[name] = self.location.point.distance(way.polygon.centroid)

        # Determine points
        points = {}
        current = 100
        for uid in sorted(distances, key=distances.get):
            points[uid] = current
            current = max(current - 25, -100)

        return points


class PointInPolygon(Classifier):
    def __init__(self, location):
        """
        This classifier gives 100 points if the polygon contains the point, -75 otherwise.

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "Point in polygon"

    def classify(self):
        points = {}
        for (name, way) in self.location.ways.items():
            points[name] = 100 if way.polygon.contains(self.location.point) else -75
        return points


class ProximityClosestEdge(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on the distance between the location and the polygon's closest edge.

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "Proximity (closest edge)"

    def classify(self):
        # Compute distances
        distances = {}
        for (name, way) in self.location.ways.items():
            distances[name] = float('inf')
            coords = way.polygon.exterior.coords
            n = len(coords)
            for i in range(n):
                line_string = shapely.geometry.linestring.LineString([coords[i], coords[(i + 1) % n]])
                distances[name] = min(distances[name], self.location.point.distance(line_string))

        # Determine points
        points = {}
        current = 100
        for uid in sorted(distances, key=distances.get):
            points[uid] = current
            current = max(current - 25, -100)

        return points


class ProximityClosestVertex(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on the distance between the location and the polygon's closest vertex.

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "Proximity (closest vertex)"

    def classify(self):
        # Compute distances
        distances = {}
        for (name, way) in self.location.ways.items():
            distances[name] = float('inf')
            for coord in way.polygon.exterior.coords:
                distances[name] = min(distances[name], self.location.point.distance(shapely.geometry.Point(coord)))

        # Determine points
        points = {}
        current = 100
        for uid in sorted(distances, key=distances.get):
            points[uid] = current
            current = max(current - 25, -100)

        return points


class SUROSMMapping(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on the SURs and the tags of the polygons using a map.

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

        self.map = [
            # (SUR key, SUR value, OSM key, OSM value, points)
            # Points: added upon match, may be negative, total is multiplied by 10 and capped at +- 100)
            # '*': match any value
            ('access:dog', 'no', 'building', 'yes', 10),
            ('access:dog', 'no', 'shop', '*', 10),
            ('access:dog', 'no', 'amenity', '*', 10),
            ('access:dog', 'no', 'leisure', 'playground', 10),

            ('access', 'restricted', 'aeroway', 'aerodrome', 10),

            ('dog_waste', 'no', 'landuse', '*', 10),
            ('dog_waste', 'no', 'leisure', 'playground', 10),

            ('smoking', 'no', 'building', '*', 10),
            ('smoking', 'no', 'shop', '*', 10),
            ('smoking', 'no', 'building', 'roof', -20),
            ('smoking', 'no', 'building', 'university', 10),
            ('smoking', 'no', 'landuse', 'retail', 10),
            ('smoking', 'no', 'railway', 'platform', 10),
            ('smoking', 'no', 'railway', 'station', 10),
            ('smoking', 'no', 'highway', '*', -10),
            ('smoking', 'no', 'amenity', 'bank', 10),
            ('smoking', 'no', 'amenity', 'cafe', 10),
            ('smoking', 'no', 'amenity', 'parking', -10),
            ('smoking', 'no', 'amenity', 'bicycle_parking', -10),
            ('smoking', 'no', 'amenity', 'restaurant', 10),
            ('smoking', 'no', 'amenity', 'stables', 10),
            ('smoking', 'no', 'amenity', 'fast_food', 10),

            ('wear:helmet', 'no', 'amenity', 'bank', 10),
            ('access', 'no', 'landuse', 'construction', 10),

            ('parking', 'yes', 'amenity', 'parking', 10),
            ('parking', 'yes', 'parking', '*', 10),
            ('parking', 'restricted', 'amenity', 'parking', 10),
            ('parking', 'restricted', 'parking', '*', 10),

            ('food', 'no', 'highway', '*', -10),
            ('food', 'no', 'oneway', '*', -10),

            ('fire', 'no', 'amenity', 'stables', 10),

            ('dog_waste', 'no', 'natural', '*', 10),

            ('way:leave', 'no', 'landuse', 'forest', 10),
        ]

    def name(self):
        return "SUR-OSM Mapping"

    def classify(self):
        totals = {}
        for (name, way) in self.location.ways.items():
            points = 0
            for (sur_key, sur_value) in self.location.surs.items():
                for m in self.map:
                    match = True
                    match &= m[0] == '*' or m[0] == sur_key
                    match &= m[1] == '*' or m[1] == sur_value
                    if m[2] == '*' or m[2] in way.tags:
                        match &= m[3] == '*' or way.tags[m[2]] == m[3]
                    else:
                        match = False
                    if match:
                        points += m[4]

            totals[name] = min([100, points * 10]) if points > 0 else max([-100, points * 10])

        return totals


class ImageProcessing(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on image processing methods.

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)
        self.tags_outside = ['natural', 'landuse']
        if self.location is not None and self.location.image is not None:
            self.image_processor = ImageProcessor(self.location.image)

    def name(self):
        return "Image processing"

    def classify(self):
        if self.location is None or self.location.image is None:
            return dict(zip(self.location.ways.keys(), [0] * len(self.location.ways)))
        totals = {}
        is_rgba = self.location.image.mode in ('RGB', 'RGBA')
        if is_rgba:
            outside = self.image_processor.outside()

        for key in self.location.ways.keys():
            totals[key] = 0
            if is_rgba and outside:
                for tag in self.location.ways[key].tags:
                    if tag in self.tags_outside:
                        totals[key] = 100
                        break

        return totals


class SURDescription(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on the SURs and the tags of the polygon
        
        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)
        # Location tags
        self.tags_building = {'access:dog', 'smoking', 'food', 'access:age', 'access:fire_case'}
        self.tags_outside = {'dog_waste', 'littering', 'open_fire', 'animal_feeding'}
        self.tags_street = {'maxspeed', 'minspeed', 'oneway'}
        self.tags_water = {'swimming', 'fishing'}

        # OSM tags
        self.keys_building = {'building', 'shop'}  # Don't forget landuse=retail
        self.keys_outside = {'natural', 'landuse'}
        self.keys_street = {'highway', 'sidewalk', 'cycleway', 'busway', 'public_transport', 'railway', 'bridge',
                            'tracks', 'tunnel', 'route'}
        self.keys_water = {
        'waterway'}  # Don't forget natural=water,bay,spring | landuse = reservoir,basin,reservoir_watershed

    def name(self):
        return "SUR Description"

    def classify(self):
        points = {}
        for way_key in self.location.ways.keys():
            points_way = 0
            for sur_key in self.location.surs.keys():
                way_tags = self.location.ways[way_key].tags

                # Buildings
                if sur_key in self.tags_building:
                    delta = -1
                    for key in way_tags.keys():
                        if key in self.keys_building:
                            delta = 1
                        elif key == "landuse" and way_tags["landuse"] in ["retail"]:
                            delta = 1
                    points_way += delta

                # Outside
                if sur_key in self.tags_outside:
                    delta = -1
                    for key in way_tags.keys():
                        if key in self.keys_outside:
                            delta = 1
                    points_way += delta

                # Street
                if sur_key in self.tags_street:
                    delta = -1
                    for key in way_tags.keys():
                        if key in self.keys_street:
                            delta = 1
                    points_way += delta

                # Water
                if sur_key in self.tags_water:
                    delta = -1
                    for key in way_tags.keys():
                        if key in self.keys_water:
                            delta = 1
                        elif key == "natural" and way_tags["natural"] in ["water", "bay", "spring"]:
                            delta = 1
                        elif key == "landuse" and way_tags["landuse"] in ["reservoir", "basin", "reservoir_watershed"]:
                            delta = 1
                    points_way += delta

                # Identical
                for key in self.location.ways[way_key].tags.keys():
                    if key == sur_key and self.location.surs[sur_key] == self.location.ways[way_key].tags[key]:
                        # Must be low due to many location which do not have a corresponding tag.
                        points_way += 1

            # Determine points
            if points_way > 0:
                points[way_key] = min([100, points_way * 25])
            elif points_way < 0:
                points[way_key] = max([-100, points_way * 25])
            else:
                points[way_key] = 0

        return points


class ExifDirection(Classifier):
    def __init__(self, location):
        """
        This classifier rates based on the exif ImageDirection tag

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "Exif GPSInfo Direction"

    def classify(self):
        if 'direction' not in self.location.gps_info.keys():
            return dict(zip(self.location.ways.keys(), [0] * len(self.location.ways)))
        else:
            points = {}
            direction = self.location.gps_info['direction']
            p = self.location.point

            # Rotate
            a = math.radians(direction)
            c = math.cos(a)
            s = math.sin(a)
            x = 0
            y = 0.001
            v = shapely.geometry.Point(c * x - s * y, s * x + c * y)

            # Translate
            v = shapely.geometry.Point(p.x + v.x, p.y + v.y)

            line = shapely.geometry.LineString([p, v])
            # print(self.location.name, direction, str([str(c[1]) + ' ' + str(c[0]) for c in line.coords]))
            for (name, way) in self.location.ways.items():
                points[name] = 100 if line.intersects(way.polygon) else 0

        return points


class GeneratedFromOSMNodeWeight(Classifier):
    def __init__(self, location):
        """
        This classifier gives -100 points to generated polygons, 0 to other polygons.
        A polygon generated from an OSM node satisfies: tags['source'] == 'generated_from_osm_node'

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "Generated Weight"

    def classify(self):
        points = {}
        for (name, way) in self.location.ways.items():
            is_gpl_polygon = 'source' in way.tags and way.tags['source'] == 'gen_from_osm_node'
            points[name] = -100 if is_gpl_polygon else 0
        return points


class OSMWeight(Classifier):
    def __init__(self, location):
        """
        This classifier gives -100 points to open street maps polygons, 0 to other polygons.
        A open street maps polygon satisfies: tags['source'] == 'osm'

        :param location: Location to analyse
        :type location: location.Location
        :return: None
        """
        super().__init__(location)

    def name(self):
        return "OSM Weight"

    def classify(self):
        points = {}
        for (name, way) in self.location.ways.items():
            is_gpl_polygon = 'source' in way.tags and way.tags['source'] == 'osm'
            points[name] = -100 if is_gpl_polygon else 0
        return points
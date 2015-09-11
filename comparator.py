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

import os
import xml.etree.ElementTree
import sys
import math

import shapely.geos
import shapely.geometry.linestring

from kml import *


class ComparatorError(Exception):
    pass


class Comparator:
    def __init__(self, input_folder_path, output_folder_path, maximum_symmetric_difference, raise_on_critical_error=False, use_two_circle_intersection_ratio=False):
        """
        This class compares the polygons from the *.computed.kml (output folder) and the *.truth.kml (input folder)

        The result can be accessed via the dicts Comparator.passed, Comparator.failed and Comparator.erroneous

        :param input_folder_path: Path to the input folder where the *.truth.kml are located
        :type input_folder_path: string
        :param output_folder_path: Path to the output folder where the *.computed.kml are located
        :type output_folder_path: string
        :param maximum_symmetric_difference: Percent of area polygons have to share to be considered equal
        :type maximum_symmetric_difference: float
        :param raise_on_critical_error: If set to true the Comparator will rise exceptions on critical errors. Default False
        :type raise_on_critical_error: bool
        :param use_two_circle_intersection_ratio: If set to true the Comparator will use the "two circle intersection ratio" method!
        :type use_two_circle_intersection_ratio: bool
        :return: None
        """
        self.input_folder_path = input_folder_path
        self.output_folder_path = output_folder_path
        self.minimum_intersection_ratio = maximum_symmetric_difference
        self.total_intersection_ratio = 0
        self.average_intersection_ratio = 0
        self.raise_on_critical_error = raise_on_critical_error
        self.use_two_circle_intersection_ratio = use_two_circle_intersection_ratio
        self.passed = {}
        self.failed = {}
        self.erroneous = {}
        self.median = 0
        self.min_value = 0
        self.max_value = 0
        self.Q1 = 0
        self.Q3 = 0
        self.variance = 0
        self.standard_deviation = 0

    def handle_critical_error(self, message):
        """
        Handles critical errors and raises ComparatorError if Comparator.raise_on_critical_error is true
        :raise ComparatorError: if Comparator.raise_on_critical_error is true
        :param message: Error message
        :type message: string
        :return: None
        """
        if self.raise_on_critical_error:
            raise ComparatorError(message)
        else:
            print(message, file=sys.stderr)

    def run(self):
        """
        Compares the polygons

        :raise ComparatorError: if Comparator.raise_on_critical_error is true
        :return: None
        """
        # Read "truth polygons"
        if not os.path.exists(self.input_folder_path):
            self.handle_critical_error('Input folder (%s) does not exist' % self.input_folder_path)

        truth_polygons = {}
        for subdir_name, dir_names, file_names in os.walk(self.input_folder_path):
            for file_name in file_names:
                if '.truth.kml' not in file_name:
                    continue

                location_name = file_name.replace('.truth.kml', '')
                try:
                    kml = KML(xml.etree.ElementTree.parse(self.input_folder_path + file_name).getroot())
                    assert len(kml.ways) == 1
                    polygon = next(iter(kml.ways.values())).polygon
                    truth_polygons[location_name] = polygon
                except:
                    self.handle_critical_error('Failed to parse KML file "%s".' % file_name)

        # Read computed polygons
        if not os.path.exists(self.output_folder_path):
            self.handle_critical_error('Output folder (%s) does not exist' % self.output_folder_path)

        computed_polygons = {}
        for subdir_name, dir_names, file_names in os.walk(self.output_folder_path):
            for file_name in file_names:
                if '.computed.kml' not in file_name:
                    continue

                location_name = file_name.replace('.computed.kml', '')
                try:
                    kml = KML(xml.etree.ElementTree.parse(self.output_folder_path + file_name).getroot())
                    assert len(kml.ways) == 1
                    polygon = next(iter(kml.ways.values())).polygon
                    computed_polygons[location_name] = polygon
                except:
                    self.handle_critical_error('Failed to parse KML file "%s".' % file_name)

        values = []
        # Compare locations
        for key in truth_polygons:
            if not key in computed_polygons:
                self.handle_critical_error('Computed polygon not found for location "%s".' % key)
                continue

            try:
                truth_hull = truth_polygons[key].convex_hull
                computed_hull = computed_polygons[key].convex_hull
                passed = False
                intersection_ratio = 0.0
                if self.use_two_circle_intersection_ratio:
                    center = truth_polygons[key].centroid
                    distance_inner = float('inf')
                    distance_outer = -1.0
                    coords = truth_polygons[key].exterior.coords
                    n = len(coords)
                    for i in range(n):
                        distance_outer = max(distance_outer, center.distance(shapely.geometry.Point(coords[i])))
                        line_string = shapely.geometry.linestring.LineString([coords[i], coords[(i + 1) % n]])
                        distance_inner = min(distance_inner, center.distance(line_string))
                    inner_circle = center.buffer(distance_inner)
                    outer_circle = center.buffer(distance_outer * 1.5)
                    if abs(outer_circle.intersection(computed_hull).area / outer_circle.area) < self.minimum_intersection_ratio:
                        intersection_ratio = abs(inner_circle.intersection(computed_hull).area / inner_circle.area)
                else:
                    intersection_area = truth_hull.intersection(computed_hull).area
                    intersection_ratio = (2 * intersection_area) / (truth_hull.area + computed_hull.area)
                passed = self.minimum_intersection_ratio < intersection_ratio
                self.total_intersection_ratio += intersection_ratio
                values.append(intersection_ratio)
                if passed:
                    self.passed[key] = intersection_ratio
                else:
                    self.failed[key] = intersection_ratio
            except shapely.geos.TopologicalError as error:
                self.erroneous[key] = error

        values.sort()
        self.min_value = values[0]
        self.max_value = values[-1]
        self.median = values[round(len(values)/2)]
        self.Q1 = values[round(len(values)/4)]
        self.Q3 = values[round(len(values)*3/4)]
        self.average_intersection_ratio = self.total_intersection_ratio / len(truth_polygons)
        self.variance = sum((value - self.average_intersection_ratio) ** 2 for value in values) / len(values)
        self.standard_deviation = math.sqrt(self.variance)

    def print(self, output_file=sys.stdout, long=False):
        """
        Prints the Comparator results to a given file
        :param output_file: The file the result should be printed to (Default sys.stdout)
        :type output_file: file
        :param long: If True a list of categories is printed
        :type long: bool
        :return: None
        :rtype: None
        """
        failed = len(self.failed)
        passed = len(self.passed)
        erroneous = len(self.erroneous)
        total = failed + passed + erroneous

        print('Results: %d total, %d correct (%.2f%%), %d incorrect (%.2f%%), %d failed to compare (%.2f%%)' % (total, passed, passed / total * 100, failed, failed / total * 100, erroneous, erroneous / total * 100), file=output_file)
        print('Average intersection ratio: %.3f' % self.average_intersection_ratio, file=output_file)
        print('Variance: %.3f' % self.variance, file=output_file)
        print('Standard deviation: %.3f' % self.standard_deviation, file=output_file)
        print('Minimum: %.3f' % self.min_value, file=output_file)
        print('Q1: %.3f' % self.Q1, file=output_file)
        print('Median: %.3f' % self.median, file=output_file)
        print('Q3: %.3f' % self.Q3, file=output_file)
        print('Maximum: %.3f\n' % self.max_value, file=output_file)

        if long:
            print('%d incorrect' % failed, file=output_file)
            for (key, deviation) in sorted(self.failed.items(), key=lambda x: x[1]):
                print('\t%s -> %.8f' % (key, deviation), file=output_file)
            print('%d correct' % passed, file=output_file)
            for (key, deviation) in sorted(self.passed.items(), key=lambda x: x[1]):
                print('\t%s -> %.8f' % (key, deviation), file=output_file)
            print('%d failed to compare' % erroneous, file=output_file)
            for (key, error) in sorted(self.erroneous.items(), key=lambda x: x[0]):
                print('\t%s -> %s' % (key, str(error)), file=output_file)
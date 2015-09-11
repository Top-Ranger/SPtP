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

import json
import operator

from classifier import *


class Processor:
    def __init__(self, location, factors, output_folder_path, exclude_slow_classifiers):
        """
        A class which applies all classifiers to the data.
        
        :param location: Location data
        :type location: location.Location
        :param factors: Correction factors for the classifiers
        :type factors: factors.Factors
        :param output_folder_path: Path to save the resulting *.csv files in
        :type output_folder_path: string
        :return: None
        """
        self.location = location
        self.factors = factors
        self.output_folder_path = output_folder_path
        self.csv_separator = ';'
        self.points = {}
        self.transposed_output = True
        self.factors = factors
        self.exclude_slow_classifiers = exclude_slow_classifiers
        self.save_csv_files = False
        self.save_json_files = True

    def run(self):
        """
        Applies all classifiers and saves the results in the output folder.

        :return: Result of classification
        :rtype: [(polygon UID, highest total), ..., (polygon UID, lowest total)]
        """
        # Instantiate and apply classifiers
        classifiers = get_classifiers_list(location=self.location, exclude_slow_classifiers=self.exclude_slow_classifiers)
        for classifier in classifiers:
            points = classifier.classify()
            points = {k: round(self.factors.get_factor(classifier.name()) * v) for k, v in points.items()}
            self.points[classifier.name()] = points

        # Store results
        ways = sorted(self.location.ways)
        lines = []
        all_points = []
        lines += [[''] + ways]
        for (classifier_name, classifier_points) in self.points.items():
            classifier_uids_sorted = sorted(classifier_points)
            points = [classifier_points[u] for u in classifier_uids_sorted]
            all_points += [points]
            lines += [[classifier_name] + [str(p) for p in points]]
        totals = [sum(p) for p in zip(*all_points)]
        lines += [['Total'] + [str(t) for t in totals]]

        if self.transposed_output:
            lines = [[row[i] for row in lines] for i in range(len(ways) + 1)]

        if self.save_csv_files:
            csv_file_path = self.output_folder_path + self.location.name + '.points.csv'
            with open(csv_file_path, 'w') as points_file:
                for line in lines:
                    points_file.write(self.csv_separator.join(line) + '\n')

        if self.save_json_files:
            json_file_path = self.output_folder_path + self.location.name + '.json'
            with open(json_file_path, 'w') as json_file:
                json_file.write(json.dumps(self.location.json_serializable(), separators=(',', ':')))

        return sorted(zip(ways, totals), key=operator.itemgetter(1), reverse=True)

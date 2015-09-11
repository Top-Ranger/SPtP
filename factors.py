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

class Factors:
    def __init__(self):
        """
        This class reads a factor file and handles saving and managing factors.
        
        :return: None
        """
        self.factors = {}

    def load_file(self, path):
        """
        Loads a factor file.
        A "factor" file is a comma separated list containing (in that order):
        [classifier_name (string)], [factor (float)]
        
        :param path: Path to factor file
        :raise: ValueError if the file is empty
        :type path: string
        :return: None
        """
        try:
            with open(path, 'r') as data_file:
                for line in iter(data_file):
                    parts = [part.strip() for part in line.split(',')]
                    if not len(parts) == 2:
                        continue
                    self.factors[str(parts[0])] = float(parts[1])

                if self.factors == {}:
                    raise ValueError('Empty factors file')
        except OSError:
            self.factors = {}
            raise

    def write_file(self, path):
        """
        Writes the current factor dict in the file specified in 'path'.

        :param path: Path to write file
        :type path: string
        :return: None
        """
        with open(path, 'w') as data_file:
            for key in self.factors.keys():
                data_file.write('%s, %s\n' % (str(key), str(self.factors[key])))

    def get_factor(self, key):
        """
        Returns the factor associated with the key.
        Returns 1.0 if the factor does not exist.

        :param key: Key (Classifier.name()) of the requested factor
        :type key: string
        :return: Factor value
        :rtype: float
        """
        if key in self.factors.keys():
            return self.factors[key]
        else:
            return 1.0

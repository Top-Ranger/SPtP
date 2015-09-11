#!/usr/bin/env python3
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

import sys
import xml.etree.ElementTree

sys.path.append('..')
from kml import *


settings = {
    'cache_dir': './cache/',
    'cache_file_extension': '.osm',
    'input_dir': './input/'
}


def main(argv):
    """
    This method finds the polygon specified in argv[1] from the cache of argv[0] and saves it in argv[0].truth.kml

    :param argv: argv[0] = location name, argv[1] = name of OSM polygon
    :type argv: List of strings
    :return: None
    """
    if len(argv) != 2:
        print('Please specify two arguments:')
        print('- First the location name')
        print('- Second the target way')
        return

    try:
        osm = OSM(xml.etree.ElementTree.parse(settings["cache_dir"] + argv[0] + settings["cache_file_extension"]).getroot())
        way = osm.ways[argv[1]]
        if way is None:
            print('Unknown way')
            return
        kml = KMLBuilder()
        kml.add_placemark(way)
        string = kml.run()
        with open(settings['input_dir'] + argv[0] + ".truth.kml", "w") as kml_file:
            kml_file.write(string)
        print('Success')
    except Exception as e:
        print('Something went wrong')
        print(str(e))


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\nAborted')
        sys.exit(0)

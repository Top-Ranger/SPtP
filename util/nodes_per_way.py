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
import os
import xml.etree.ElementTree

sys.path.append('..')
from osm import OSM

for subdir, dirs, files in os.walk(os.path.join('..', 'cache')):
    total_avg = 0
    for file in files:
        osm = OSM(xml.etree.ElementTree.parse(os.path.join(subdir, file)).getroot())
        avg = 0
        for way in osm.ways.values():
            avg += len(way.polygon.exterior.coords)
        avg /= len(osm.ways)
        total_avg += avg
        print('%s: %.2f' % (file, avg))
    total_avg /= len(files)
    print('Total: %.2f' % total_avg)

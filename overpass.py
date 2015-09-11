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

import urllib
import urllib.parse
import urllib.request
import os.path


class Overpass:
    def __init__(self, output_file_path):
        self.output_file_path = output_file_path
        self.file_size = -1

    def query_by_osm_script(self, osm_script):
        """
        This function passes an OSM script to the "Open Street Map Overpass API"
        (http://overpass-api.de/api/interpreter). It saves the result in a file.

        :param osm_script: Correct OSM script which should be used for the request
        :type osm_script: string
        :return: Information about the request in the form (filename, headers)
        :rtype: (string, dict)
        """
        query = {'data': osm_script}
        relative_file_path, headers = urllib.request.urlretrieve('http://overpass-api.de/api/interpreter?' + urllib.parse.urlencode(query), self.output_file_path)
        self.file_size = os.path.getsize(relative_file_path)
        return relative_file_path, headers

    def query_by_lat_lon_and_radius(self, lat, lon, radius):
        """
        This function is an interface to the Overpass API which takes away the need of writing your own OSM script.

        :param lat: Latitude of the target position
        :type lat: float
        :param lon: Longitude of the target position
        :type lon: float
        :param radius: Radius in which should be searched
        :type radius: int
        :return: Information about the request in the form (filename, headers)
        :rtype: (filename, headers)
        """
        osm_script = '\
        <osm-script>\
            <union>\
                <query type="way">\
                    <around lat="' + str(lat) + '" lon="' + str(lon) + '" radius="' + str(radius) + '"/>\
                </query>\
                <recurse type="way-node"/>\
                <query type="node">\
                    <around lat="' + str(lat) + '" lon="' + str(lon) + '" radius="' + str(radius) + '"/>\
                </query>\
            </union>\
            <print/>\
        </osm-script>'

        return self.query_by_osm_script(osm_script)

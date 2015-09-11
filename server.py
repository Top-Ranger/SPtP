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

import xml.etree.ElementTree
import cgi
import os
import http.server
import hashlib
import base64
import sys

import PIL.Image

from kml import *
from location import *
from overpass import *
from processor import *
from factors import *
from generated import *

class JSONNotFoundError(Exception):
    pass

def default_settings():
    """
    This method returns a dict containing the default settings for the server.

    :return: Default settings
    :rtype: dict
    """
    return {
        'host': 'localhost',
        'port': 8080,
        # Paths must be relative to /server/
        'data_folder_path': '../data/',
        'cache_folder_path': '../cache/',
        'input_folder_path': '../input/',
        'output_folder_path': '../output/',
        'images_folder_path': './images/',
        'tmp_files_folder_path': './tmp/',
        'quiet_mode': False,
        'correct_kml_suffix': '.truth.kml',
        'computed_kml_suffix': '.computed.kml',
        'json_file_suffix': '.json',
        'maximum_image_height': 350,
        'maximum_image_width': 350
    }


def format_header(settings):
    """
    Creates a printable header from server settings.

    :param settings: Server settings
    :type settings: dict
    :return: Formatted header
    :rtype: string
    """

    def item(label, value):
        """
        Creates a header item (line) with correct padding.

        :param label: Label of the option
        :type label: string
        :param value: Value of the label
        :type value: string
        :return: Correct formatted line
        :rtype string
        """
        return label.ljust(30, '.') + ': ' + str(value) + '\n'

    header = "SPtP - Server\n-------------\n\n"
    header += item('Host', settings['host'])
    header += item('Port', settings['port'])
    header += item('Data folder path', os.path.abspath(settings['data_folder_path']))
    header += item('Input folder path', os.path.abspath(settings['input_folder_path']))
    header += item('Output folder path', os.path.abspath(settings['output_folder_path']))
    header += item('Cache folder path', os.path.abspath(settings['cache_folder_path']))
    header += item('Images folder path', os.path.abspath(settings['images_folder_path']))
    header += item('Temporary files folder path', os.path.abspath(settings['tmp_files_folder_path']))

    return header


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Implements the server's HTTP request handler extending http.server.SimpleHTTPRequestHandler.
    """

    def exception_to_str(self, exception):
        """
        Convenience method for creating a JSON serializable exception representation.

        :param exception: Exception to be converted
        :type exception: Exception
        :return: JSON serializable exception representation
        :rtype: string
        """
        return str(exception).replace("'", '"')

    def _query_location(self, location_name):
        """
        Helper method to retrieve all information available on the location
        with the given name and prepare it for transmission to the client.

        :param location_name: name of the location
        :return: None
        """
        try:
            json_file_path = self.server.settings['output_folder_path'] + location_name + self.server.settings['json_file_suffix']
            with open(json_file_path) as json_file:
                location = json.loads(json_file.read())
        except:
            raise JSONNotFoundError()

        computed_kml_file_name = location_name + self.server.settings['computed_kml_suffix']
        computed_kml_file_path = self.server.settings['output_folder_path'] + computed_kml_file_name
        computed_kml = KML(xml.etree.ElementTree.parse(computed_kml_file_path).getroot())
        point = next(iter(computed_kml.nodes.values())).point
        with open(computed_kml_file_path) as kml_file:
            location['kml'] = kml_file.read()
        location['kml_name'] = computed_kml_file_name
        location['point'] = [point.y, point.x]
        location['computed'] = next(iter(computed_kml.ways.values())).json_serializable()

        try:
            truth_kml_file_path = self.server.settings['input_folder_path'] + location_name + self.server.settings['correct_kml_suffix']
            truth_kml = KML(xml.etree.ElementTree.parse(truth_kml_file_path).getroot())
            location['truth'] = next(iter(truth_kml.ways.values())).json_serializable()
        except:
            location['truth'] = None

        try:
            if not os.path.exists(self.server.settings['images_folder_path']):
                os.makedirs(self.server.settings['images_folder_path'])
            hash = hashlib.md5()
            hash.update(str(self.server.settings['output_folder_path'] + location_name + '.jpg').encode('utf-8'))
            hash.update(str(os.path.getmtime(self.server.settings['output_folder_path'] + location_name + '.jpg')).encode('utf-8'))
            image_file_path = self.server.settings['images_folder_path'] + hash.hexdigest() + '.png'
            if not os.path.exists(image_file_path):
                image = PIL.Image.open(self.server.settings['output_folder_path'] + location_name + '.jpg', 'r')
                width, height = image.size
                scalar = self.server.settings['maximum_image_width'] / width if width > height else self.server.settings['maximum_image_height'] / height
                height *= scalar
                width *= scalar
                image = image.resize((int(width), int(height)), PIL.Image.ANTIALIAS)
                image.save(image_file_path, 'PNG')
            location['image_file_path'] = image_file_path
        except:
            location['image_file_path'] = None

        return location

    def query_location(self, fields):
        """
        Implements server action "query_location". The field store is expected to contain:
        - location_name: name of the location

        :param fields: POST request's fields
        :type fields: cgi.FieldStorage
        :return: None
        """

        if not 'location_name' in fields:
            self.send_json({'result': 'failure', 'reason': 'Missing field value: "location_name".'})
            return

        try:
            location = self._query_location(fields['location_name'].value)
        except JSONNotFoundError:
            self.send_json({'result': 'failure', 'reason': 'JSON file not found or corrupted'})
            return
        except FileNotFoundError:
            self.send_json({'result': 'failure', 'reason': 'Computed KML file not found'})
            return
        except OSError:
            self.send_json({'result': 'failure', 'reason': 'Failed to read computed KML file'})
            return
        except xml.etree.ElementTree.ParseError:
            self.send_json({'result': 'failure', 'reason': 'Failed to parse computed KML file'})
            return
        except Exception as error:
            self.send_json({'result': 'failure', 'reason': 'Unknown error: %s' % str(error)})
            return

        response = {'result': 'success', 'type': 'location', 'data': location}
        self.send_json(response)

    def process_location(self, fields):
        """
        Implements server action "process_location". The field storage is expected to contain:
        - lat: latitude (convertible to float)
        - lon: longitude (convertible to float)
        - radius: Overpass API radius (convertible to int)
        - surs: space usage rules (e. g. 'smoking="no"'), each on a new line
        - location_name: name of the location

        Optional fields:
        - image_base_64: base 64 string containing image data (any type PIL can process)

        Uses factors file at server_settings['data_folder_path'] + 'factors.txt'.

        :param fields: POST request's fields
        :type fields: cgi.FieldStorage
        :return: None
        """
        if not 'lat' in fields:
            self.send_json({'result': 'failure', 'reason': 'Latitude is missing.'})
            return

        try:
            lat = float(fields['lat'].value)
        except ValueError:
            self.send_json({'result': 'failure', 'reason': 'Invalid latitude format.'})
            return

        if not 'lon' in fields:
            self.send_json({'result': 'failure', 'reason': 'Longitude is missing.'})
            return

        try:
            lon = float(fields['lon'].value)
        except ValueError:
            self.send_json({'result': 'failure', 'reason': 'Invalid longitude format.'})
            return

        if not 'radius' in fields:
            self.send_json({'result': 'failure', 'reason': 'Radius is missing.'})
            return

        try:
            radius = float(fields['radius'].value)
        except ValueError:
            self.send_json({'result': 'failure', 'reason': 'Invalid radius format.'})
            return

        location = Location('Manual', shapely.geometry.Point(lon, lat))

        if not 'surs' in fields:
            self.send_json({'result': 'failure', 'reason': 'SURs are missing.'})
            return

        surs_raw = fields['surs'].value
        if len(surs_raw) == 0:
            self.send_json({'result': 'failure', 'reason': 'SURs are missing.'})
            return

        for sur in surs_raw.split('\n'):
            pattern = re.compile('([^=]*)=["]*([^"]*)["]*')
            match = pattern.match(sur)
            if not match:
                self.send_json({'result': 'failure', 'reason': 'Invalid SUR: %s' % sur})
                return
            sur_key = match.group(1)
            sur_value = match.group(2)
            if not sur_key or len(sur_key) == 0 or not sur_value or len(sur_value) == 0:
                self.send_json({'result': 'failure', 'reason': 'Invalid SUR: %s' % sur})
                return
            location.surs[sur_key] = sur_value

        if not os.path.exists(self.server.settings['tmp_files_folder_path']):
            try:
                os.makedirs(self.server.settings['tmp_files_folder_path'])
            except OSError as error:
                self.send_json({'result': 'failure', 'reason': 'Could not create folder for temporary files.'})
                return

        osm_file_path = self.server.settings['tmp_files_folder_path'] + 'manual.osm'
        try:
            overpass = Overpass(osm_file_path)
            overpass.query_by_lat_lon_and_radius(lat, lon, radius)
        except:
            self.send_json({'result': 'failure', 'reason': 'Error querying Overpass API.'})
            return

        try:
            osm = OSM(xml.etree.ElementTree.parse(osm_file_path))
        except:
            self.send_json({'result': 'failure', 'reason': 'Error parsing Overpass OSM data.'})
            return
        location.add_osm(osm)

        generated = GeneratedFromOSMNode(location)
        location.add_generated(generated)

        if 'image_base_64' in fields:
            try:
                image_base_64 = fields['image_base_64'].value.partition('base64,')[2]
                image_data = base64.b64decode(image_base_64)

                image_file_path = self.server.settings['tmp_files_folder_path'] + 'manual.image'
                with open(image_file_path, 'wb') as file:
                    file.write(image_data)
                location.image = PIL.Image.open(image_file_path)
            except Exception as error:
                self.send_json(
                    {'result': 'failure', 'reason': 'Failed to process image: %s' % self.exception_to_str(error)})
                return
        else:
            location.image = None
            image_file_path = None

        factors = Factors()
        try:
            factors.load_file(self.server.settings['data_folder_path'] + 'factors.txt')
        except Exception as exception:
            print('Failed to load factors file. Using default factors. Exception: %s' % str(exception), file=sys.stderr)
        processor = Processor(location, factors, self.server.settings['tmp_files_folder_path'], True)
        try:
            totals = processor.run()
        except Exception as exception:
            self.send_json({'result': 'failure', 'reason': 'Failed to process location: %s' % str(exception)})
            return

        if not totals or not totals[0][0]:
            self.send_json({'result': 'failure', 'reason': 'No polygon found.'})
            return
        winner_uid = totals[0][0]

        # Build KML
        single_kml_builder = KMLBuilder()
        kml_way = location.ways[winner_uid]
        kml_way.name = location.name
        single_kml_builder.add_placemark(kml_way)

        kml_node = Node(location.name, {}, location.point)
        single_kml_builder.add_placemark(kml_node)
        kml = single_kml_builder.run()

        location = {
            'name': 'Manual',
            'point': [lat, lon],
            'nodes': {k: v.json_serializable() for (k, v) in location.nodes.items()},
            'ways': {k: v.json_serializable() for (k, v) in location.ways.items()},
            'surs': location.surs,
            'computed': location.ways[winner_uid].json_serializable(),
            'image_file_path': image_file_path,
            'kml': kml,
            'kml_name': 'manual.computed.kml'
        }
        response = {'result': 'success', 'type': 'location', 'data': location}
        self.send_json(response)

    def query_location_names(self, fields):
        """
        Implements server action "process_location". The field storage is ignored.

        :param fields: POST request's fields (ignored)
        :type fields: cgi.FieldStorage
        :return: None
        """
        location_names = []
        for subdir_name, dir_names, file_names in os.walk(self.server.settings['output_folder_path']):
            for file_name in file_names:
                if self.server.settings['computed_kml_suffix'] in file_name:
                    location_names += [file_name.replace(self.server.settings['computed_kml_suffix'], '')]

        location_names.sort()
        response = {'result': 'success', 'type': 'location_names', 'data': location_names}
        self.send_json(response)

    def do_POST(self):
        """
        Handles a POST request to the server. Its header is expected to contain an 'action' field
        that resolves to one of the following server action names:
        - "query_location": retrieves information on a single stored location (e.g. computed polygon, truth polygon (if available))
        - "query_location_names": retrieves a list of location names for the "Query location" dialog.
        - "process_location": manually submits a location to the processing logic

        :return: None
        """
        fields = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
        try:
            action = fields['action'].value
        except:
            self.send_json({'result': 'failure', 'reason': 'Missing field value: "action".'})
            return

        if action == "query_location":
            self.query_location(fields)
            return

        if action == "query_location_names":
            self.query_location_names(fields)
            return

        if action == "process_location":
            self.process_location(fields)
            return

        self.send_json({'result': 'failure', 'reason': 'Unknown action: "%s".' % action})

    def send_json(self, object):
        """
        Converts the given object to (pretty) JSON, builds an HTTP response with header
        and sends it to the client.

        :param object: any object
        :return: None
        """
        body = json.dumps(object, separators=(',', ':'))
        self.send_response(200)  # HTTP code: OK
        self.send_header("Content-type", 'application/json')
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        """
        Overridden to save message into log file instead of stderr.

        :return: None
        """
        try:
            with open('./server.log', 'a', 1) as log_file:
                log_file.write("From %s at %s: %s\n" % (self.address_string(), self.log_date_time_string(), format % args))
        except OSError:
            sys.stderr.write('Can not write to log file "./server.log" Message: ')
            sys.stderr.write("From %s at %s: %s\n" % (self.address_string(), self.log_date_time_string(), format % args))
            pass
        return


class Server(http.server.HTTPServer):
    def __init__(self, *args, settings=default_settings(), **kwargs):
        """
        Calls http.server.HTTPServer.__init__() and stores the given settings
        to self.settings. This makes them available to the request handler.

        :param settings: server settings (Default: server.default_settings())
        :type settings: dict
        :return: None
        """
        http.server.HTTPServer.__init__(self, *args, **kwargs)
        self.settings = settings

    def start(self):
        """
        Prints the settings header to stdout and calls http.server.HTTPServer.serve_forever().

        :return: None
        """
        header = format_header(self.settings)
        if not self.settings['quiet_mode']:
            print(header)

        http.server.HTTPServer.serve_forever(self)

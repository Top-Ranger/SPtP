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

import os
import sys
import argparse

import server


def main(argv):
    """
    Parses command line options and starts the server.

    :param argv: Command line arguments
    :type argv: list
    :return: None
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='SPtP Server')
    parser.add_argument('--host', dest='host', default='localhost'
                                                       '', help='Host name. Default: localhost')
    parser.add_argument('--port', dest='port', default=8080, type=int, help='Port. Default: 8080')
    parser.add_argument('--data_folder_path', dest='data_folder_path', default='../data/', help='Path to data folder containing factors.txt. Default: ../data/ (relative to server/)')
    parser.add_argument('--input_folder_path', dest='input_folder_path', default='../input/', help='Path to input folder containing *.truth.kml. Default: ../input/ (relative to server/)')
    parser.add_argument('--output_folder_path', dest='output_folder_path', default='../output/', help='Path to output folder. Default: ../output/ (relative to server/)')
    parser.add_argument('--cache_folder_path', dest='cache_folder_path', default='../cache/', help='Path to cache folder containing *.osm. Default: ../input/ (relative to server/)')
    parser.add_argument('--images_folder_path', dest='images_folder_path', default='./images/', help='Path to input folder. Default: ./images/ (relative to server/)')
    parser.add_argument('-q', '--quiet-mode', dest='quiet_mode', help='Prevents all output to stdout.', action='store_true')
    args = parser.parse_args()

    # Compile settings
    settings = server.default_settings()
    settings['host'] = args.host
    settings['port'] = args.port
    settings['quiet_mode'] = args.quiet_mode
    settings['data_folder_path'] = args.data_folder_path + '/'
    settings['cache_folder_path'] = args.cache_folder_path + '/'
    settings['input_folder_path'] = args.input_folder_path + '/'
    settings['output_folder_path'] = args.output_folder_path + '/'
    settings['images_folder_path'] = args.images_folder_path + '/'

    # Run server
    os.chdir('server/')
    try:
        server_instance = server.Server((settings['host'], settings['port']), server.HTTPRequestHandler, settings=settings)
    except OSError as error:
        print('Error while starting server: %s' % str(error), file=sys.stderr)
        sys.exit(1)
    try:
        server_instance.start()
    except KeyboardInterrupt:
        print('\nServer halted.')
        sys.exit(0)

if __name__ == '__main__':
    main(sys.argv[1:])

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

import argparse
import sys
import os.path

import batch


def main(argv):
    """
    Parses command line options and starts the batch processing.

    :param argv: Command line arguments
    :type argv: list
    :return: None
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='SPtP Batch Processing')
    parser.add_argument('-i', '--input-folder-path', dest='input_folder_path',
                        help='Path to the folder containing input data (i. e. images, SURs file, and *.truth.kml files).')
    parser.add_argument('-o', '--output-folder-path', dest='output_folder_path',
                        help='Path to the folder that will contain the resulting KML files. It will be deleted if it exists.')
    parser.add_argument('-s', '--surs-file-path', dest='surs_file_path', default='./input/surs.txt',
                        help='Path to the text file containing the SURs. (Default: ./input/surs.txt)')
    parser.add_argument('-f', '--factors-file-path', dest='factors_file_path', default='./data/factors.txt',
                        help='Path to the text file containing the SURs. (Default: ./data/factors.txt).')
    parser.add_argument('-c', '--cache-folder-path', dest='cache_folder_path',
                        help='Path to the folder containing cache data (i. e. data from OpenStreetMap)')
    parser.add_argument('-u', '--force-cache-update', dest='force_cache_update', help='Force cache update.',
                        action='store_true')
    parser.add_argument('--skip-cache-update', dest='skip_cache_update',
                        help='Skip automatic cache update. Useful e.g. if no internet connection is available.',
                        action='store_true')
    parser.add_argument('-q', '--quiet-mode', dest='quiet_mode', help='Do not write to stdout.', action='store_true')
    parser.add_argument('--exclude-slow-classifiers', dest='exclude_slow_classifiers',
                        help='Exclude classifiers with suboptimal running times.', action='store_true')
    parser.add_argument('--overpass-radius', dest='overpass_radius', help='Overpass API query radius.', type=int)
    parser.add_argument('--compare-results', dest='compare_results',
                        help='Compare computed polygons to polygons in *.truth.kml files.', action='store_true')
    parser.add_argument('--log-prefix', dest='log_file_prefix', default='icup_',
                        help='Sets a prefix for log file names. (Default: icup_)')
    parser.add_argument('--debug-output', dest='debug_output', help='Saves CSV files for debug purposes.',
                        action='store_true')
    parser.add_argument('--two-circle-intersection', dest='use_two_circle_intersection_ratio',
                        help='Use two circle intersection ratio method. Default: False', action='store_true')

    args = parser.parse_args()

    # Compile settings
    settings = batch.default_settings()
    if args.input_folder_path:
        settings['input_folder_path'] = args.input_folder_path + os.path.sep
    if args.output_folder_path:
        settings['output_folder_path'] = args.output_folder_path + os.path.sep
    if args.cache_folder_path:
        settings['cache_folder_path'] = args.cache_folder_path + os.path.sep
    if args.overpass_radius:
        settings['overpass_radius'] = args.overpass_radius
    settings['surs_file_path'] = args.surs_file_path
    settings['factors_file_path'] = args.factors_file_path
    settings['force_cache_update'] = args.force_cache_update
    settings['skip_cache_update'] = args.skip_cache_update
    settings['quiet_mode'] = args.quiet_mode
    settings['exclude_slow_classifiers'] = args.exclude_slow_classifiers
    settings['compare_results'] = args.compare_results
    settings['log_file_prefix'] = args.log_file_prefix
    settings['debug_output'] = args.debug_output
    settings['use_two_circle_intersection_ratio'] = args.use_two_circle_intersection_ratio

    # Run batch processing
    exit_code = batch.main(settings)
    if not args.quiet_mode:
        if exit_code == 0:
            print('Batch processing finished successfully.')
        else:
            print('Batch processing failed. Check log files for details.')
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print('\nBatch processing aborted.')
        sys.exit(0)

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

import shutil
import time
import xml.etree.ElementTree
import urllib.request
import multiprocessing

from location import *
from generated import *
from overpass import *
from processor import *
from comparator import *
from factors import *


def default_settings():
    """
    Returns a dict containing the default settings for batch processing.

    :return: Default batch processing settings
    :rtype: dict
    """
    return {
        'input_folder_path': './input/',
        'output_folder_path': './output/',
        'surs_file_path': 'surs.txt',  # relative to input_folder_path
        'factors_file_path': 'factors.txt',
        'cache_folder_path': './cache/',
        'log_folder_path': './log/',
        'log_file_prefix': '',
        'force_cache_update': False,
        'skip_cache_update': False,
        'maximum_cache_file_age': 4 * 24 * 60 * 60,
        'overpass_radius': 200,
        'minimum_intersection_ratio': 0.7,
        'compare_results': True,
        'exclude_slow_classifiers': False,
        'quiet_mode': False,
        'factors': None,
        'debug_output': False,
        'use_two_circle_intersection_ratio': False
    }

def format_header(settings):
    """
    Creates a printable header from batch processing settings.

    :param settings: Batch processing settings
    :type settings: dict
    :return: Printable header
    :rtype: string
    """
    def item(label, value):
        """
        Returns a header item (line) with correct padding.
        :param label: Label of the option
        :type label: string
        :param value: Value of the option
        :type value: string
        :return: Formatted line
        :rtype String
        """
        return label.ljust(30, '.') + ': ' + str(value) + '\n'

    header = "SPtP - Batch Processing\n-----------------------\n\n"
    header += item('Input folder path', os.path.abspath(settings['input_folder_path']))
    header += item('Output folder path', os.path.abspath(settings['output_folder_path']))
    header += item('SURs file path', os.path.abspath(settings['surs_file_path']))
    header += item('Factors file path', os.path.abspath(settings['factors_file_path']))
    header += item('Cache folder path', os.path.abspath(settings['cache_folder_path']))
    header += item('Log folder path', os.path.abspath(settings['log_folder_path']))
    header += item('Log file prefix', settings['log_file_prefix'])
    header += item('Force cache update', settings['force_cache_update'])
    header += item('Maximum cache file age', time.strftime("%dd %Hh %Mm %Ss", time.gmtime(settings['maximum_cache_file_age'])))
    header += item('Exclude slow classifiers', settings['exclude_slow_classifiers'])
    header += item('Overpass radius [m]', settings['overpass_radius'])
    header += item('Minimum intersection ratio', settings['minimum_intersection_ratio'])
    header += item('Compare results', settings['compare_results'])
    header += item('Debug CSV output', settings['debug_output'])
    header += item('Use two circle intersection ratio', settings['use_two_circle_intersection_ratio'])

    return header


def worker(locations, worker_id, settings):
    """
    Worker function that processes given locations.
    Used for multi-processing.

    :param locations: Locations this worker will process
    :type locations: list
    :param worker_id: Unique worker identification token
    :type worker_id: int
    :param settings: Reference to batch settings
    :type settings: dict
    :return: None
    """

    try:
        start_time = time.time()
        worker_log_file_path = settings['log_folder_path'] + settings['log_file_prefix'] + 'process_' + str(worker_id) + '.log'
        with open(worker_log_file_path, 'w', 1) as worker_log_file:
            worker_log_file.write('+++ Started process %i at %i +++\n\n' % (worker_id, time.time()))

            # Import images
            worker_log_file.write('Importing images...')
            failed_osm_parsings = {}
            image_error_string=''
            for location in locations.values():
                image_file_path = settings['input_folder_path'] + location.name + '.jpg'
                if os.path.isfile(image_file_path):
                    try:
                        location.add_image(image_file_path)
                    except OSError as error:
                        failed_osm_parsings[location.name] = image_file_path
                        image_error_string += '\tFailed to add image %s: %s \n' % (image_file_path, str(error))
                        print('\nFailed to add image: %s' % str(error), file=sys.stderr)
                else:
                    failed_osm_parsings[location.name] = image_file_path
                if not settings['quiet_mode']:
                    print('.', end='', flush=True)
            worker_log_file.write('OK, %d failed \n' % len(failed_osm_parsings))
            worker_log_file.write(image_error_string)

            # Update OSM cache
            if not settings['skip_cache_update']:
                worker_log_file.write('Updating OSM cache...\n')
                current_time = time.time()
                for location in locations.values():
                    cache_file_name = settings['cache_folder_path'] + location.name + '.osm'
                    worker_log_file.write('\t' + cache_file_name + '...')
                    file_exists = os.path.isfile(cache_file_name)
                    if file_exists:
                        file_mtime = os.path.getmtime(cache_file_name)
                    else:
                        file_mtime = 0
                    if settings['force_cache_update'] or not file_exists or current_time - file_mtime > settings['maximum_cache_file_age']:
                        overpass = Overpass(cache_file_name)
                        try:
                            overpass.query_by_lat_lon_and_radius(location.point.y, location.point.x, settings['overpass_radius'])
                        except (urllib.request.URLError, OSError) as error:
                            print('Could not get "%s", aborting.\n' % cache_file_name, file=sys.stderr)
                            worker_log_file.write('FAILURE\n')
                            worker_log_file.write('Exception: %s\n' % str(error))
                            worker_log_file.write('Could not get "%s", aborting.\n' % cache_file_name)
                            sys.exit(1)
                        worker_log_file.write('OK, %d bytes\n' % overpass.file_size)
                        if not settings['quiet_mode']:
                            print('.', end='', flush=True)
                    else:
                        worker_log_file.write('Skipped\n')
            else:
                worker_log_file.write('Skipping cache update.\n')

            # Parse OSM files
            try:
                worker_log_file.write('Parsing OSM files...')
                for location in locations.values():
                    cache_file_name = settings['cache_folder_path'] + location.name + '.osm'
                    try:
                        element_tree = xml.etree.ElementTree.parse(cache_file_name)
                    except xml.etree.ElementTree.ParseError as error:
                        print('Removing bad file "%s", please restart the script.' % cache_file_name, file=sys.stderr)
                        worker_log_file.write('FAILURE\nException: %s\n' % str(error))
                        worker_log_file.write('Removing bad file "%s", please restart the script.\n' % cache_file_name)
                        os.remove(cache_file_name)
                        sys.exit(1)

                    osm = OSM(element_tree.getroot())
                    location.add_osm(osm)
                worker_log_file.write('OK\n')
                if not settings['quiet_mode']:
                    print('.', end='', flush=True)
            except OSError as error:
                print('Could not parse OSM files, aborting.', file=sys.stderr)
                worker_log_file.write('FAILURE\nException: %s\n' % str(error))
                worker_log_file.write('Could not parse OSM files, aborting.\n')
                sys.exit(1)

            # Add generated locations
            for location in locations.values():
                generated = GeneratedFromOSMNode(location)
                location.add_generated(generated)

            # Process
            worker_log_file.write('Processing...')
            if settings['factors'] is None:
                factors = Factors()
                try:
                    factors.load_file(settings['factors_file_path'])
                except Exception as exception:
                    print('Could not load factors file, aborting.', file=sys.stderr)
                    worker_log_file.write('FAILURE\nException: %s\n' % str(exception))
                    worker_log_file.write('Could not load factors file, aborting.\n')
                    sys.exit(1)
            else:
                factors = settings['factors']
            for location in locations.values():
                # Determine winner
                processor = Processor(location, factors, settings['output_folder_path'], settings['exclude_slow_classifiers'])

                processor.save_csv_files = settings['debug_output']

                try:
                    totals = processor.run()
                except Exception as error:
                    print('Could not complete processing, aborting.', file=sys.stderr)
                    worker_log_file.write('FAILURE\nException: %s\n' % str(error))
                    worker_log_file.write('Could not complete processing, aborting.\n')
                    sys.exit(1)
                winner_uid = totals[0][0]

                # Build and save local KML
                single_kml_builder = KMLBuilder()
                kml_way = location.ways[winner_uid]
                kml_way.name = location.name
                if location.image is not None:
                    kml_way.tags['description'] = '<img src="' + location.name + '.jpg" width="400"/>'
                single_kml_builder.add_placemark(kml_way)

                kml_node = Node(location.name, {}, location.point)
                single_kml_builder.add_placemark(kml_node)
                kml = single_kml_builder.run()

                local_kml_file_path = settings['output_folder_path'] + location.name + '.computed.kml'
                try:
                    with open(local_kml_file_path, 'w') as kml_file:
                        kml_file.write(kml)
                except OSError as error:
                    print('Could not save KML file "%s", aborting.' % local_kml_file_path, file=sys.stderr)
                    worker_log_file.write('FAILURE\nException: %s\n' % str(error))
                    worker_log_file.write('Could not save KML file "%s", aborting.\n' % local_kml_file_path)
                    sys.exit(1)

                if location.image is not None:
                    image_file_path = settings['output_folder_path'] + location.name + '.jpg'
                    try:
                        location.image.save(image_file_path)
                    except OSError as error:
                        print('Could not save image file "%s"' % image_file_path, file=sys.stderr)
                        worker_log_file.write('FAILURE\nException: %s\n' % str(error))
                        worker_log_file.write('Could not save image file "%s"\n' % image_file_path)
                if not settings['quiet_mode']:
                    print('.', end='', flush=True)

            worker_log_file.write('OK\n')
            worker_log_file.write('\n+++ Completed process %i +++\n' % worker_id, )

            end_time = time.time()
            worker_log_file.write('\nElapsed time: %.2f ms\n' % ((end_time - start_time) * 1000))

    except OSError as error:
        print('Process ' + worker_id + ' failed: ' + str(error), file=sys.stderr)
        print('Could not save log file "%s", aborting.' % worker_log_file_path, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        return


def compare_results(main_log_file, settings):
    """
    Runs the Comparator on on settings['input_folder_path']
    and settings['output_folder_path']. Used exclusively by batch.main().

    :param main_log_file: Reference to batch.main()'s log file
    :type main_log_file: file
    :param settings: Reference to batch settings
    :type settings: dict
    :return: 0 when successful, 1 otherwise
    :rtype: int
    """
    main_log_file.write('Running comparator...')
    try:
        comparator = Comparator(settings['input_folder_path'], settings['output_folder_path'], settings['minimum_intersection_ratio'], raise_on_critical_error=False, use_two_circle_intersection_ratio=settings['use_two_circle_intersection_ratio'])
        comparator.run()
    except Exception as exception:
        main_log_file.write('FAILURE\nException: %s\n' % str(exception))
        main_log_file.write('Could not complete comparison, aborting.\n')
        return 1

    failed = len(comparator.failed)
    passed = len(comparator.passed)
    erroneous = len(comparator.erroneous)
    total = failed + passed + erroneous
    main_log_file.write('OK\n')

    comparator.print(main_log_file, True)
    if not settings['quiet_mode']:
        print('\n')
        comparator.print(sys.stdout, False)
        print('See batch log file "%s" for more information.' % str(main_log_file.name))

    return 0


def main(settings):
    """
    Batch main function. Parses the SURs file, distributes locations
    among workers and starts them.

    :param settings: Batch settings
    :type settings: dict
    :return: 0 when successful, 1 otherwise
    :rtype: int
    """
    header = format_header(settings)
    if not settings['quiet_mode']:
        print(header)

    # Initialize
    if not os.path.exists(settings['log_folder_path']):
        try:
            os.makedirs(settings['log_folder_path'])
        except OSError as error:
            print('FAILURE\nException: %s' % str(error))
            print('Could not create log folder "%s", aborting.' % settings['print_folder_path'])
            return 1

    main_log_file_path = settings['log_folder_path'] + settings['log_file_prefix'] + 'batch.log'
    try:
        start_time = time.time()
        with open(main_log_file_path, 'w', 1) as main_log_file:
            main_log_file.write(header + '\n')
            main_log_file.write('Initializing...')
            if not os.path.exists(settings['cache_folder_path']):
                try:
                    os.makedirs(settings['cache_folder_path'])
                except OSError as error:
                    main_log_file.write('FAILURE\nException: %s\n' % str(error))
                    main_log_file.write('Could not create folder "%s", aborting.\n' % settings['cache_folder_path'])
                    return 1
            try:
                if os.path.exists(settings['output_folder_path']):
                    shutil.rmtree(settings['output_folder_path'])
                os.makedirs(settings['output_folder_path'])
            except OSError as error:
                main_log_file.write('FAILURE\nException: %s\n' % str(error))
                main_log_file.write('Could not create folder "%s", aborting.\n' % settings['output_folder_path'])
                return 1
            main_log_file.write('OK\n')

            # Validate factors file unless factors are given
            if not settings['factors']:
                try:
                    main_log_file.write('Validating factors file...')
                    Factors().load_file(settings['factors_file_path'])
                    main_log_file.write('OK\n')
                except Exception as exception:
                    print('Could not validate factors file "%s", aborting.' % settings['factors_file_path'], file=sys.stderr)
                    main_log_file.write('FAILURE\nException: %s\n' % str(exception))
                    main_log_file.write('Could not validate factors file "%s", aborting.\n' % settings['output_folder_path'])
                    return 1

            # Parse SURs file
            main_log_file.write('Parsing SURs file "%s"...' % settings['surs_file_path'])
            try:
                data_file_parser = LocationsFileParser(settings['surs_file_path'])
            except Exception as error:
                main_log_file.write('FAILURE\nException: %s\n' % str(error))
                main_log_file.write('Could not parse SURs file "%s", aborting.\n' % settings['surs_file_path'])
                return 1
            locations = data_file_parser.locations
            total_locations = len(locations)
            if total_locations == 0:
                print('SURs file "%s" is empty, aborting.' % settings['surs_file_path'], file=sys.stderr)
                main_log_file.write('FAILURE')
                main_log_file.write('SURs file "%s" is empty, aborting.' % settings['surs_file_path'])
                return 1
            main_log_file.write('OK, %d location(s)\n' % total_locations)

            # Prepare parallelization
            main_log_file.write('Preparing parallelization...')
            cpu_count = multiprocessing.cpu_count()
            parallel_locations = [{} for i in range(cpu_count)]
            i = 0
            for key in locations.keys():
                parallel_locations[i % cpu_count][key] = locations[key]
                i += 1
            main_log_file.write('OK, distribution: %s\n' % str([len(pl) for pl in parallel_locations]))

            # Start processes
            if not settings['quiet_mode']:
                print('Running %d processes' % cpu_count, end='', flush=True)
            main_log_file.write('Running %d processes...' % cpu_count)
            processes = []
            failed_processes = []
            for i in range(cpu_count):
                processes.append(multiprocessing.Process(target=worker, args=(parallel_locations[i], i, settings, )))
            for process in processes:
                process.start()
            for process in processes:
                process.join()
                if not process.exitcode == 0:
                    failed_processes += [process]
            if len(failed_processes) == 0:
                main_log_file.write('OK\n')
            else:
                main_log_file.write('FAILURE\n')
                main_log_file.write('Failed processes: %s\n' % ', '.join([p.name for p in failed_processes]))
                return 1

            if settings['compare_results']:
                code = compare_results(main_log_file, settings)
                if not code == 0:
                    return code
            else:
                if not settings['quiet_mode']:
                    print()

            end_time = time.time()
            elapsed_time_text = '\nElapsed time: %.2f ms' % ((end_time - start_time) * 1000)
            if not settings['quiet_mode']:
                print(elapsed_time_text)
            main_log_file.write(elapsed_time_text + '\n')
            if not settings['quiet_mode']:
                print()
    except OSError as error:
        print('FAILURE\n')
        print('%s\n' % str(error))
        print('Could not write log file "%s", aborting.\n' % main_log_file_path)
        sys.exit(1)

    return 0

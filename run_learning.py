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

import random
import shutil
import argparse

import batch
from comparator import *
from classifier import *
from factors import *


classifiers_list = get_classifiers_list(None)

def default_settings():
    """
    Returns a dict containing the default settings for learning.

    :return: Default learning settings
    :rtype: dict
    """
    return {
        'max_factor_value': 5,
        'rounds': 20,
        'population': 30,
        'new_population_per_turn': 30,
        'mutations_rate': 0.5,
        'maximum_cache_file_age': 4 * 24 * 60 * 60,
        'overpass_radius': 200,
        'factors_file_path': './data/factors.txt',
        'surs_file_path': './learning/db/surs.txt',
        'cache_folder_path': './cache/',
        'log_folder_path': './log/',
        'db_folder_path': './learning/db/',
        'test_folder_path': './learning/test/',
        'test_surs_file_path': './learning/test/surs.txt',
        'temp_folder_path': './learning/tmp/',
        'use_two_circle_intersection_ratio': False,
        'minimum_intersection_ratio': 0.7,
    }

def main(settings):
    """
    Runs the learning process.

    :param settings: Settings dict like default_learning_settings. Defaults to default_learning_settings
    :type settings: dict
    :return: 0 if success, 1 otherwise
    :rtype: int
    """

    def get_random_number():
        """
        Returns a random number.

        The chance of getting a number between 0-1 is equal to 1-settings['max_factor_value']
        The numbers are uniformly distributed in both ranges.

        :return: Random number between 0 and settings['max_factor_value']
        :rtype: float
        """
        random_num = random.random()
        if random_num < 0.5:
            return random_num * 2
        else:
            return random.uniform(1, settings['max_factor_value'])

    def test_result(batch_settings, learning_settings, winner):
        """
        Tests the accuracy after learning.

        :param batch_settings: The settings used for batch processing. Path will be corrected in the method
        :type batch_settings: Dict from batch.default_settings()
        :param learning_settings: The settings used for learning. Path will be corrected in the method
        :type learning_settings: Dict from batch.default_settings()
        :param batch_settings: The winner of the learning
        :type batch_settings: factors.Factors
        :return: None
        """
        nonlocal main_log_file
        settings = batch_settings.copy()
        settings['surs_file_path'] = learning_settings['test_surs_file_path']
        settings['input_folder_path'] = learning_settings['test_folder_path']
        settings['factors'] = winner
        batch.main(settings)
        try:
            comparator = Comparator(settings['input_folder_path'], settings['output_folder_path'], settings['minimum_intersection_ratio'], raise_on_critical_error=True)
            comparator.run()
        except Exception as exception:
            print('Comparison failed! See log file for more information.')
            main_log_file.write('COMPARISON FAILURE\n')
            main_log_file.write('%s\n' % str(exception))
            main_log_file.write('Can not complete comparison, aborting.\n')
            return 1

        comparator.print(sys.stdout, False)
        comparator.print(main_log_file, False)


    def clear_learning_tmp():
        """
        Deletes temporary files created by processing.

        :return: None
        """
        nonlocal main_log_file
        main_log_file.write('Deleting temporary files...')
        try:
            shutil.rmtree(settings['temp_folder_path'])
            main_log_file.write('OK\n')
        except Exception as error:
            main_log_file.write('FAILURE\n')
            main_log_file.write('%s\n' % str(error))
            main_log_file.write('Can not delete temporary folder "%s", aborting.\n' % settings['temp_folder_path'])
            sys.exit(1)

    #Create header
    header = format_header(settings)
    print(header + '\n')

    # Initialize
    if not os.path.exists(settings['log_folder_path']):
        try:
            os.makedirs(settings['log_folder_path'])
        except OSError as error:
            print('FAILURE')
            print('%s' % str(error))
            print('Can not create log folder "%s", aborting.' % settings['print_folder_path'])
            sys.exit(1)

    # Settings for batch processing
    batch_settings = batch.default_settings()
    batch_settings['surs_file_path'] = settings['surs_file_path']
    batch_settings['input_folder_path'] = settings['db_folder_path']
    batch_settings['output_folder_path'] = settings['temp_folder_path']
    batch_settings['log_folder_path'] = settings['log_folder_path']
    batch_settings['cache_folder_path'] = settings['cache_folder_path']
    batch_settings['force_cache_update'] = True  # Force cache update
    batch_settings['maximum_cache_file_age'] = settings['maximum_cache_file_age']
    batch_settings['overpass_radius'] = settings['overpass_radius']
    batch_settings['minimum_intersection_ratio'] = settings['minimum_intersection_ratio']
    batch_settings['use_two_circle_intersection_ratio'] = settings['use_two_circle_intersection_ratio']
    batch_settings['compare_results'] = False
    batch_settings['quiet_mode'] = True
    batch_settings['log_file_prefix'] = 'learning_'

    main_log_file_path = settings['log_folder_path'] + 'learning.log'
    try:
        with open(main_log_file_path, 'w', 1) as main_log_file:
            main_log_file.write(header + '\n')
            main_log_file.write('Initializing...')
            if not os.path.exists(settings['cache_folder_path']):
                try:
                    os.makedirs(settings['cache_folder_path'])
                except OSError as error:
                    main_log_file.write('FAILURE\n')
                    main_log_file.write('%s\n' % str(error))
                    main_log_file.write('Can not create folder "%s", aborting.\n' % settings['cache_folder_path'])
                    return 1
            if not os.path.exists(settings['temp_folder_path']):
                try:
                    os.makedirs(settings['temp_folder_path'])
                except OSError as error:
                    main_log_file.write('FAILURE\n')
                    main_log_file.write('%s\n' % str(error))
                    main_log_file.write('Can not create folder "%s", aborting.\n' % settings['temp_folder_path'])
                    return 1
            if not os.path.exists(settings['log_folder_path']):
                try:
                    os.makedirs(settings['log_folder_path'])
                except OSError as error:
                    main_log_file.write('FAILURE\n')
                    main_log_file.write('%s\n' % str(error))
                    main_log_file.write('Can not create folder "%s", aborting.\n' % settings['log_folder_path'])
                    return 1
            main_log_file.write('OK\n')

            main_log_file.write('Initializing factors...')
            factor_list = []
            for i in range(0, settings['population']):
                temp_factor = Factors()
                for classifier in classifiers_list:
                    temp_factor.factors[classifier.name()] = get_random_number()
                factor_list.append((temp_factor, None))
            main_log_file.write('OK\n')

            winner = None
            for round in range(settings['rounds']):
                print('Round %i' % (round + 1), end='', flush=True)
                main_log_file.write('Round %i' % (round + 1))

                # New population
                current_population = factor_list.copy()
                result_population = []
                for i in range(0, settings['new_population_per_turn']):
                    parent1 = current_population[random.randint(0, len(current_population) - 1)][0]
                    parent2 = current_population[random.randint(0, len(current_population) - 1)][0]
                    child = Factors()
                    for classifier in classifiers_list:
                        if random.randint(0, 1) == 0:
                            child.factors[classifier.name()] = parent1.factors[classifier.name()]
                        else:
                            child.factors[classifier.name()] = parent2.factors[classifier.name()]
                    # Mutation of children
                    if random.random() < settings['mutations_rate']:
                        child.factors[classifiers_list[random.randint(0, len(classifiers_list) - 1)].name()] = get_random_number()
                    current_population.append((child, None))

                # Processing
                for current_factor in current_population:
                    if current_factor[1] is None:
                        batch_settings['factors'] = current_factor[0]
                        if batch.main(batch_settings) == 1:
                            main_log_file.write(' ERROR - Can not complete batch processing!')
                            print('!', end='', flush=True)
                            result_population.append((current_factor[0], -1.0))
                            continue
                        batch_settings['force_cache_update'] = False

                        try:
                            comparator = Comparator(settings['db_folder_path'], settings['temp_folder_path'], settings['minimum_intersection_ratio'], raise_on_critical_error=True, use_two_circle_intersection_ratio=settings['use_two_circle_intersection_ratio'])
                            comparator.run()
                        except Exception as exception:
                            main_log_file.write(' ERROR - %s!' % str(exception))
                            result_population.append((current_factor[0], -1.0))
                            print('!', end='', flush=True)
                            continue
                        if settings['use_two_circle_intersection_ratio']:
                            passed = len(comparator.passed)
                            points = (passed / (passed + len(comparator.failed) + len(comparator.erroneous))) - (comparator.average_intersection_ratio/100)
                        else:
                            points = comparator.average_intersection_ratio
                        result_population.append((current_factor[0], points))
                        print('.', end='', flush=True)
                        main_log_file.write('.')
                    else:
                        print(':', end='', flush=True)
                        main_log_file.write(':')
                        result_population.append(current_factor)
                result_population.sort(key=lambda x: x[1], reverse=True)
                print('[ ', end='', flush=True)
                main_log_file.write('[ ')
                for tuple in result_population:
                    print('%5.4f ' % tuple[1], end='', flush=True)
                    main_log_file.write('%5.4f ' % tuple[1])
                print(']', end='', flush=True)
                main_log_file.write(']')

                winner = result_population[0][0]
                factor_list = []
                for _ in range(0, settings['population']):
                    factor_list.append(result_population.pop(0))
                print(' OK')
                main_log_file.write(' OK\n')
            print('All rounds complete!')
            main_log_file.write('All rounds complete!\n')
            winner.write_file(settings['factors_file_path'])
            test_result(batch_settings, settings, winner)
            clear_learning_tmp()
    except OSError as error:
        print('FAILURE\n')
        print('%s\n' % str(error))
        print('Can not write log file "%s", aborting.\n' % main_log_file_path)
        return 1

    return 0

def parse_cmd_args():
    """
    Parses the command line arguments and returns a learning settings dict
    :return: Learning settings
    :rtype: dict
    """
    settings = default_settings()

    parser = argparse.ArgumentParser(description='SPtP learning')
    parser.add_argument('-f', '--factor-value', dest='factor_value', help='Maximum value the factors can have. Default: %i' % settings['max_factor_value'], type=int)
    parser.add_argument('-r', '--rounds', dest='rounds', help='Amount of rounds the learning is doing. Default: %i' % settings["rounds"], type=int)
    parser.add_argument('-p', '--population', dest='population', help='Size of population carried from one turn to next turn. Default: %i' % settings['population'], type=int)
    parser.add_argument('-c', '--children', dest='children', help='Amount of children produced in every turn. Default: %i' % settings['new_population_per_turn'], type=int)
    parser.add_argument('-m', '--mutation-rate', dest='mutation_rate', help='Probability of a children changing one factor value. Default: %f' % settings['mutations_rate'], type=float)
    parser.add_argument('--overpass-radius', dest='overpass_radius', help='Overpass API query radius. Default: %i' % settings['overpass_radius'], type=int)
    parser.add_argument('--learning-db', dest='learning_db', help='Path to the folder containing learning data (images + *.truth.kml). Default: %s' % settings['db_folder_path']) # learning-db
    parser.add_argument('--learning-sur-file', dest='learning_sur_file', help='Path to the text file containing the SURs for learning. Default: %s' % settings['surs_file_path']) # lerning-sur
    parser.add_argument('--test-db', dest='test_db', help='Path to the folder containing verification data (images + *.truth.kml). Default: %s' % settings['test_folder_path']) # testdb
    parser.add_argument('--test-sur-file', dest='test_sur_file', help='Path to the text file containing the SURs for verification. Default: %s' % settings['test_surs_file_path']) # #testsur
    parser.add_argument('--temp-output', dest='output_folder', help='Path to the folder that will contain the resulting KML files. This folder will be deleted at the end. Default: %s' % settings['temp_folder_path']) # output
    parser.add_argument('--two-circle-intersection', dest='use_two_circle_intersection_ratio', help='Use two circle intersection ratio method. Default: False', action='store_true')

    args = parser.parse_args()

    if args.factor_value:
        if args.factor_value < 1:
            print('factor_value must be larger or equal to 1')
            sys.exit(0)
        settings['max_factor_value'] = args.factor_value
    if args.rounds:
        if args.rounds < 1:
            print('rounds must be larger or equal to 1')
            sys.exit(0)
        settings['rounds'] = args.rounds
    if args.population:
        if args.population < 1:
            print('population must be larger or equal to 1')
            sys.exit(0)
        settings['population'] = args.population
    if args.children:
        if args.children < 1:
            print('children must be larger or equal to 1')
            sys.exit(0)
        settings['new_population_per_turn'] = args.children
    if args.mutation_rate:
        if not (0.0 <= args.mutation_rate <= 1.0):
            print('mutation_rate must be between 0.0 and 1.0')
            sys.exit(0)
        settings['mutations_rate'] = args.mutation_rate
    if args.overpass_radius:
        settings['overpass_radius'] = args.overpass_radius
    if args.learning_db:
        settings['db_folder_path'] = args.learning_db
    if args.learning_sur_file:
        settings['surs_file_path'] = args.learning_sur_file
    if args.test_db:
        settings['test_folder_path'] = args.test_db
    if args.test_sur_file:
        settings['test_surs_file_path'] = args.test_sur_file
    if args.output_folder:
        output_folder = args.output_folder
        if output_folder[-1] is not os.path.sep:
            output_folder += os.path.sep
        settings['temp_folder_path'] = output_folder
    if args.use_two_circle_intersection_ratio:
        settings['use_two_circle_intersection_ratio'] = args.use_two_circle_intersection_ratio

    return settings

def format_header(settings):
    """
    Creates a printable header from learning settings.

    :param settings: Learning settings
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

    header = "SPtP - Learning\n-----------------------\n\n"
    header += item('Maximum factor value', settings['max_factor_value'])
    header += item('Rounds', settings['rounds'])
    header += item('Population', settings['population'])
    header += item('Children', settings['new_population_per_turn'])
    header += item('Mutation rate', settings['mutations_rate'])
    header += item('Overpass radius [m]', settings['overpass_radius'])
    header += item('Learning database path', settings['db_folder_path'])
    header += item('Learning SUR file path', settings['surs_file_path'])
    header += item('Verification database path', settings['test_folder_path'])
    header += item('Verification SUR file path', settings['test_surs_file_path'])
    header += item('Temporary output path', settings['temp_folder_path'])
    return header

if __name__ == '__main__':
    learning_settings = parse_cmd_args()
    try:
        exit_code = main(learning_settings)
        if exit_code == 0:
            print('Learning finished successfully.')
        else:
            print('Learning failed. Check log files for details.')
    except KeyboardInterrupt:
        print('\nAborted')
        sys.exit(0)

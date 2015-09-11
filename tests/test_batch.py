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

import unittest
import shutil
import subprocess
import os

class TestBatch(unittest.TestCase):
    def setUp(self):
        self.std = []
        os.chdir('./tests/batch_test_files/')

    def run_batch(self, parameters):
        process = subprocess.Popen(['python3', '../../run_batch.py', '-q'] + parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = process.communicate()
        self.std += ['%s -> %s || %s' % (str(parameters), str(stdout_data), str(stderr_data))]
        return process.returncode

    def test_file_output(self):
        self.assertEqual(0, self.run_batch(['--skip-cache-update']))
        self.assertTrue(os.path.isfile('./output/0001.computed.kml'), 'Missing KML file from output')
        self.assertTrue(os.path.isfile('./output/0001.jpg'), 'Missing image file from output')
        self.assertTrue(os.path.isfile('./output/0001.json'), 'Missing JSON file from output')
        self.assertFalse(os.path.isfile('./output/0001.csv'), 'CSV file should not be there')

    def test_file_output_debug(self):
        self.assertEqual(0, self.run_batch(['--skip-cache-update', '--debug-output']))
        self.assertTrue(os.path.isfile('./output/0001.computed.kml'), 'Missing KML file from output')
        self.assertTrue(os.path.isfile('./output/0001.jpg'), 'Missing image file from output')
        self.assertTrue(os.path.isfile('./output/0001.json'), 'Missing JSON file from output')
        self.assertTrue(os.path.isfile('./output/0001.points.csv'), 'Missing CSV file from output')

    def tearDown(self):
        if os.path.exists('./log'):
            shutil.rmtree('./log')
        if os.path.exists('./output'):
            shutil.rmtree('./output')
        os.chdir('..')
        os.chdir('..')
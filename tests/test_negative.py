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
import unittest
import shutil
import subprocess


class TestNegative(unittest.TestCase):
    def setUp(self):
        self.std = []
        os.chdir('./tests/')

    def run_batch(self, parameters):
        process = subprocess.Popen(['python3', '../run_batch.py', '-q'] + parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = process.communicate()
        self.std += ['%s -> %s || %s' % (str(parameters), str(stdout_data), str(stderr_data))]
        return process.returncode

    def test_bitflip(self):
        self.assertEqual(1, self.run_batch(['-f=./negative/bitflip/factors.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/bitflip', '-s=./negative/valid_surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/bitflip', '-f=./negative/valid_factors.txt', '-s=./negative/valid_surs.txt', '--skip-cache-update']))

    def test_empty_file(self):
        self.assertEqual(1, self.run_batch(['-f=./negative/empty_file/factors.txt']))
        self.assertEqual(1, self.run_batch(['-f=./negative/empty_file/surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/empty_file', '-s=./negative/valid_surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/empty_file', '-f=./negative/valid_factors.txt', '-s=./negative/valid_surs.txt', '--skip-cache-update']))

    def test_missing_block(self):
        self.assertEqual(1, self.run_batch(['-f=./negative/missing_block/factors.txt']))
        self.assertEqual(1, self.run_batch(['-f=./negative/missing_block/surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/missing_block', '-s=./negative/valid_surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/missing_block', '-f=./negative/valid_factors.txt', '-s=./negative/valid_surs.txt', '--skip-cache-update']))

    def test_other_file(self):
        self.assertEqual(1, self.run_batch(['-f=./negative/other_file/factors.txt']))
        self.assertEqual(1, self.run_batch(['-f=./negative/other_file/surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/other_file', '-s=./negative/valid_surs.txt']))
        self.assertEqual(1, self.run_batch(['-i=./negative/other_file', '-f=./negative/valid_factors.txt', '-s=./negative/valid_surs.txt', '--skip-cache-update']))

    def test_invalid_images(self):
        self.assertEqual(1, self.run_batch(['-i=./negative/invalid_images', '-f=./negative/valid_factors.txt', '-s=./negative/invalid_images/surs.txt']))

    def tearDown(self):
        if os.path.exists('./cache'):
            shutil.rmtree('./cache')
        if os.path.exists('./log'):
            shutil.rmtree('./log')
        if os.path.exists('./output'):
            shutil.rmtree('./output')
        os.chdir('..')
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 gr-doa author.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import testbench
from beamform_1d import beamform_1d

class qa_beamform_1d(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        resolution = 128
        theta_min = 0
        theta_max = 180
        num_samples = 512


        antennas = testbench.square_array(.5)[:,1:]

        [powers, Rxx] = testbench.beamform_testbench(antennas, num_samples, resolution, 

        # set up fg
        self.tb.run()
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_beamform_1d)

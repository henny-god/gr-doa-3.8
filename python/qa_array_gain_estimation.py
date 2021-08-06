#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Henry Pick.
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
from array_gain_estimation import array_gain_estimation
import numpy as np
import testbench

class qa_array_gain_estimation(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        # set up fg

        array_config = '../../python/testbench/square.conf'
        pilot_theta = np.deg2rad(90)
        pilot_phi = np.deg2rad(75)

        antennas = testbench.read_array_config(4, array_config)

        self.array_gain_estimation = array_gain_estimation(len(antennas), array_config, pilot_theta, pilot_phi)
        self.vector_source = blocks.vector_source_c(data=

        self.tb.run()
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_array_gain_estimation)

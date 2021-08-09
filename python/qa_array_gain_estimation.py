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

        snr = 5
        
        antennas = testbench.read_array_config(4, array_config)

        gamma = np.diag((1, np.exp(-1j*np.pi/45), 1, 1)) # perturb the second antenna by 45 degrees
        gamma[1, 1] = 1

        x = testbench.channel_model(antennas, [[pilot_theta, pilot_phi]], [1], 512, snr)

        x = np.dot(gamma, x)

        Rxx = testbench.autocorrelate(x)

        self.array_gain_estimation = array_gain_estimation(len(antennas), array_config, pilot_theta, pilot_phi)
        self.vector_source = blocks.vector_source_c(data=Rxx.flatten(), vlen=len(antennas)**2, repeat=False)
        self.vector_sink = blocks.vector_sink_c(vlen=len(antennas))

        self.tb.connect((self.vector_source, 0), (self.array_gain_estimation, 0))
        self.tb.connect((self.array_gain_estimation, 0), (self.vector_sink, 0))

        self.tb.run()
        # check data
        observed_data = self.vector_sink.data()
        print(observed_data)
        print(np.diag(gamma))


if __name__ == '__main__':
    gr_unittest.run(qa_array_gain_estimation)

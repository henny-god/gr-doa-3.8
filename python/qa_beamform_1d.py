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
import numpy as np
import matplotlib.pyplot as plt

class qa_beamform_1d(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        resolution = 512
        theta = np.deg2rad(130)
        num_samples = 512
        capon = 1
        array_config = '../../python/testbench/linear_6.conf'


        antennas = testbench.read_array_config(6, array_config)

        [testbench_powers, Rxx] = testbench.beamform_1d_testbench(antennas, num_samples, resolution, theta, 10, capon)

        self.beamform_1d = beamform_1d(len(antennas), resolution, array_config, capon, 0, np.pi, np.pi/2)
        self.vec_source = blocks.vector_source_c(data=Rxx.flatten(), repeat=False, vlen=len(antennas)*len(antennas))
        self.vec_sink = blocks.vector_sink_f(resolution)

        self.tb.connect((self.vec_source, 0), (self.beamform_1d, 0))
        self.tb.connect((self.beamform_1d, 0), (self.vec_sink, 0))


        # set up fg
        self.tb.run()
        # check data

        observed_powers = self.vec_sink.data()
        self.assertTrue(np.max(np.abs(observed_powers - testbench_powers)) < 1e-4)

if __name__ == '__main__':
    gr_unittest.run(qa_beamform_1d)

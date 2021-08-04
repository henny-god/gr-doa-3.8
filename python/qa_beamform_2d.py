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
import numpy as np
import testbench
import matplotlib.pyplot as plt
from beamform_2d import beamform_2d

class qa_beamform_2d(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        resolution = 128
        angles = np.deg2rad([[90, 90]])
        amplitudes = [1]
        num_samples = 512
        capon = 1
        array_config = '../../python/testbench/square.conf'
        snr = 10

        # antennas load correctly
        antennas = testbench.read_array_config(4, array_config)

        [testbench_powers, Rxx] = testbench.beamform_2d_testbench(antennas, num_samples, resolution, angles, amplitudes, snr, capon)

        self.beamform_2d = beamform_2d(len(antennas), resolution, array_config, capon, 0, np.pi, 0, 2*np.pi)

        self.vec_source = blocks.vector_source_c(data=Rxx.flatten(), repeat=False, vlen=len(antennas)*len(antennas))
        self.vec_sink = blocks.vector_sink_b(resolution * resolution*2)


        self.tb.connect((self.vec_source, 0), (self.beamform_2d, 0))
        self.tb.connect((self.beamform_2d, 0), (self.vec_sink, 0))

        # set up fg
        self.tb.run()
        # check data
        observed_powers = self.vec_sink.data()
        self.assertTrue(np.max(np.abs(testbench_powers.flatten() - observed_powers)) < 1.1)

if __name__ == '__main__':
    gr_unittest.run(qa_beamform_2d)

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
from music_1d import music_1d

import testbench

import numpy as np
import matplotlib.pyplot as plt

class qa_music_1d(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):

        resolution = 512
        phi = np.deg2rad(120)
        num_samples = 512
        snr = 10
        array_config = '../../python/testbench/linear_6.conf'

        antennas = testbench.read_array_config(6, array_config)

        [testbench_powers, Rxx] = testbench.music_1d_testbench(antennas, num_samples, resolution, phi, snr)

        self.music_1d = music_1d(len(antennas), 1, resolution, array_config, 0, np.pi, np.pi/2)
        self.vec_source = blocks.vector_source_c(data=Rxx.flatten(), repeat=False, vlen=len(antennas)*len(antennas))
        self.vec_sink = blocks.vector_sink_f(vlen=resolution)

        self.tb.connect((self.vec_source, 0), (self.music_1d, 0))
        self.tb.connect((self.music_1d, 0), (self.vec_sink, 0))

        # set up fg
        self.tb.run()
        observed_powers = self.vec_sink.data()

        self.assertTrue(np.max(np.abs(observed_powers - testbench_powers)) < .01)
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_music_1d)

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
from music_2d import music_2d

import testbench
import numpy as np
import matplotlib.pyplot as plt

class qa_music_2d(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        # set up fg
        resolution = 128
        angles = np.deg2rad((118, 270))
        num_samples = 512
        snr = 10
        array_config = '../../python/testbench/square.conf'

        antennas = testbench.read_array_config(4, array_config)

        [testbench_music, Rxx] = testbench.music_2d_testbench(antennas, num_samples, resolution, angles, snr)

        self.music_2d = music_2d(len(antennas), 1, resolution, array_config, 0, np.pi, 0, 2*np.pi)
        self.vec_source = blocks.vector_source_c(data=Rxx.flatten(), repeat=False, vlen=int(len(antennas)**2))
        self.vec_sink = blocks.vector_sink_b(vlen=int(resolution**2*2))

        self.tb.connect((self.vec_source, 0), (self.music_2d, 0))
        self.tb.connect((self.music_2d, 0), (self.vec_sink))

        # run
        self.tb.run()
        observed_music = self.vec_sink.data()

        self.assertTrue(np.max(np.abs(observed_music - testbench_music.flatten())) < 1.1)

if __name__ == '__main__':
    gr_unittest.run(qa_music_2d)

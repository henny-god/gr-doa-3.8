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
import doa_swig as doa
import testbench

class qa_beamform(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        # some input phases
        norm_spacing = 0.5
        num_antennas = 4
        resolution = 16
        array_type = 0 # linear array
        theta = 45
        phi = 23

        [beamform_matrix, phases] = testbench.autocorrelation_testbench(norm_spacing, num_antennas, resolution, theta, phi)
        beamform_matrix = beamform_matrix.flatten()

        self.doa_beamform = doa.beamform(norm_spacing, num_antennas, resolution, array_type)
        self.vec_sink = blocks.vector_sink_c(resolution*resolution*2)

        # setup inputs
        for p in range(num_antennas):
            # add vector source, assign to each element in the data matrix
            object_name_vs = 'vec_source_'+str(p)
            setattr(self, object_name_vs, blocks.vector_source_f(data=phases[p].tolist(), repeat=False))
            # connect
            self.tb.connect((getattr(self, object_name_vs), 0), (self.doa_beamform, p))
        self.tb.connect((self.doa_beamform, 0), (self.vec_sink, 0))
        
        # set up fg
        self.tb.run()
        observed_beamform = self.vec_sink.data()

        # check data
        beamform_matrix = beamform_matrix.flatten()
        for i in range(resolution*resolution*2):
            self.assertTrue(abs(beamform_matrix[i] - observed_beamform[i]) > .1)



if __name__ == '__main__':
    gr_unittest.run(qa_beamform)

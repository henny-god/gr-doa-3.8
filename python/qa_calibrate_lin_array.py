#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2016 
# Srikanth Pagadarai<srikanth.pagadarai@gmail.com>
# Travis Collins<travisfcollins@gmail.com>.	
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
import itertools
import numpy as np
import testbench
import os

class qa_calibrate_lin_array (gr_unittest.TestCase):

	def setUp (self):
                self.tb = gr.top_block ()

	def tearDown (self):
		self.tb = None

	def test_001_t (self):	       
                config_file = '../../python/testbench/square.conf'
                pilot_angles = np.deg2rad([[90, 115]])
                pilot_mags = [1]
                print(pilot_angles)
                print(pilot_mags)
                resolution = 128
                num_samps = int(2**13)
                snr = 10


                antennas = testbench.read_array_config(4, config_file)


                x = testbench.channel_model(antennas, pilot_angles, pilot_mags, num_samps, snr)
                gamma = np.diag(np.random.uniform(0, 1, len(antennas))*np.exp(1j*np.random.uniform(-np.pi, np.pi, len(antennas))))
                x_p = np.dot(gamma, x) # x perturbed

                R_xx_p = testbench.autocorrelate(x_p)

                self.vec_source = blocks.vector_source_c(data=R_xx_p.flatten(), repeat=False, vlen=int(len(antennas)**2))
                self.vec_sink = blocks.vector_sink_c(vlen=len(antennas))
                self.estimate_offset = doa.calibrate_lin_array(len(antennas), config_file, pilot_angles[0, 0], pilot_angles[0,1])

                self.tb.connect((self.vec_source, 0), (self.estimate_offset, 0))
                self.tb.connect((self.estimate_offset, 0), (self.vec_sink, 0))


                self.tb.run()

                observed_gamma = self.vec_sink.data()

                print(gamma)
                print(observed_gamma)

                return
 
if __name__ == '__main__':
    gr_unittest.run(qa_calibrate_lin_array, "qa_calibrate_lin_array.xml")

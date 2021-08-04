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


import numpy as np
import math
import sys
from gnuradio import gr

class beamform_1d(gr.sync_block):
    """
    docstring for block beamform_1d
    """
    def __init__(self, num_antennas, resolution, array_config, capon, phi_min, phi_max, theta):
        gr.sync_block.__init__(self,
            name="beamform_1d",
            in_sig=[(np.csingle, num_antennas*num_antennas), ],
            out_sig=[(np.single, resolution), ])

        self.resolution = resolution
        self.num_antennas = num_antennas
        self.capon = capon
        self.phi_min = phi_min
        self.phi_max = phi_max
        self.theta = theta

        self.amvs = np.empty((resolution, num_antennas), dtype=complex)

        # parse config file and put positions into array
        self.array = np.ndarray((num_antennas, 3), dtype=np.single)
        try:
            file = open(array_config, 'r')
            file.close()
        except:
            sys.stderr.write("Configuration "+ array_config +", not valid\n")
            print(sys.stderr)
            sys.exit(1)
        file = open(array_config, 'r')
        lines = file.readlines()
        file.close()
        if len(lines) < num_antennas*3:
            raise ValueError("Number of antennas specified in config file is too small")
        elif len(lines) > num_antennas*3:
            raise ValueError("Number of antennas specified in config file is too large")
        for i in range(num_antennas):
            self.array[i][0] = float(lines[3*i])
            self.array[i][1] = float(lines[3*i+1])
            self.array[i][2] = float(lines[3*i+2])

        # setup amv lookup table
        # just for standardization, we set theta as our sweeping angle and hold phi constant
        for i in range(self.resolution):
            phi = float(i) / resolution * (phi_max - phi_min) + phi_min
            wave_vector = np.array([math.sin(self.theta)*math.cos(phi), math.sin(self.theta)*math.sin(phi), math.cos(self.theta)])
            self.amvs[i] = np.exp(2j*math.pi*np.array(np.dot(self.array - self.array[0], wave_vector)))

        # if not capon beamforming, we normalize the weight vectors by the number of antennas
        if not self.capon:
            self.amvs = self.amvs / np.sqrt(self.num_antennas)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        for item in range(len(output_items[0])):
            Rxx = np.array(in0[item]).reshape(self.num_antennas, self.num_antennas)
            # we have already applied normalization in the constructor
            # the numpy syntax using einsum actually has a purpose here. Speeds up the matrix processing by a factor of 70 or so
            if self.capon:
                Rinv = np.linalg.inv(Rxx)
                out[item] = 10*np.log10(1/np.einsum('ay, ay->a', np.conj(self.amvs), np.einsum('ay,xy->xa', Rinv, self.amvs)).real)
            else:
                out[item] = 10*np.log10(np.einsum('ay, ay->a', np.conj(self.amvs), np.einsum('ay,xy->xa', Rxx, self.amvs)).real)
            
        return len(output_items[0])

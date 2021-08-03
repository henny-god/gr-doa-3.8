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
    def __init__(self, num_antennas, resolution, array_config, capon, theta_min, theta_max):
        gr.sync_block.__init__(self,
            name="beamform_1d",
            in_sig=[np.csingle],
            out_sig=[np.single])

        self.resolution = resolution
        self.num_antennas = num_antennas
        self.capon = capon
        self.theta_min = theta_min
        self.theta_max = theta_max

        self.amvs = np.empty((resolution, num_antennas), dtype=complex)

        # parse config file and put positions into array
        self.array = np.array((num_antennas, 2), dtype=np.single)
        try:
            file = open(array_config, 'r')
            file.close()
        except:
            sys.stderr.write("Configuration "+ array_config +", not valid\n")
            print(sys.stderr)
            sys.exit(1)
        file = open(array_config, 'r')
        lines = file.readlines()
        if len(lines) < num_antennas*2:
            raise ValueError("Number of antennas specified in config file is too small")
        elif len(lines) > num_antennas*2:
            raise ValueError("Number of antennas specified in config file is too large")
        for i in range(num_antennas):
            self.array[2*i][0] = float(lines[2*i])
            self.array[2*i][1] = float(lines[2*i])

        # setup amv lookup table
        for i in range(self.resolution):
            theta = float(i) / resolution * (theta_max - theta_min) + theta_min
            wave_vector = np.array([math.cos(theta), math.sin(theta)])
            self.amvs [i] = np.exp(-2j*math.pi*np.array(np.dot(self.array[i], wave_vector)))

        if self.capon:
            self.amvs = self.amvs / self.num_antennas

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        for item in range(output_items):
            Rxx = np.array(in0[item*self.num_antennas*self.num_antennas:(item + 1)*self.num_antennas*self.num_antennas]).reshape(self.num_antennas, self.num_antennas)

            # we have already applied normalization in the constructor
            # the numpy syntax using einsum actually has a purpose here. Speeds up the matrix processing by a factor of 70 or so
            if self.capon:
                Rxxinv = np.linalg.inv(Rxx)
                out[item*self.resolution:(item+1)*self.resolution] = np.log10((1/np.einsum('xyz , xyz-> xy', np.conj(self.amvs), np.einsum('az, xyz->xya', Rxxinv, self.amvs)).real).flatten)
            else:
                out[item*self.resolution:(item+1)*self.resolution] = np.log10((1/np.einsum('xyz, xyz->xy', np.conj(self.amvs), np.einsum('az, xyz->xya', Rxx, self.amvs)).real).flatten)
            
        return len(output_items[0])

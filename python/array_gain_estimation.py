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


import numpy as np
import sys
from gnuradio import gr

class array_gain_estimation(gr.sync_block):
    """
    docstring for block array_gain_estimation
    """
    def __init__(self, num_antennas, array_config, pilot_theta, pilot_phi):
        gr.sync_block.__init__(self,
            name="array_gain_estimation",
            in_sig=[(np.csingle, num_antennas*num_antennas), ],
            out_sig=[(np.csingle, num_antennas), ])
        self.num_antennas = num_antennas
        self.pilot_phi = pilot_phi
        self.pilot_theta = pilot_theta

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

        wave_vector = np.array([np.sin(pilot_theta)*np.cos(pilot_phi), np.sin(pilot_theta)*np.sin(pilot_phi), np.cos(pilot_theta)])
        # a diagonal matrix whose diagonals are the amv for this array
        self.D = np.diag(np.exp(-2j*np.pi*np.dot(self.array, wave_vector)))

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        for item in range(len(in0)):
            Rxx = np.ndarray(in0[item], (self.num_antennas, self.num_antennas))

            [evals_Rxx, evecs_Rxx] = np.linalg.eigh(Rxx)
            evecs_Rxx = evecs_Rxx[:,np.argsort(evals_Rxx)]

            E = evecs_Rxx[:, self.num_antennas - 1]

            E_sq = np.outer(E, np.conj(E))

            W = np.dot(np.conj(self.D.T), np.dot(E_sq, self.D))

            [evals_W, evecs_W] = np.linalg.eigh(W)
            evecs_W = evecs_W[:,np.argsort(evals_W)]

            out[item] = evecs_W[:,self.num_antennas-1]

        return len(output_items[0])


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

class music_2d(gr.sync_block):
    """
    docstring for block music_2d
    """
    def __init__(self, num_antennas: int, num_signals: int, resolution: int, array_config: str, theta_min: float, theta_max: float, phi_min: float, phi_max: float):
        gr.sync_block.__init__(self,
            name="music_2d",
            in_sig=[(np.csingle, num_antennas*num_antennas), ],
            out_sig=[(np.byte, int(resolution**2*2)), ])

        self.num_antennas = num_antennas
        self.num_signals = num_signals
        self.resolution = resolution

        self.amvs = np.ndarray((resolution, 2*resolution, num_antennas), dtype=np.csingle)

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

        for i in range(self.resolution):
            theta = float(i) / resolution * (theta_max - theta_min) + theta_min
            for j in range(self.resolution*2):
                phi = float(j) / resolution / 2 * (phi_max - phi_min) + phi_min
                wave_vector = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
                self.amvs[i][j] = np.exp(2j*np.pi*np.array(np.dot(self.array - self.array[0], wave_vector)))

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        for item in range(len(output_items[0])):
            Rxx = np.array(in0[item].reshape(self.num_antennas, self.num_antennas))

            [evals, evecs] = np.linalg.eigh(Rxx)
            V = evecs[:, :-self.num_signals]
            V_sq = np.dot(V, np.conj(V.T))
            output = 10*np.log10(1/np.einsum('xyz, xyz->xy', np.conj(self.amvs), np.einsum('az, xyz->xya', V_sq, self.amvs)).real).flatten()
            output_min = np.min(output)
            out[item] = (output - output_min)/(np.max(output) - output_min)* 255
        return len(output_items[0])


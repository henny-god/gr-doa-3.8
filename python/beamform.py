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
import math
from gnuradio import gr



class beamform(gr.sync_block):
    """
    docstring for block beamform
    """
    def __init__(self, norm_spacing: float, num_antennas: int, resolution: int, array_type: str):
        gr.sync_block.__init__(self,
            name="beamform",
            in_sig=[(np.single, num_antennas)],
            out_sig=[np.byte])
        self.norm_spacing = norm_spacing
        self.num_antennas = num_antennas
        self.array_type = array_type # may not be needed after this
        self.resolution = resolution
        self.antennas = np.ndarray

        # display coordinates
        self.phi = 0
        self.theta = 0
        self.flag = True

        if array_type == 'square':
            assert(self.num_antennas == 4)
            self.antennas = self.square_array()

        if array_type == 'linear':
            self.antennas = self.lin_array()
        else:
            self.antennas = self.lin_array()
                

    def antenna_distances(self):
        ret = np.ndarray((self.num_antennas, self.num_antennas), dtype=float)
        for i in range(self.num_antennas):
            for j in range(self.num_antennas):
                ret[i][j] = np.linalg.norm(self.antennas[i] - self.antennas[j])
        return ret

    def lin_array(self):
        distances = np.ndarray((self.num_antennas, 3), dtype=float)

        for i in range(self.num_antennas):
            distances[i,:] = np.array((0, 0, i*self.norm_spacing - (self.num_antennas - 1)*self.norm_spacing/2))
        return distances

    def square_array(self):
        return np.array([[-self.norm_spacing/2, -self.norm_spacing/2, 0], [-self.norm_spacing/2, self.norm_spacing/2, 0], [self.norm_spacing/2, -self.norm_spacing/2, 0], [self.norm_spacing/2, self.norm_spacing/2, 0]])

    def tetra_array(self):
        return np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]])

    def delta_distances(self, theta, phi):
        '''
        computes the phase offset between antennas based on their physical locations and the angle of arrival of the signal
        '''

        # compute signal vector from theta and phi
        n = [math.sin(theta)*math.cos(phi), math.sin(theta)*math.sin(phi), math.cos(theta)]
        ret = np.ndarray((self.num_antennas, self.num_antennas), dtype=float)

        # the phase distance between each element in the array is just the dot product
        # between the distance 
        for i in range(self.num_antennas):
            for j in range(self.num_antennas):
                ret[i][j] = -np.dot(n, self.antennas[i] - self.antennas[j])
        return ret
                
    def distance_error(self, input_vec, theta, phi):
        '''
Compute the error between a vector of signal phase differences and generated vector of phases for a signal arriving at angle theta, phi
        '''

        source_dist = self.delta_distances(theta, phi)
        expected_dist = self.phase_dist_matrix(input_vec)

        # TODO: need to normalize error for the gnuradio video sink block
        error = np.linalg.norm(source_dist - expected_dist)**2
        # normalize so we are on
        return error

    def phase_dist_matrix(self, input_vec):
        '''
        Calculate the pairwise phase distances between elements in the incoming signal vector
        '''
        ret = np.ndarray((self.num_antennas, self.num_antennas), dtype=float)
        for i in range(self.num_antennas):
            for j in range(self.num_antennas):
                ret[i][j] = input_vec[i] - input_vec[j]
        return ret


    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        for i in range(len(in0)):


            if self.phi == self.resolution*2:
                self.phi = 0
                self.theta = self.theta + 1
            if self.theta == self.resolution:
                self.theta = 0
                    
            phi_ang = self.phi * 360/self.resolution/180*math.pi
            theta_ang = self.theta * 180/self.resolution/180*math.pi
            out[i] = self.distance_error(in0[i], theta_ang, phi_ang)
                    
            self.phi = self.phi+1

        return len(out)


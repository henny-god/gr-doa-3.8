/* -*- c++ -*- */
/*
 * Copyright 2021 Henry Pick.
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#include <cassert>
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#define MAT_NORM 24 // normalization calculated empirically

#include <gnuradio/io_signature.h>
#include "beamform_impl.h"
#include <gsl/gsl_matrix_float.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>

namespace gr {
  namespace doa {

    beamform::sptr
    beamform::make(float norm_spacing, int num_antennas, int resolution, int array_type)
    {
      return gnuradio::get_initial_sptr
        (new beamform_impl(norm_spacing, num_antennas, resolution, array_type));
    }


    /*
     * The private constructor
     */
    beamform_impl::beamform_impl(float norm_spacing, int num_antennas, int resolution, int array_type)
      : gr::sync_block("beamform",
		       gr::io_signature::make(num_antennas, num_antennas, sizeof(float)),
		       gr::io_signature::make(1, 1, resolution*resolution*2*sizeof(char))),
	d_norm_spacing(norm_spacing),
	d_num_antennas(num_antennas),
	d_array_type(array_type),
	d_resolution(resolution)
    {
      
      if(!array_type) { // linear array
	d_antenna_positions = new float[num_antennas*3];
	for(int i = 0; i < num_antennas; i++) {
	  d_antenna_positions[i*3] = 0;
	  d_antenna_positions[i*3+1] = 0;
	  d_antenna_positions[i*3+2] = i*d_norm_spacing - (d_num_antennas-1)*d_norm_spacing/2.0;
	}
	
      } else {
	// square array
	assert(d_num_antennas == 4);
	d_antenna_positions = new float[12];

	// don't know if there's an easier way to do this
	d_antenna_positions[0] = -norm_spacing/2;
	d_antenna_positions[1] = -norm_spacing/2;
	d_antenna_positions[2] =  0;
	d_antenna_positions[3] = -norm_spacing/2;
	d_antenna_positions[4] = norm_spacing/2;
	d_antenna_positions[5] = 0;
	d_antenna_positions[6] = norm_spacing/2;
	d_antenna_positions[7] = -norm_spacing/2;
	d_antenna_positions[8] = 0;
	d_antenna_positions[9] = norm_spacing/2;
	d_antenna_positions[10] = norm_spacing/2;
	d_antenna_positions[11] = 0;
      }

      // generate a LUT for expected phases based on angles
      d_angle_phase_lut = new float[d_num_antennas*d_num_antennas*resolution*resolution*2]; // for each theta and phi, store d_num_antennas*d_num_antennas floats corresponding to pairwise phase offsets
      float *wave_arr = new float[3];
      float *diff_arr = new float[3];
      for(int i = 0; i < resolution; i++) {
	float theta = i*M_PI/resolution;
	for(int j = 0; j < 2*resolution; j++) {
	  float phi =  j*M_PI/resolution;
	  // wave vector
	  wave_arr[0] = sin(theta)*cos(phi);
	  wave_arr[1] = sin(theta)*sin(phi);
	  wave_arr[2] = cos(theta);
	  
	  for(int a = 0; a < d_num_antennas; a++) {
	    // dot producte with wave vector and antenna vector is the phase difference between antenna 0 and antenna k
	    float *antenna_a_pos = d_antenna_positions + a*3;
	    for(int b = 0; b < d_num_antennas; b++) {
	      float *antenna_b_pos = d_antenna_positions + b*3;
	      diff_arr[0] = antenna_b_pos[0] - antenna_a_pos[0];
	      diff_arr[1] = antenna_b_pos[1] - antenna_a_pos[1];
	      diff_arr[2] = antenna_b_pos[2] - antenna_a_pos[2];
	      // TODO: make sure that these have the right sign
	      d_angle_phase_lut[d_num_antennas*d_num_antennas*(i*2*d_resolution + j) + a*d_num_antennas + b] = diff_arr[0] * wave_arr[0] + diff_arr[1]*wave_arr[1] + diff_arr[2]*wave_arr[2];
	    }
	  }
	}
      }
      delete[] wave_arr;
      delete[] diff_arr;
    }

    /*
     * Our virtual destructor.
     */
    beamform_impl::~beamform_impl()
    {
      delete[] d_antenna_positions;
      delete[] d_angle_phase_lut;
    }

    int
    beamform_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const float *in = (const float *) input_items[0];
      char *out = (char *) output_items[0];

      gsl_matrix_float *phase_diff_m = gsl_matrix_float_alloc(d_num_antennas, d_num_antennas);

      for (int n_item = 0; n_item < noutput_items; n_item++) {
	// form input phase difference matrix
	for(int i = 0; i < d_num_antennas; i++) {
	  for(int j = 0; j < d_num_antennas; j++) {
	    gsl_matrix_float_set(phase_diff_m, i, j, *((float*)input_items[j] + n_item) - *((float*)input_items[i] + n_item));
	  }
	}

	gsl_matrix_float *error_mat = gsl_matrix_float_alloc(d_num_antennas, d_num_antennas);

	for(int i = 0; i < d_resolution; i++) {
	  for(int j = 0; j < 2*d_resolution; j++) {
	    // look up the phase vector corresponding to theta and phi
	    gsl_matrix_float_view lut_diff_m = gsl_matrix_float_view_array(d_angle_phase_lut + d_num_antennas*d_num_antennas*(i*2*d_resolution + j), d_num_antennas, d_num_antennas);

	    // copy phase differences into out location and map an array onto that block
	    gsl_matrix_float_memcpy(error_mat, phase_diff_m);

	    // compute the normalized difference between the two matrices
	    gsl_matrix_float_sub(error_mat, &lut_diff_m.matrix);
	    out[n_item*d_resolution * d_resolution*2 + i*2*d_resolution + j] = frobenius_norm_mat(error_mat);
	  }
	}
	gsl_matrix_float_free(error_mat);
      }

      // Tell runtime system how many output items we produced.
      gsl_matrix_float_free(phase_diff_m);
      return noutput_items;
    }

    char beamform_impl::frobenius_norm_mat(gsl_matrix_float* mat) {
      float sum = 0;
      for (int i = 0; i < d_num_antennas; i++) {
	for (int j = 0; j < d_num_antennas; j++) {
	  sum += pow(gsl_matrix_float_get(mat, i, j), 2.0);
	}
      }
      sum *= MAT_NORM;
      if (sum > UCHAR_MAX)
	return UCHAR_MAX;
      else
	return (char)sum;
    }
  } /* namespace doa */
} /* namespace gr */

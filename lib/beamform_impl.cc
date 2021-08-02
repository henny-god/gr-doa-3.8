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

#include <gsl/gsl_cblas.h>
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#define MAT_NORM 24 // normalization calculated empirically

#include <gnuradio/io_signature.h>
#include "beamform_impl.h"

#include <gsl/gsl_matrix_float.h>
#include <gsl/gsl_vector_complex_float.h>
#include <gsl/gsl_complex_math.h>
#include <gsl/gsl_blas.h>
#include <gsl/gsl_linalg.h>

#include <string.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <fstream>

namespace gr {
  namespace doa {

    beamform::sptr
    beamform::make(int num_antennas, int resolution, char *array_config, int capon)
    {
      return gnuradio::get_initial_sptr
        (new beamform_impl(num_antennas, resolution, array_config, capon));
    }


    /*
     * The private constructor
     */
    beamform_impl::beamform_impl(int num_antennas, int resolution, char *array_config, int capon)
      : gr::sync_block("beamform",
		       gr::io_signature::make(1, 1, sizeof(float)*num_antennas*num_antennas),
		       gr::io_signature::make(1, 1, resolution*resolution*2*sizeof(char))),
	d_num_antennas(num_antennas),
	d_resolution(resolution),
	d_array_config(array_config),
	d_capon(capon)
    {
      // just for use in the amv
      GSL_SET_COMPLEX(&i, 0, 1);
      GSL_SET_COMPLEX(&one, 1, 0);


      std::fstream config_file(array_config);

      d_antenna_positions = new float[num_antennas*2];
      
      if(!config_file.good())
	throw std::invalid_argument("Cannot find configuration file.");
      float x, y;
      int i = 0;
      while (config_file >> x >> y) {
	if(i >= d_num_antennas) {
	  throw std::invalid_argument("Configuration file has too many antenna positions specified");
	}
	d_antenna_positions[2*i] = x;
	d_antenna_positions[2*i+1] = y;
	i++;
      }
      if(i!= d_num_antennas)
	throw std::invalid_argument("Configuration file does not have enough inputs.");

      // generate a LUT for amv's based on angles. Visualise this as a three-dimensional array
      d_amv_lut = new gr_complex[d_num_antennas*resolution*resolution*2];
      for(int i = 0; i < resolution; i++) {
	float theta = i*M_PI/resolution;
	for(int j = 0; j < 2*resolution; j++) {
	  float phi =  j*M_PI/resolution;
	  amv(theta, phi, d_amv_lut + (i*2*resolution + j)*d_num_antennas);
	}
      }
    }

    /*
     * Our virtual destructor.
     */
    beamform_impl::~beamform_impl()
    {
      delete[] d_antenna_positions;
      delete[] d_amv_lut;
    }

    int beamform_impl::work(int noutput_items,
	     gr_vector_const_void_star &input_items,
	     gr_vector_void_star &output_items
	     ) {
      const gr_complex *in = (const gr_complex *)input_items[0];
      float *out = (float *) output_items[0];

      for (int item = 0; item < noutput_items; item++) {
	// autocorrelation matrix
	gsl_matrix_complex_float_const_view Rxx = gsl_matrix_complex_float_const_view_array((float *)(in + d_num_antennas*d_num_antennas*item), d_num_antennas, d_num_antennas); // MxM
	// hold the intermediate product between Rxx and amv
	gsl_vector_complex_float *tmp = gsl_vector_complex_float_alloc(d_num_antennas);
	// access output vector as array
	gsl_matrix_float_view output_matrix = gsl_matrix_float_view_array(out + item*d_resolution * d_resolution * 2, d_resolution, d_resolution * 2);

	// step through the angle space in two dimensions
	for(int i = 0; i < d_resolution; i++) {
	  for(int j = 0; j < 2*d_resolution; j++) {
	    // array manifold vector corresponding with this theta and phi, which we pick from the 3d lookup table
	    gsl_vector_complex_float_view amv = gsl_vector_complex_float_view_array((float*)(d_amv_lut + d_num_antennas*(i*2*d_resolution + j)), d_num_antennas); // Mx1
	    gsl_complex_float alpha, beta, result;
	    GSL_SET_COMPLEX(&beta, 0, 0); //

	    // without capon beamforming we just compute dot(w^H, dot(Rxx, w))
	    if(!d_capon) {
	      // for normalizing the weight vector
	      GSL_SET_COMPLEX(&alpha, 1.0/sqrt(d_num_antennas), 0);

	      // tmp = dot(Rxx, amv)/ sqrt(d_num_antennas)
	      gsl_blas_chemv(CblasUpper, alpha, &Rxx.matrix, &amv.vector, beta, tmp);
	    
	      //result = dot(amv^H, tmp)
	      gsl_blas_cdotc(&amv.vector, tmp, &result);
	      // set i, j index of output matrix to result real part (imag should be approx zero)
	      gsl_matrix_float_set(&output_matrix.matrix, i, j, 1.0/result.dat[0]);
	    } else {
	      // for some reason gsl doesn't have linalg functions for
	      // single precision, so make a temporary matrix of
	      // doubles (somewhat inefficient) and then convert the
	      // inverse back to single precision
	      gsl_matrix_complex *Rxx_double = gsl_matrix_complex_alloc(d_num_antennas, d_num_antennas);
	      for(int i = 0; i < d_num_antennas; i++) {
		for (int j = 0; j < d_num_antennas; j++) {
		  gsl_matrix_complex_set(Rxx_double, i, j, (gsl_complex)gsl_matrix_complex_float_get(&Rxx.matrix, i, j));
		}
	      }
	      // permutation space
	      gsl_permutation *p = gsl_permutation_alloc(d_num_antennas);

	      GSL_SET_COMPLEX(&alpha, 1.0, 0);

	      // compute inverse of Rxx and cast back to double
	      gsl_linalg_complex_LU_invert(tmp, p, tmp);
	      gsl_matrix_complex_float *Rinv = gsl_matrix_complex_float_alloc(d_num_antennas, d_num_antennas);

	      for(int i = 0; i < d_num_antennas; i++) {
		for (int j = 0; j < d_num_antennas; j++) {
		  gsl_matrix_complex_float_set(Rinv, i, j, gsl_matrix_complex_get(tmp, i, j));
		}
	      }
	      gsl_vector_complex_float *tmp = gsl_vector_complex_float_alloc(d_num_antennas);

	      gsl_blas_chemv(CblasUpper, alpha, Rinv, &amv.vector, beta, &result);
	      gsl_blas_cdotc(&amv.vector, tmp, &result);
	      gsl_matrix_float_set(&output_matrix.matrix, i, j, 1.0/result.dat[0]);

	      gsl_permutation_free(p);
	      gsl_matrix_complex_free(Rxx_double);
	    }
	  }
	} 
	gsl_vector_complex_float_free(tmp);
      }
      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

    void
    beamform_impl::amv(float theta_source, float phi_source, gr_complex *lut_pointer) {
      float wave_vector[3] = {sin(theta_source)*cos(phi_source), sin(theta_source)*sin(phi_source), cos(phi_source)};
      lut_pointer[0] = 1;
      for (int i = 1; i < d_num_antennas; i++) {
	float x_diff = d_antenna_positions[3*i] - d_antenna_positions[0];
	float y_diff = d_antenna_positions[3*i+1] - d_antenna_positions[1];
	float z_diff = d_antenna_positions[3*i+2] - d_antenna_positions[2];

	float dotprod = wave_vector[0]*x_diff + wave_vector[1]*y_diff + wave_vector[2]*z_diff;

	lut_pointer[i] = exp(i * 2*M_PI*dotprod);
      }
    }
  } /* namespace doa */
} /* namespace gr */

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

#include <stdexcept>
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#define COPY_MEM false
#define FIX_SIZE true

#include <gnuradio/io_signature.h>
#include <math.h>

#include "calibrate_arb_array_impl.h"

using namespace arma;

namespace gr {
  namespace doa {

    calibrate_arb_array::sptr
    calibrate_arb_array::make(int num_antennas, float pilot_angle, char* array_config)
    {
      return gnuradio::get_initial_sptr
        (new calibrate_arb_array_impl(num_antennas, pilot_angle, array_config));
    }


    /*
     * The private constructor
     */
    calibrate_arb_array_impl::calibrate_arb_array_impl(int num_antennas, float pilot_angle, char* array_config)
      : gr::sync_block("calibrate_arb_array",
		       gr::io_signature::make(1, 1, num_antennas*num_antennas*sizeof(gr_complex)),
		       gr::io_signature::make(1, 1, num_antennas*sizeof(gr_complex))),
	d_num_antennas(num_antennas),
	d_pilot_angle(pilot_angle),
	d_array_config(array_config)

    {
      d_array_loc = fmat(d_num_antennas, 2);
	
      // form antenna array locations centered around zero and normalize
      d_array_loc = fmat(d_num_antennas, 2);
      std::fstream config_file{array_config};
      if(!config_file.good())
	throw std::invalid_argument("Cannot find configuration file.");
      float x, y;
      int i = 0;
      while (config_file >> x >> y) {
	if(i >= d_num_antennas) {
	  throw std::invalid_argument("Configuration file has too many antenna positions specified");
	}
	d_array_loc(i, 0) = x;
	d_array_loc(i,1) = y;
	i++;
      }
      if(i!= d_num_antennas)
	throw std::invalid_argument("Configuration file does not have enough inputs.");

      // form array response matrix
      cx_fcolvec v_temp(d_num_antennas, fill::zeros);
      d_diagmat_v_vec = cx_fmat(d_num_antennas, d_num_antennas);
      d_diagmat_v_vec_conj = cx_fmat(d_num_antennas, d_num_antennas);


      // generate array manifold vector for pilot angle
      amv(v_temp, d_array_loc, d_pilot_angle);
      d_diagmat_v_vec = diagmat(v_temp);

      // save transposed copy
      d_diagmat_v_vec_conj = diagmat(conj(v_temp));
    }

    /*
     * Our virtual destructor.
     */
    calibrate_arb_array_impl::~calibrate_arb_array_impl()
    {
    }

    /*
     * This approach is based on 
     * V. C. Soon, L. Tong, Y. F. Huang and R. Liu, 
     * "A Subspace Method for Estimating Sensor Gains and Phases," 
     * in IEEE Transactions on Signal Processing, 
     * vol. 42, no. 4, pp. 973-976, Apr 1994.
     */

    int
    calibrate_arb_array_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      fvec eig_val, W_eig_val;
      cx_fmat eig_vec, W_eig_vec;
      cx_fmat U_S, U_S_qs;
      cx_fmat W;

      for (int item = 0; item < noutput_items; item++) {
	// make input pointer into matrix pointer
	cx_fmat in_matrix(in + item*d_num_antennas*d_num_antennas, d_num_antennas, d_num_antennas);
	cx_fvec gain_phase_est_vec(out + item*d_num_antennas, d_num_antennas, COPY_MEM, FIX_SIZE);

	// determine EVD of the auto-correlation matrix

	eig_sym(eig_val, eig_vec, in_matrix);

	cx_fmat U_S = eig_vec.col(d_num_antennas - 1);
	cx_fmat U_S_sq = U_S*trans(U_S);


	// array gain and phase vector is the eigenvector of W that corresponds to the eigenvalue of unity
	W = d_diagmat_v_vec_conj*U_S_sq*d_diagmat_v_vec;
	eig_sym(W_eig_val, W_eig_vec, W);


	gain_phase_est_vec = W_eig_vec.col(d_num_antennas - 1);
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

    void
    calibrate_arb_array_impl::amv(cx_fcolvec& v_ii, fmat& array_loc, float theta)
    {
      // dot product between wave vector and antenna position vector
      const gr_complex i = gr_complex(0.0, 1.0);
      const fvec wave_vector({cos(theta), sin(theta)});
      const fvec phase_offsets = array_loc*wave_vector;

      // array manifold vector
      v_ii = exp(i*(-1.0*2*M_PI*phase_offsets));
    }

  } /* namespace doa */
} /* namespace gr */


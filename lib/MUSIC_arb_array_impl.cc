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
#include "MUSIC_arb_array_impl.h"

#include <armadillo>
#include <fstream>
#include <math.h>

using namespace arma;

namespace gr {
  namespace doa {

    MUSIC_arb_array::sptr
    MUSIC_arb_array::make(int num_antennas, int num_targets, int pspectrum_len, char* array_config)
    {
      return gnuradio::get_initial_sptr
        (new MUSIC_arb_array_impl(num_antennas, num_targets, pspectrum_len, array_config));
    }


    /*
     * The private constructor
     */
    MUSIC_arb_array_impl::MUSIC_arb_array_impl(int num_antennas, int num_targets, int pspectrum_len, char* array_config)
      : gr::sync_block("MUSIC_arb_array",
		       gr::io_signature::make(1, 1, num_antennas*num_antennas*sizeof(gr_complex)),
		       gr::io_signature::make(1, 1, pspectrum_len*sizeof(float))), // just a 1-dimensional sweep
	d_num_antennas{num_antennas},
	d_num_targets{num_targets},
	d_pspectrum_len{pspectrum_len}
    {
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

      // form theta vector
      d_theta = new float[d_pspectrum_len];
      d_theta[0] = 0.0;
      for(int j = 0; j < d_pspectrum_len; j++) {
	d_theta[j] = j*2*M_PI/pspectrum_len;
      }

      cx_fcolvec vii_temp(d_num_antennas, fill::zeros);
      d_vii_matrix = cx_fmat(d_num_antennas, d_pspectrum_len);
      d_vii_matrix_trans = cx_fmat(d_pspectrum_len, d_num_antennas);
      for(int j = 0; j < d_pspectrum_len; j++) {
	amv(vii_temp, d_array_loc, d_theta[j]);
	d_vii_matrix.col(i) = vii_temp;
      }
    }

    /*
     * Our virtual destructor.
     */
    MUSIC_arb_array_impl::~MUSIC_arb_array_impl()
    {
    }

    int
    MUSIC_arb_array_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      float *out = (float *) output_items[0];

      // Do <+signal processing+>
      fvec eig_val;
      cx_fmat eig_vec;
      cx_fmat U_N;
      cx_fmat U_N_sq;
      for (int item = 0; item < noutput_items; item++) {

	cx_fmat in_matrix(in+item*d_num_antennas*d_num_antennas, d_num_antennas, d_num_antennas);

	fvec out_vec(out + item*d_pspectrum_len, d_pspectrum_len, COPY_MEM, FIX_SIZE);

	// determine EVD of the autocorrelation matrix
	eig_sym(eig_val, eig_vec, in_matrix);


	U_N = eig_vec.cols(0, d_num_antennas-d_num_targets-1);
	U_N_sq = U_N*trans(U_N);


	// determine pseudo-spectrum for each value of theta [0.0 to 360.0]
	gr_complex Q_temp;
	for (int i = 0; i < d_pspectrum_len; i++) {
	  Q_temp = as_scalar(d_vii_matrix_trans.row(i)*U_N_sq*d_vii_matrix.col(i));
	  out_vec(i) = 1.0/Q_temp.real();
	}
	out_vec = 10.0*log10(out_vec/out_vec.max());
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

    // for a general 2-d position vector
    void
    MUSIC_arb_array_impl::amv(cx_fcolvec& v_ii, fmat& array_loc, float theta) {
      // dot product between wave vector and antenna position vector
      const gr_complex i = gr_complex(0.0, 1.0);
      const fvec wave_vector({cos(theta), sin(theta)});
      const fvec phase_offsets = array_loc*wave_vector;

      // array manifold vector
      v_ii = exp(i*(-1.0*2*M_PI*phase_offsets));
    }

  } /* namespace doa */
} /* namespace gr */


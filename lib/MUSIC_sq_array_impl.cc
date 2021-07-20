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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "MUSIC_sq_array_impl.h"

#include <armadillo>

using namespace arma;

namespace gr {
  namespace doa {

    MUSIC_sq_array::sptr
    MUSIC_sq_array::make(float norm_spacing, int num_targets, int pspectrum_len)
    {
      return gnuradio::get_initial_sptr
        (new MUSIC_sq_array_impl(norm_spacing, num_targets, pspectrum_len));
    }


    /*
     * The private constructor
     */
    MUSIC_sq_array_impl::MUSIC_sq_array_impl(float norm_spacing, int num_targets, int pspectrum_len)
      : gr::sync_block("MUSIC_sq_array",
		       gr::io_signature::make(1, 1, 16*sizeof(gr_complex)),
		       gr::io_signature::make(1, 1, pspectrum_len*pspectrum_len*sizeof(float))),
	d_norm_spacing(norm_spacing),
	d_num_targets(num_targets),
	d_pspectrum_len(pspectrum_len)
    {
      // form antenna array locations centered around zero and normalize
      d_array_loc[0] = pair {0, 0};
      d_array_loc[1] = pair {1, 0};
      d_array_loc[1] = pair {1, 1};
      d_array_loc[1] = pair {0, 1};
    }

    /*
     * Our virtual destructor.
     */
    MUSIC_sq_array_impl::~MUSIC_sq_array_impl()
    {
    }

    int
    MUSIC_sq_array_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      float *out = (float *) output_items[0];

      // Do <+signal processing+>

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace doa */
} /* namespace gr */


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

#ifndef INCLUDED_DOA_CALIBRATE_ARB_ARRAY_IMPL_H
#define INCLUDED_DOA_CALIBRATE_ARB_ARRAY_IMPL_H

#include <doa/calibrate_arb_array.h>
#include <armadillo>

using namespace arma;

namespace gr {
  namespace doa {

    class calibrate_arb_array_impl : public calibrate_arb_array
    {
     private:
      // Nothing to declare in this block.
      int d_num_antennas;
      int d_pilot_angle;
      char *d_array_config;
      fmat d_array_loc;
      cx_fmat d_diagmat_v_vec;
      cx_fmat d_diagmat_v_vec_conj;

     public:
      calibrate_arb_array_impl(int num_antennas, float pilot_angle, char* array_config);
      ~calibrate_arb_array_impl();
      void amv(cx_fcolvec& v_ii, fmat& array_loc, float theta);

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace doa
} // namespace gr

#endif /* INCLUDED_DOA_CALIBRATE_ARB_ARRAY_IMPL_H */


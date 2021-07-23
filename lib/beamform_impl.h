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

#ifndef INCLUDED_DOA_BEAMFORM_IMPL_H
#define INCLUDED_DOA_BEAMFORM_IMPL_H

#include <doa/beamform.h>
#include <gsl/gsl_matrix_float.h>

namespace gr {
  namespace doa {

    class beamform_impl : public beamform
    {
     private:
      float d_norm_spacing;
      int d_num_antennas;
      int d_array_type;
      int d_resolution;
      float* d_antenna_positions;
      float* d_angle_phase_lut;

      char frobenius_norm_mat(gsl_matrix_float* mat);

     public:
      beamform_impl(float norm_spacing, int num_antennas, int resolution, int array_type);
      ~beamform_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };
  } // namespace doa
} // namespace gr

#endif /* INCLUDED_DOA_BEAMFORM_IMPL_H */


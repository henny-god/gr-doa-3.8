/* -*- c++ -*- */

#define DOA_API

%include "gnuradio.i"           // the common stuff

//load generated python docstrings
%include "doa_swig_doc.i"

%{
#include "doa/antenna_correction.h"
#include "doa/MUSIC_lin_array.h"
#include "doa/autocorrelate.h"
#include "doa/calibrate_lin_array.h"
#include "doa/find_local_max.h"
#include "doa/MUSIC_sq_array.h"
#include "doa/beamform.h"
%}

%include "doa/antenna_correction.h"
GR_SWIG_BLOCK_MAGIC2(doa, antenna_correction);
%include "doa/MUSIC_lin_array.h"
GR_SWIG_BLOCK_MAGIC2(doa, MUSIC_lin_array);
%include "doa/autocorrelate.h"
GR_SWIG_BLOCK_MAGIC2(doa, autocorrelate);
%include "doa/calibrate_lin_array.h"
GR_SWIG_BLOCK_MAGIC2(doa, calibrate_lin_array);
%include "doa/find_local_max.h"
GR_SWIG_BLOCK_MAGIC2(doa, find_local_max);
%include "doa/MUSIC_sq_array.h"
GR_SWIG_BLOCK_MAGIC2(doa, MUSIC_sq_array);
%include "doa/beamform.h"
GR_SWIG_BLOCK_MAGIC2(doa, beamform);

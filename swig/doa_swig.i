/* -*- c++ -*- */

#define DOA_API

%include "gnuradio.i"           // the common stuff

//load generated python docstrings
%include "doa_swig_doc.i"

%{
#include "doa/antenna_correction.h"
#include "doa/autocorrelate.h"
#include "doa/find_local_max.h"
%}

%include "doa/antenna_correction.h"
GR_SWIG_BLOCK_MAGIC2(doa, antenna_correction);

%include "doa/autocorrelate.h"
GR_SWIG_BLOCK_MAGIC2(doa, autocorrelate);

%include "doa/find_local_max.h"
GR_SWIG_BLOCK_MAGIC2(doa, find_local_max);



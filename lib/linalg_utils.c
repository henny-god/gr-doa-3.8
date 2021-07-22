#include "linalg_utils.h"
#include <math.h>



float frobenius_norm_mat_b(gsl_matrix_float* a) {
  char sum = 0;

  for (int i = 0; i < a->size1; i++) {
    for (int j = 0; j < a->size2; j++) {
      sum += pow(gsl_matrix_float_get(a, i, j), 2.0);
    }
  }
  return sqrt(sum);
}

import numpy as np


def autocorrelation_testbench(num_ss: int, len_ss: int, overlap_size: int, num_inputs: int, FB: bool):
    num_samps = num_ss*(len_ss - overlap_size) + overlap_size
    
    # generate data matrix of random samples
    data = np.random.randn(num_samps, num_inputs) + 1j*np.random.randn(num_samps, num_inputs)

    # the actual block will buffer some zeros before because it
    # computes an overlapping portion on the first sample just have to
    # generate that manually here
    data_overlap_appended = np.zeros((num_samps, num_inputs), dtype=complex)
    data_overlap_appended[overlap_size:num_samps, :] = data[0:num_samps-overlap_size, :]
    

    # do autocorrelation
    out_matrix = np.ndarray((num_ss*num_inputs, num_inputs), dtype=complex)
    for i in range(num_ss):
        snapshot = data_overlap_appended[i*(len_ss-overlap_size):i*(len_ss-overlap_size) + len_ss,:]
        corr = np.dot(snapshot.T, np.conj(snapshot))/len_ss
        if FB:
            corr = 0.5 * corr + (0.5/len_ss)*np.flipud(np.fliplr(np.conj(corr)))
            
        out_matrix[i*num_inputs:(i+1)*num_inputs, :] = corr

    return [data, out_matrix]

import numpy as np
import sys
import math

def square_array(norm_spacing: float):
    return np.array([[-norm_spacing/2, -norm_spacing/2, 0], [-norm_spacing/2, norm_spacing/2, 0], [norm_spacing/2, -norm_spacing/2, 0], [norm_spacing/2, norm_spacing/2, 0]])

def linear_array(norm_spacing: float, num_antennas: int):
    antenna_norm_distances = np.ndarray((num_antennas, 3), dtype=float)
    # form the array about the z-axis with the the origin between the middle two elements
    for i in range(num_antennas):
        antenna_norm_distances[i,:] = np.array((0, 0, i*norm_spacing - (num_antennas-1)*norm_spacing/2))
    return antenna_norm_distances

def tetrahedron(norm_spacing: float):
    # normalize distances
    return np.arra([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]])

def antenna_distance_matrix(antennas):
    ret = np.ndarray((len(antennas), len(antennas)), dtype=float)
    for i in range(len(antennas)):
        for j in range(len(antennas)):
            ret[i][j] = np.linalg.norm(antennas[i] - antennas[j])
    return ret

def angle_to_phase_offset(antennas, theta, phi):
    '''
    computes the phase offset between antennas based on their physical locations and 
    the angle of arrival of the signal
    '''
    
    # compute signal vector from theta and phi
    l = len(antennas)
    n = [math.sin(theta)*math.cos(phi), math.sin(theta)*math.sin(phi), math.cos(theta)]
    ret = np.ndarray((l, l), dtype=float)
    
    # the phase distance between each element in the array is just the dot product
    # between the distance 
    for i in range(l):
        for j in range(l):
            ret[i][j] = -np.dot(n, antennas[i]-antennas[j])
    return ret

def distance_error(antennas, theta_source, phi_source, theta, phi):
    '''
    Compute the error between a vector of signal phase differences and a 
    generated vector of phases for a signal arriving at angle theta phi
    '''
    source_dist = angle_to_phase_offset(antennas, theta_source, phi_source)
    expected_dist = angle_to_phase_offset(antennas, theta, phi)
    
    # TODO: need to normalize error for the gnuradio block
    error = np.linalg.norm(source_dist - expected_dist)**2
    return error

def autocorrelation_testbench(num_ss: int, len_ss: int, overlap_size: int, num_inputs: int, FB: bool):
    num_samps = int(num_ss*(len_ss - overlap_size) + overlap_size)
    
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


def beamform_testbench(norm_spacing: float, num_antennas:int, resolution: int, theta: float, phi: float, array_type: int):
    n = [math.cos(phi)*math.sin(theta), math.sin(phi)*math.sin(theta), math.cos(theta)]
    arr = np.ndarray((num_antennas, 3), dtype=float)
    if array_type == 0:
        arr = linear_array(norm_spacing, num_antennas)
    elif array_type == 1:
        arr = square_array(norm_spacing)
    elif array_type == 2:
        arr = tetrahedron(norm_spacing)

    source_dist = angle_to_phase_offset(arr, theta, phi)

    beamform_array = np.ndarray((resolution, 2*resolution), dtype=float)
    for i in range(resolution):
        theta_sample = i/resolution*math.pi
        for j in range(2*resolution):
            phi_sample = j/resolution*math.pi
            # hold the expected phase distance matrix for theta_sample and phi_sample
            expected_dist = angle_to_phase_offset(arr, theta_sample, phi_sample)
            # compute distance norm between arrays
            norm = np.linalg.norm(source_dist - expected_dist)**2*24
            if norm > 255:
                norm = 255
            else:
                norm = int(norm)
            beamform_array[i][j] = norm

            # if i == 5 and j == 8:
            #     print("Debug sample from python testbench\n=======================")
            #     print("Phase diff input matrix: ")
            #     print(source_dist)
            #     print("Lut distances: ")
            #     print(expected_dist)
            #     print("Differences: ")
            #     print(source_dist - expected_dist)
            #     print("Normalized distance: ")
            #     print(beamform_array[i][j])

    # array to hold some input phase offsets that will be fed into the actual block
    phase_offsets = angle_to_phase_offset(arr, theta, phi)[0,:]
    return beamform_array, phase_offsets

def amv(num_antennas: int, norm_spacing: float, arr_type: str, theta: float, config_file: str):
    """
    Generate amv for a two-dimensional antenna configuration
    """
    wave_vector = np.array([math.cos(theta), math.sin(theta)])

    if arr_type == 'linear':
        return np.exp(-2j*math.pi*norm_spacing*math.cos(theta)*np.array(range(num_antennas)))
    elif arr_type == 'square':
        array = square_array(norm_spacing)
        offset_normalized = np.array(np.dot(array, wave_vector))
        return np.exp(-2j*math.pi*offset_normalized)

    elif arr_type == 'custom':
        pos_arr = np.ndarray((num_antennas, 2), dtype=float)
        try:
            file = open(config_file, 'r') # Clear file
            file.close()
        except:
            sys.stderr.write("Configuration "+config_file+", not valid\n")
            print(sys.stderr)
            sys.exit(1)
        file = open(config_file, 'r')

        lines = file.readlines()
        if len(lines) < num_antennas*2:
            raise ValueError("Number of antennas specified in config file is too small")
        elif len(lines) > num_antennas*2:
            raise ValueError("Number of antennas specified in config file is too large")
        for i in range(num_antennas):
            pos_arr[2*i][0] = float(lines[2*i])
            pos_arr[2*i][1] = float(lines[2*i+1])

        offset_normalized = np.array(np.dot(pos_arr, wave_vector))
        return np.exp(-2j*math.pi*offset_normalized)
    

def music_input_gen(len_ss: int, overlap_size: int, num_ss: int, num_antennas: int, FB: bool, arr_type: str, norm_spacing: float, PERTURB: bool, expected_aoa: float):
    nonoverlap_size = len_ss - overlap_size
    len_input = nonoverlap_size*num_ss + overlap_size

    if PERTURB:
        pass
    # generate signal and multiply by amv
    # assuming we're looking at a 5kHz signal at 2Msmps
    freq = 5e3
    samp_rate = 2e6
    samples_per_period = samp_rate/freq # should be 400

    config_file = ''

    array_manifold = amv(num_antennas, norm_spacing, arr_type, expected_aoa, config_file)
    signal = np.exp(-2j*math.pi/samples_per_period*np.array(range(len_input)))

    signal_matrix = np.dot(amv, signal)



    

    

    pass


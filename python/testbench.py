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

def read_array_config(num_antennas: int, array_config: str):
    array = np.ndarray((num_antennas, 3), dtype=float)
    try:
        file = open(array_config, 'r')
        file.close()
    except:
        sys.stderr.write("Configuration "+ array_config +", not valid\n")
        print(sys.stderr)
        sys.exit(1)
    file = open(array_config, 'r')
    lines = file.readlines()
    file.close()
    if len(lines) < num_antennas*3:
        raise ValueError("Number of antennas specified in config file is too small")
    elif len(lines) > num_antennas*3:
        raise ValueError("Number of antennas specified in config file is too large")
    for i in range(num_antennas):
        array[i][0] = float(lines[3*i])
        array[i][1] = float(lines[3*i+1])
        array[i][2] = float(lines[3*i+2])

    return array
    

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


def channel_model(antennas, sig_angle, sig_mag, num_samps, snr) -> np.array:
    assert(len(sig_angle) == len(sig_mag))
    M = num_samps
    N = len(antennas)
    
    n = 1/np.sqrt(snr)*np.random.randn(N, M)*np.exp(1j*np.random.uniform(0, 2*np.pi, (N, M)))
    
    A = np.ndarray((len(antennas), len(sig_angle)), dtype=complex)
    for i in range(len(sig_angle)):
        A[:,i] = amv(antennas, theta=sig_angle[i][0], phi=sig_angle[i][1])
    
    S = np.random.randn(len(sig_angle), M)*np.exp(1j*np.random.uniform(0,2*np.pi,(len(sig_angle), M)))
    
    for i in range(len(sig_mag)):
        S[i,:] = S[i,:]*sig_mag[i]
    
    X = np.dot(A, S) + n
    return X

    

def amv(antennas, theta, phi):
    '''
    computes the array manifold vector for an array specified by antennas
    '''
    
    # compute signal vector from theta and phi
    l = len(antennas)
    n = [math.sin(theta)*math.cos(phi), math.sin(theta)*math.sin(phi), math.cos(theta)]
    ret = np.ndarray(l, dtype=float)
    
    # the phase distance between each element in the array is just the dot product
    # between the distance 
    for i in range(l):
        ret[i] = np.dot(n, antennas[i]-antennas[0]) # signed negative by typical array config
    return np.exp(2j*(math.pi*ret))    


def beamform_1d_testbench(antennas, num_samples: int, resolution: int, phi: float, snr: float, capon: int):
    x = channel_model(antennas, [[np.pi/2, phi]], [1], num_samples, snr)
    Rxx = np.dot(x, np.conj(x.T))*(1/num_samples)
    amvs = np.ndarray((resolution, len(antennas)), dtype=complex)
    powers = np.ndarray((resolution), dtype=float)

    for i in range(resolution):
        phi_step = i * np.pi/resolution
        amvs[i] = amv(antennas, np.pi/2, phi_step)

    if capon:
        Rinv = np.linalg.inv(Rxx)
        powers = np.log10(1/np.einsum('ay, ay->a', np.conj(amvs), np.einsum('ay,xy->xa', Rinv, amvs)).real)
    else:
        amvs = amvs/len(antennas)
        powers = np.log10(np.einsum('ay, ay->a', np.conj(amvs), np.einsum('ay,xy->xa', Rxx, amvs)).real)

    return [powers, Rxx]

def beamform_2d_testbench(antennas, num_samples: int, resolution: int, angles, snr: float, capon: int):
    x = channel_model(antennas, angles, [1], num_samples, snr)
    Rxx = np.dot(x, np.conj(x.T))*(1/num_samples)
    amvs = np.ndarray((resolution, 2*resolution), len(antennas), dtype=complex)
    powers = np.ndarray((resolution, 2*resolution), dtype=float)


    for i in range(resolution):
        theta_step = i * np.pi/resolution
        for j in range(resolution*2):
            phi_step = j * np.pi/resolution
            amvs[i][j] = amv(antennas, theta_step, phi_step)
    if capon:
        Rinv = np.linalg.inv(Rxx)
        powers = np.log10(1/np.einsum('xyz, xyz->xy', np.conj(amvs), np.einsum('az, xyz->xya', Rinv, amvs)).real)
    else:
        amvs = amvs/len(antennas)
        powers = np.einsum('xyz, xyz->xy', np.conj(amvs, np.einsum('az, xyz->xya', Rxx, amvs)).real)
    return [powers, Rxx]
                
        

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


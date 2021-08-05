This is the doa-write-a-block package meant as a guide to building
out-of-tree packages. To use the doa blocks, the Python namespaces
is in 'doa', which is imported as:

    import doa

See the Doxygen documentation for details about the blocks available
in this package. A quick listing of the details can be found in Python
after importing by using:

    help(doa)

# Using gr-doa blocks to perform direction-finding

This port of gr-doa aims to implement direction finding algorithms as modular blocks that can be used with arbitrary phase-coherent multi-channel SDRs. Due to its modular nature, you will need to learn how to correctly configure these blocks for your particular array even to get the most basic setups working. As long as you have good measurement tools and some patience, this shouldn't be too difficult.

In order to perform any kind of direction finding, you will need a phase-coherent SDR and some sort of antenna array to detect phase-differences between arriving signals. The first of these sounds complicated but it is really just any SDR where you can sample multiple channels and know that there is some constant, predictable phase-offset between samples in those channels. Ideally, this difference is zero. Phase coherence usually means that the individual ADC's of the SDR's channels are running off the same clock and the datapath from the ADC's to the SDR's processor are designed to propagate information in the same amount of time for all the channels.

The antenna array is just a fixed configuration for some multiple of antennas. You might wonder what array configuration is ideal for direction finding and the answer is that it depends on the circumstances of your DoA task. Obviously, the more antennas you have, the more information you know about the signal in space, but the positioning of the antennas can also determine this. A linear array, for example, can only 'see' in angular dimension. Think of a wavefront impinging on a line of antennas. If you rotate that wavefront's source around the colinear axis of those antennas, the time-of-arrival of that wavefront will be the same in all rotations, meaning you won't be able to discern one of these positions from another.

Generally, you will want to keep the spacings between adjacent antennas in an array at or less than half the signal's wavelength. This is because aliasing between phase offsets can occur between antennas that are spaced more than this distance apart. For example, if a signal must travel .6 wavelengths before hitting another antenna, the phase difference will look the same as if the other antenna were .1 wavelengths *in front* of the other antenna. This could be harmful if we only have these two antennas in our array, but it's likely irrelevant if there are more that have spacing of less than half a wavelength. So as a general rule of thumb, make sure that the minumum distance between an antenna and its set of adjacent antennas is at most half a wavelength.

Centro-symmetric arrays

In all of the direction-finding blocks, you will need to provide a spatial configuration file to tell the blocks where your antennas lie relative to one another. In direction finding, we prefer to use distance normalized to the carrier frequency of the signal that you're detecting. This makes the algorithm's math easier and only requires that you provide one configuration file without having to specify the carrier frequency.


The first four steps are as follows:
1. Calculate carrier wavelength: $\lambda = \frac{c}{f}$. e.g. mine is 915MHz, so $\lambda = \frac{3\times10^6}{915\times10^6}=.3276m$
2. Determine the coordinates of your antennas. It's conventional to have the symmetric center of the array be $(0, 0, 0)$, but this doesn't matter mathematically, as long as the relative positioning is correct. Pay attention to the order in which you specify the antennas. e.g. I have a square antenna array, whose positions are (in $(x,y,z)$ coordinate format and in centimeters) $A = ((-8.19, -8.19, 0), (-8.19, 8.19, 0), (8.19, -8.19, 0), (8.19, 8.19, 0))$.
3. normalize this array with the wavelength: $A_{norm} = A / \lambda$. My normalized array is then $((-0.25, -0.25, 0), (-0.25, 0.25, 0), (0.25, -0.25, 0), (0.25, 0.25, 0))$.
4. Create a file that can be read by the gnuradio blocks. This file MUST be in a a one-index-by line format. Reading the array in $x$, $y$ axis order. You can use decimal syntax to represent floating point numbers. e.g.:
```
-0.25
-0.25
0
-0.25
0.25
0
0.25
-0.25
0
0.25
0.25
0
```

You now need to setup your SDR in correspondence with your antenna array. The routing from antennas to connections in the flowgraph do matter, so make sure you have some way of distinguishing the antennas from one another. I have mine labelled because they are all green and centro-symmetric in a square. Now configure your SDR source:
6. Whichever SDR you are using, set it's center frequency to the carrier of the signal you are receiving. 
7. By the Nyquist criterion, set the SDR's sample rate to twice the frequency of whatever modulated signal you are sampling. I have another SDR transmitting a 10kHz sine with a center frequency of 915Mhz, so I would want to sample with at least 20kSmps.
8. At this step, I find it useful to assemble my connections between antennas and the SDR. Connect the antennas such that channel 1 of the SDR corresponds with the first coordinate pair in the config file etc.

Autocorrelation: this step is the same for all doa techniques because it is sort of an averaging of the phase offsets between antennas in your array. The operation takes a block of samples and computes a normalized dot-product between every combination of sample lists in the array. This returns a matrix whose entries are the approximated phase offsets for arriving signals in all the pairs of antennas.

9. Make an autocorrelation block and set its number of antennas to be the number specified in the array config file.
10. Route outputs from the SDR source in ascending order to inputs of the autocorrelation matrix
11. Specify the number of samples to autocorrelate. Gnuradio requires that this be some power of two. Choose some number that is at least greater than 100 in most cases. The more samples you average, the more accurate the autocorrelation matrix will approximate the actual phase offsets between elements in the array. Adjust the overlap parameter and also make it some power of two. 
12. This will determine how many samples of overlap are between each autocorrelation matrix. This can be zero, but when set to be higher, the successive autocorrelation matrices will be more 'continuous' representations of the input signals.

From here on out, the steps are determined by which DoA estimation technique you are performing.

## Beamforming
Beamforming is essentially measuring the signal power in a given direction

## MUSIC
MUSIC is a subspace-DoA technique that uses the property of orthogonality between signal and noise subspaces to find signal angles. It is particularly good at estimating the arrival angles of multiple *uncorrelated* signals.




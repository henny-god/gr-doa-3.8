# About gr-doa
gr-doa-3.8 is a branch of the gr-doa repository from Ettus Research which aims to:
 - port the project to gnuradio 3.8, migrating the project's initial code to a build environment that works on newer debian and arch linux systems.
 - have a wider array of doa blocks. The original library only implements MUSIC but there are a number of other doa algorithms that I plan to put in here
 - be hardware agnostic. All you should need is a phase-coherent multi-channel receiver

From the original repository, "We provide apps to determine the accuracy of phase synchronization achieved and to estimate DoA which fundamentally requires accurate phase synchronization across the receive streams."

### Basic Dependencies
 - gnuradio >= 3.8
 - armadillo >= 7.300

### Dependencies Needed for QA Testing
 - octave (Tested 4.0.2)
 - octave-signal (Tested 1.3.2)
 - scipy (Tested 0.15.1)
 - oct2py (Tested 3.5.9)

### Dependencies Needed for Doc
 - texlive-latex-base

### What is implemented?
 - Relative phase offset measurement and correction
 - Antenna element calibration for linear arrays
 - MUSIC algorithm for linear arrays
 - Root-MUSIC algorithm for linear arrays 

### Planned Features
 - MUSIC for square arrays
 - move from armadillo to gsl for building on embedded hardware

### OSs Tested 
 - Ubuntu 14.04, Ubuntu 16.04 
 
### Installation
`$ git clone https://github.com/EttusResearch/gr-doa` <br />
`$ cd gr-doa` <br />
`$ mkdir build` <br />
`$ cd build` <br />
`$ cmake ..` <br />
`$ make` <br />
`$ make test` <br />
`$ sudo make install` <br />
`$ sudo ldconfig` <br />

### Documentation
 - For a concise description of the steps involved: `https://github.com/EttusResearch/gr-doa/wiki`
 - For details about the blocks available
in this package: `gr-doa/build/docs/doxygen/html/index.html`
 - For detailed description: `gr-doa/docs/whitepaper/doa_whitepaper.pdf`

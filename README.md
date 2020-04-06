This repository consist of the hardware and specification of parts associated to the paper "A programmable chemical state machine solves hard computational problems "

University of Glasgow, School of Chemistry

Authors: Abhishek Sharma, Marcus Tze-Kiat Ng, Juan Manuel Parrilla Gutierrez, Yibin Jiang, Leroy Cronin

# BZ Computation
BZ platforms are automated platform that couple Belousov-Zhabotinsky reaction, hydrodynamic of the system and image recgonition to realise computation in a chemical system.


## Platform Overview
The periodicity of the oscillation of the BZ reaction is controlled via mechanical stimuli from the magnetics stirrers. On top of that, the coupling between two or more neighbouring cells are governed by the hydrodynamics through the interfacial stirrers.<br/>
The dimension of each cell was desgined in such a way that no apparent coupling between cells can be observed without activation of the interfacial stirrers.
<p align="center">
  <img width="596" height="282" src="https://github.com/croningp/BZComputation/blob/master/media/bz_platform_description.jpg">
<!-- </p>
![](https://github.com/croningp/BZComputation/blob/master/media/bz_platform_description.jpg)
## Hardware -->

Details regarding the hardware and the STLs of the 3D printed parts used for the experiments are provided in [hardware](https://github.com/croningp/BZComputation/tree/master/hardware/stls).

## Code example
```python
# Library imports
import cv2
import sys
import time
import queue
import random
import numpy as np

from tricont_ctonrols import TricontControl
from bz_control import BZBoard
import predict_cnn_2D

resq = multiprocessing.Queue()
stopt = multiprocessing.Queue()

cnn = predict_cnn_2D.CNN(kwargs={
	'streampath': "invideo", 'outvideo': "output",
	'resq': resq, 'stopsig': stopt
	})

arduino_dict= {         
		0: "/dev/BZ_satu",
		1: "/dev/BZ_dua",
		2: "/dev/BZ_tiga",
		3: "/dev/BZ_empat"  }

b = BZBoard(port_dict=arduino_dict)    # Arduino device
p = TricontControl()                   # calling tricont class
'''
Pretreatment before starting an experiment which includes filling the platform with the BZ
solutions and mixing/stabilisation period which allow the solution to be spread evenly 
throughout the platform.
 '''
p.filling_2d()
b.activate_all(speed=50)
time.sleep(120)
b.disable_all()
time.sleep(160)

# Start of experiment
cnn.start()
'''
Conditions provided which is unique to the experiments depending on what is required.
In this particular example the experiment will stay put for a minute and terminate the experiment.
'''
time.sleep(60)

# End of experiment
stopt.put(1)
cnn.join()

p.cleaning_2d()
```


## __________________________________________________________________________________

Authors: <br/>
Abhishek Sharma<br/>
Marcus Tze-Kiat Ng<br/>
Juan Manuel Parrilla Gutierrez<br/>
Yibin Jiang <br/>
Leroy Cronin 

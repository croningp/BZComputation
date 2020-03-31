###############################################################################
#
# This class implements a deque type from Python, but using Numpy
#
###############################################################################

import numpy as np

class NPDeque():

  def __init__(self, numcells=4, maxLen=10):

    self.maxlen = maxLen
    self.deques = np.ones((numcells, maxLen))

  def append(self, cell, value):
    ''' adds value "value" to the queue "cell" within our self.deques'''

    x = self.deques[cell]
    x[:-1] = x[1:] 
    x[-1] = value

  def get(self, cell, lastN=0):
    ''' returns deque row within our self.deques
    if lastN is given, it returns the last N entries instead of all of it'''

    return self.deques[cell][-lastN:]


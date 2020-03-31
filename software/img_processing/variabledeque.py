###############################################################################
#
# This class implements a deque type from Python, but with variable maxlen.
# In the original deque, maxlean is read-only. Once set it cannot be changed.
# We will solved it by basically copying the old conents and creating a new 
# deque with the new maxlen.
#
###############################################################################


from collections import deque
import numpy as np


class VariableQueue():


	def __init__(self, numcells=7, maxLen=10, oldqueues=None):
		'''oldqueue is going to be a list of deques, because we have a 
		deque for each cell in the BZ platform'''

		self.maxlen = maxLen

		# We are not sending an old one, so just create a new one
		if not oldqueues:
			self.deques = [ deque(maxlen = maxLen) for i in range(numcells)]

		else: # user sends and old one, so we need to copy and change size.
			self.deques = [ deque(oldq, maxlen = maxLen) for oldq in oldqueues]


	def newmaxlength(self, newLen=10):
		'''Changes the maxlen of the queues to the new input value'''

		self.maxlen = newLen
		self.deques = [ deque(dq, maxlen=newLen) for dq in self.deques]


	def append(self, cell, value):
		''' adds value "value" to the queue "cell" within our self.deques'''

		self.deques[cell].append(value)


	def get(self, cell):
		''' returns deque "cell" within our self.deques'''

		return self.deques[cell]


	def tonp(self):
		''' returns deque "cell" within our self.deques'''

		return np.array(self.deques)


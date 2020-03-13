# ---------------------------------------------------------------------------- #
# --------------- TWO DIMENSIONAL BZ PLATFORM 7 X 7 CONTROLLER --------------- #
# ---------------------------------------------------------------------------- #


"""
	Controls BZ Board using Serial Interface. Each motor can be addressed individually.

	Cell Stirrers in 7x7 array are given by : 

	+ --------------------------------------------+
	|											  |
	|	C17	  C27   C37   C47   C57   C67   C77	  |
	|											  |
	|	C16   C26   C36   C46   C56   C66   C76   |
	|											  |
	|	C15	  C25	C35	  C45	C55	  C65	C75   |
	|											  |
	|	C14   C24	C34	  C44	C54	  C64	C74   |
	|											  |
	|	C13	  C23	C33	  C43	C53	  C63	C73   |
	|											  |
	|	C12	  C22	C32	  C42	C52	  C62	C72   |
	|											  |
	|	C11	  C21	C31	  C41	C51	  C61	C71   |
	|											  |
	+---------------------------------------------+

"""

import os
import time
import json
import random
import serial

class BZBoard:
	"""
		Base Class to control all the motors via four connected Arduino UNOs.
	"""


	def __init__(self, port_dict):
		random.seed(37)
		"""
			Initialized BZ Board, Serial Communication with Arduino UNOs.
		"""

		self.ncells_X, self.ncells_Y = 7, 7

		self.ser = {}
		for n, port in port_dict.items():
			self.ser[n] = serial.Serial(port, 9600, timeout=120)
		
		time.sleep(2) # serial docs recommend a wait just after connection
		for serial_obj in self.ser.values():
			serial_obj.flush()
			serial_obj.flushInput()
			serial_obj.flushOutput()


		# List of all Cell Stirrers
		# [arduino_numer, adafruit_shield, motor] 
		
		self.cell_motors = { 

			# Port_1(satu): CONTROLS CELL STIRRERS
			# ----------------------------------------------------------------------- #

			"C11": [0, 0, 1], "C21": [0, 0, 2], "C31": [0, 0, 3], "C41": [0, 0, 4],
			"C12": [0, 1, 1], "C22": [0, 1, 2], "C32": [0, 1, 3], "C42": [0, 1, 4],
			"C13": [0, 2, 1], "C23": [0, 2, 2], "C33": [0, 2, 3], "C43": [0, 2, 4],
			"C14": [0, 3, 1], "C24": [0, 3, 2], "C34": [0, 3, 3], "C44": [0, 3, 4],
			"C15": [0, 4, 1], "C25": [0, 4, 2], "C35": [0, 4, 3], "C45": [0, 4, 4],
			"C16": [0, 5, 1], "C26": [0, 5, 2], "C36": [0, 5, 3], "C46": [0, 5, 4],
			"C17": [0, 6, 1], "C27": [0, 6, 2], "C37": [0, 6, 3], "C47": [0, 6, 4],

			# Port_2(dua): CONTROLS CELL STIRRERS
			# ----------------------------------------------------------------------- #

			"C51": [1, 0, 1], "C61": [1, 0, 2], "C71": [1, 0, 3],
			"C52": [1, 1, 1], "C62": [1, 1, 2], "C72": [1, 1, 3],
			"C53": [1, 2, 1], "C63": [1, 2, 2], "C73": [1, 2, 3],
			"C54": [1, 3, 1], "C64": [1, 3, 2], "C74": [1, 3, 3],
			"C55": [1, 4, 1], "C65": [1, 4, 2], "C75": [1, 4, 3],
			"C56": [1, 5, 1], "C66": [1, 5, 2], "C76": [1, 5, 3],
			"C57": [1, 6, 1], "C67": [1, 6, 2], "C77": [1, 6, 3],
		}

		# List of all Interfacial Stirrers
		# [arduino_numer, adafruit_shield, motor] 

		self.interface_motors = {

			# Port_3(tiga): CONTROLS INTERFACIAL STIRRERS
			# ----------------------------------------------------------------------- #

			"I11": [2, 0, 1], "I12": [2, 0, 2], "I13": [2, 0, 3], "I14": [2, 0, 4],
			"I15": [2, 1, 1], "I16": [2, 1, 2], "I17": [2, 1, 3], "I18": [2, 1, 4],
			"I19": [2, 2, 1], "I110": [2, 2, 2], "I111": [2, 2, 3], "I112": [2, 2, 4],
			"I21": [2, 3, 1], "I22": [2, 3, 2], "I23": [2, 3, 3], "I24": [2, 3, 4],
			"I25": [2, 4, 1], "I26": [2, 4, 2], "I27": [2, 4, 3], "I28": [2, 4, 4],
			"I29": [2, 5, 1], "I210": [2, 5, 2], "I211": [2, 5, 3], "I212": [2, 5, 4],
			"I31": [2, 6, 1], "I32": [2, 6, 2], "I33": [2, 6, 3], "I34": [2, 6, 4],
			"I35": [2, 7, 1], "I36": [2, 7, 2], "I37": [2, 7, 3], "I38": [2, 7, 4],
			"I39": [2, 8, 1], "I310": [2, 8, 2], "I311": [2, 8, 3], "I312": [2, 8, 4],
			"I113": [2, 9, 1], "I213": [2, 9, 2], "I313": [2, 9, 3],
			"I48": [2, 10, 1], "I410": [2, 10, 2], "I412": [2, 10, 3],

			# Port_4(empat): CONTROLS INTERFACIAL STIRRERS
			# ----------------------------------------------------------------------- #

			"I41": [3, 0, 1], "I42": [3, 0, 2], "I43": [3, 0, 3], "I44": [3, 0, 4],
			"I45": [3, 1, 1], "I46": [3, 1, 2], "I47": [3, 1, 3],
			"I49": [3, 2, 1], "I411": [3, 2, 2], "I413": [3, 2, 3],
			"I51": [3, 3, 1], "I52": [3, 3, 2], "I53": [3, 3, 3], "I54": [3, 3, 4],
			"I55": [3, 4, 1], "I56": [3, 4, 2], "I57": [3, 4, 3], "I58": [3, 4, 4],
			"I59": [3, 5, 1], "I510": [3, 5, 2], "I511": [3, 5, 3], "I512": [3, 5, 4],
			"I61": [3, 6, 1], "I62": [3, 6, 2], "I63": [3, 6, 3], "I64": [3, 6, 4],
			"I65": [3, 7, 1], "I66": [3, 7, 2], "I67": [3, 7, 3], "I68": [3, 7, 4],
			"I69": [3, 8, 1], "I610": [3, 8, 2], "I611": [3, 8, 3], "I612": [3, 8, 4],
			"I72": [3, 9, 1], "I74": [3, 9, 2], "I76": [3, 9, 3], "I78": [3, 9, 4],
			"I513": [3, 10, 4], "I613": [3, 10, 3], "I712": [3, 10, 2], "I710": [3, 10, 1],
		}

		# Getting a combined list of all stirrers
		self.motors = {**self.cell_motors, **self.interface_motors} 

		# this matrix stores if the motors are enabled (1) or disabled (0)
		# before writting to serial we check this to not sent writes not needed
		self.matrix = {

			# Port_1(satu)
			"C11": 0, "C21": 0, "C31": 0, "C41": 0,
			"C12": 0, "C22": 0, "C32": 0, "C42": 0,
			"C13": 0, "C23": 0, "C33": 0, "C43": 0,
			"C14": 0, "C24": 0, "C34": 0, "C44": 0,
			"C15": 0, "C25": 0, "C35": 0, "C45": 0,
			"C16": 0, "C26": 0, "C36": 0, "C46": 0,
			"C17": 0, "C27": 0, "C37": 0, "C47": 0,

			# Port_2(dua)
			"C51": 0, "C61": 0, "C71": 0,
			"C52": 0, "C62": 0, "C72": 0,
			"C53": 0, "C63": 0, "C73": 0,
			"C54": 0, "C64": 0, "C74": 0,
			"C55": 0, "C65": 0, "C75": 0,
			"C56": 0, "C66": 0, "C76": 0,
			"C57": 0, "C67": 0, "C77": 0,

			# Port_3(tiga)
			"I11": 0,  "I12": 0,  "I13": 0, "I14": 0,
			"I15": 0,  "I16": 0,  "I17": 0, "I18": 0,
			"I19": 0,  "I110": 0, "I111": 0, "I112": 0,
			"I21": 0,  "I22": 0,  "I23": 0, "I24": 0,
			"I25": 0,  "I26": 0,  "I27": 0, "I28": 0,
			"I29": 0,  "I210": 0, "I211": 0, "I212": 0,
			"I31": 0,  "I32": 0,  "I33": 0, "I34": 0,
			"I35": 0,  "I36": 0,  "I37": 0, "I38": 0,
			"I39": 0,  "I310": 0, "I311": 0, "I312": 0,
			"I113": 0, "I213": 0, "I313": 0,
			"I48": 0,  "I410": 0, "I412": 0,

			# Port_4(empat)
			"I41": 0,  "I42": 0,  "I43": 0,  "I44": 0,
			"I45": 0,  "I46": 0,  "I47": 0,
			"I49": 0,  "I411": 0, "I413": 0,
			"I51": 0,  "I52": 0,  "I53": 0,  "I54": 0,
			"I55": 0,  "I56": 0,  "I57": 0,  "I58": 0,
			"I59": 0,  "I510": 0, "I511": 0, "I512": 0,
			"I61": 0,  "I62": 0,  "I63": 0,  "I64": 0,
			"I65": 0,  "I66": 0,  "I67": 0,  "I68": 0,
			"I69": 0,  "I610": 0, "I611": 0, "I612": 0,
			"I72": 0,  "I74": 0,  "I76": 0,  "I78": 0,
			"I513": 0, "I613": 0, "I712": 0, "I710": 0,
			}


	def __del__(self):
		"""
			Disables all the motors.
		"""
		self.disable_all()
		for serial_obj in self.ser.values():
			serial_obj.close()
			del serial_obj


	def close(self):
		"""
			Disables all motors and close the seial communication.
		"""
		self.disable_all()
		for serial_obj in self.ser.values():
			serial_obj.close()
			del serial_obj


	def activate_motor(self, motor_code, direction=0, speed=90):
		"""
			Activates a motor based on the given input arguments.
			Speed : usually refers to the PWM levels.
		"""

		arduino, shield, motor = self.motors[motor_code] # get shield and motor 
		
		if self.matrix[motor_code] < 1 and speed > 0: # we need to activate it

			# Motors needs to be started at higher PWM.
			command = "A%d M%d D%d S255\n" % (shield, motor, direction)
			time.sleep(0.1)	# Sleeping time for 100 ms.
			
			# Setting the desired speed
			command += "A%d M%d D%d S%d\n" % ( shield, motor, direction, speed )
			
			self.matrix[motor_code] = 1 # mark it as enabled
			self.ser[arduino].write(command.encode()) # encode helps program run 

		elif self.matrix[motor_code] < 1 and speed == 0: # we keep it disabled (it's off with 0 speed)
			pass

		elif self.matrix[motor_code] > 0 and speed > 0: # just update speed
			command = "A%d M%d D%d S%d\n" % ( shield, motor, direction, speed )
			self.ser[arduino].write(command.encode())

		elif self.matrix[motor_code] > 0 and speed == 0: # we disable it (on with no speed)
			self.disable_motor(motor_code)

		else:
			print("Motor not responding | Something is WRONG") 


	def activate_cell_all(self, direction=0, speed=90):
		"""
			Activates all interfacial motors at a given PWM level
		"""
		for key, value in self.cell_motors.items(): 
			self.activate_motor(key, direction, speed)
			self.ser[value[0]].flush() #flush variables


	def activate_interface_all(self, direction=0, speed=127):
		"""
			Activates all interfacial motors at a given PWM level
		"""
		for key, value in self.interface_motors.items(): 
			self.activate_motor(key, direction, speed)
			self.ser[value[0]].flush() #flush variables


	def activate_all(self, direction=0, speed=20):
		"""
			Activates all motors at a given PWM level
		"""

		for key, value in self.motors.items(): 
			self.activate_motor(key, direction, speed)
			self.ser[value[0]].flush() #flush variables


	def activate_cell_neighbours(self, cell, nn=4, direction=0, speed=150):
		"""
			Activates all interfacial stirrers for a given cell stirrer ID.
		"""
		i, j = list(map(int, list(cell)[1:3]))
		self.neigh = [[i, 2*j-2], [i, 2*j-1], [i, 2*j], [i-1, 2*j-1]]
		
		# Creating list of surrounding interfacial stirrers
		self.n_list = []

		for i in range(nn):
			self.n_list.append("I"+"".join(str(x) for x in self.neigh[i]))

		# Activating Interfacial stirrers
		for i in self.n_list:
			try:
				self.activate_motor(i, direction, speed)
			except KeyError:
				continue


	def disable_motor(self, motor_code):
		"""
			Disable a motor with the given address.
		"""
		arduino, shield, motor = self.motors[motor_code]
		command = "A%d M%d D0 S0\n" % ( shield, motor )

		if self.matrix[motor_code] > 0: # so it was enabled
			self.ser[arduino].write(command.encode())
			self.matrix[motor_code] = 0 # mark it disabled
			
			
	def disable_all_cells(self):
		"""
			Disables all cell motors.
		"""
		for key in self.cell_motors.keys():
			self.disable_motor(key)


	def disable_all(self):
		"""
			Disables all motors.
		"""
		for key in self.motors.keys():
			self.disable_motor(key)


	def rand_pattern(self, n_cells, activate_neighbours=False, direction=0, speed=20):
		"""
			Creates a random pattern of activated cell stirrers over the whole array.
			n_cells : Number of random cells to be activated.
			
		"""
		# Deactivate previously activated cells
		self.disable_all_cells()
		# time.sleep(5)
		# Randomly shuffling the list of cell stirrers

		# random.seed(time.time()) random function took out to global variable
		self.cell_list = ["C" + str(x) + str(y) for x in range(1,self.ncells_X+1) for y in range(1,self.ncells_Y+1)]
		random.shuffle(self.cell_list)
		
		# Selecting cells from the random shuffle
		self.random_cells = self.cell_list[:n_cells]

		# Activating Cells
		[self.activate_motor(i, direction, speed) for i in self.random_cells]

		# Activating Neighbours
		if activate_neighbours == True:
			[self.activate_cell_neighbours(i) for i in self.random_cells]


if __name__ == "__main__":
	arduino_dict = {
		0: "/dev/BZ_satu",
		1: "/dev/BZ_dua",
		2: "/dev/BZ_tiga",
		3: "/dev/BZ_empat"
		}
	b = BZBoard(port_dict=arduino_dict)

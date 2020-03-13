# Last update 20190715
# Dream Team 
# This scipt consist of class that can automate the BZ platform (1D and 2D)
import os
import sys
import time
from pycont.controller import MultiPumpController

TRICONT_JSON_CONFIG="pycont_config.json"

class TricontControl():
	"""
	Helps to clean and fill the BZ platforms 
	2D in particular
	"""
	
	
	def __init__(self):
		self.controller = MultiPumpController.from_configfile(TRICONT_JSON_CONFIG)
		self.controller.smart_initialize()

		#self.controller.apply_command_to_pumps("go_to_volume", 0)
		
	def get_pump_object(self, pump_name: str):
		"""Get the pump object from string name
		
		Arguments:
			pump_name {str} -- Name of the pump
		
		Raises:
			Exception: No pump found
		
		Returns:
			pump -- Pump object
		"""
		try:
			# Get the pump name
			return getattr(self.controller, pump_name)
		except:
			# Raise exception if no pump found
			print(f"No pump named {pump_name}!")
			raise Exception

	def pump_all(self, pump_dict: dict, wait: bool = False) -> (dict, dict):
		"""Pump all values in the pump dictionary
		If values are over the maximum volume, recalculate what's left to pump

		Arguments:
			pump_dict {dict} -- Pump names and volumes
		
		Keyword Arguments:
			wait {bool} -- Whether to wait for other pumps to finish
		
		Returns:
			dict, dict -- Remaining volumes and values to deliver
		"""

		remaining, to_deliver = {}, {}

		# Iterate through items
		for pump_name, set_volume in pump_dict.items():
			# Get the pump and calculate volume
			pump_obj = self.get_pump_object(pump_name)

			# if set_volume > pump_obj.total_volume:
			#     volume = pump_obj.total_volume
			# else:
			#     volume = set_volume
			# This line under here is equivalent of the four lines above! super-cool but more difficoult to read

			volume_to_pump = pump_obj.total_volume if set_volume > pump_obj.total_volume else set_volume

			# Pump the volume
			pump_obj.pump(volume_to_pump, "I")

			# Set deliver to the pumped volume
			to_deliver[pump_name] = volume_to_pump

			# Calculate remaining volume
			remaining[pump_name] = set_volume - volume_to_pump

			# Whether to wait until pump is finished or not
			if wait:
				pump_obj.wait_until_idle()

		return remaining, to_deliver


	def deliver_all(self, pump_dict: dict, wait: bool = False):
		"""
		
		Arguments:
			pump_dict {dict} -- Values to deliver
		
		Keyword Arguments:
			wait {bool} -- Wait until operation is complete or not (default: {False})
		"""
		for pump_name, set_volume in pump_dict.items():
			pump_obj = self.get_pump_object(pump_name)
			pump_obj.deliver(set_volume, "O")
			if wait:
				pump_obj.wait_until_idle()


	def p_transfer(self, pump_dict: dict, pump_wait: bool = False, deliver_wait: bool = False):
		"""Pump and deliver all volumes specified in the pump_dict

		(At the same time)
		
		Arguments:
			pump_dict {dict} -- Values to pump and deliver
		
		Keyword Arguments:
			pump_wait {bool} -- Wait until each pump has drawn in their volume (default: {False})
			deliver_wait {bool} -- Wait until pump has delivered their volume (default: {False})
		"""
		remaining, to_deliver = self.pump_all(pump_dict, wait=pump_wait)
		self.controller.wait_until_all_pumps_idle()
		self.deliver_all(to_deliver, wait=deliver_wait)
		self.controller.wait_until_all_pumps_idle()
		remaining_volumes = sum(remaining.values())
		# print(remaining)

		if remaining_volumes > 0:
			self.p_transfer(remaining, pump_wait=pump_wait, deliver_wait=deliver_wait)


	def s_transfer(self, pump_dict: dict):
		"""Sequentially transfer reagents in pump_dict
		
		Arguments:
			pump_dict {dict} -- Values to transfer
		"""
		for k, v in pump_dict.items():
			pump_obj = self.get_pump_object(k)
			pump_obj.transfer(v, "I", "O")

	def create_BZ_mix(self, total_volume): # With this, we can create bz mix and address it by volume
		volume_1_ml  = total_volume / 140
		bz_mix = {
			"water":volume_1_ml*36, "malonic":volume_1_ml*36,
			"sulfuric":volume_1_ml*25, "bromate":volume_1_ml*38,
			"ferroin": volume_1_ml*5
		}
		#pump_class.s_transfer(bz_mix)
		self.s_transfer(bz_mix)

	def filling_2d(self): # This is just a way to automate the whole system. need to double the amount
		bz_2d = {"bzmix2d1":85, "bzmix2d2":85 }
		for _ in range(2):
			self.create_BZ_mix(140)
			self.p_transfer(bz_2d, pump_wait=False, deliver_wait=False)
		
	def filling_1d(self): # Need to double check the json file
		self.create_BZ_mix(volume=70)
		self.p_transfer(bz_1d, pump_wait=False, deliver_wait=False)

	def cleaning_2d(self):
		bz_waste = {"waste2d2": 110, "waste2d1": 110}
		water_dict = {"water2d1": 80, "water2d2": 80}
		for cyc in range(3):
			self.p_transfer(bz_waste, pump_wait=False, deliver_wait=False)
			self.p_transfer(water_dict, pump_wait=False, deliver_wait=False)

			if cyc == 2:
				print('Completing cleaning cycle')
				self.p_transfer(bz_waste, pump_wait=False, deliver_wait=False)

if __name__ == "__main__":
	pump_controller = TricontControl()

	

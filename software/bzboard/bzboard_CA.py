# ---------------------------------------------------------------------------- #
# --------------- ONE DIMENSIONAL BZ PLATFORM 1 X 7 CONTROLLER --------------- #
# ---------------------------------------------------------------------------- #


"""
	Controls BZ Board using Serial Interface. Each motor can be addressed individually.
    Cell Stirrers: AC
    Interfacial Stirrers: IF
	The 1 x 7 Platform with interface hsa the following nomenclature:

	+ --------------------------------------------------------------+
	|AC1-(IF1)-AC2-(IF2)-AC3-(IF3)-AC4-(IF4)-AC5-(IF5)-AC6-(IF6)-AC7|
	+---------------------------------------------------------------+

"""

import serial, time, json, random, csv
from datetime import datetime
from random import randint, choice
import json, os

class BZBoard:


    def __init__(self, port): # creates objects to pass through function for each self

        self.ser = serial.Serial(port, 9600, timeout=120)
        time.sleep(2) # serial docs recommend a wait just after connection
        self.ser.flush(); self.ser.flushInput(); self.ser.flushOutput();

        #   This is an attempt to change the script for our system
        #   Since Adafruit goes by binary naming, the 'adafruit_shield' below tells the jumper 
        #   setting of adafruit, we have from 0000(being 0)- 1001(being 9)
        self.motors = { # [adafruit_shield, motor]

            "IF1":[0,1],"IF2":[0,2],"IF3":[0,3],"IF4":[0,4],"IF5":[1,1], "IF6":[1,2],
            "AC1":[2,1],"AC2":[2,2],"AC3":[2,3],"AC4":[2,4],"AC5":[3,1],"AC6":[3,2],"AC7":[3,3]
            }

        # this matrix stores if the motors are enabled (1) or disabled (0)
        # before writting to serial we check this to not sent writes not needed
        self.matrix = { 
            "IF1":0,"IF2":0,"IF3":0,"IF4":0,"IF5":0,"IF6":0,
            "AC1":0,"AC2":0,"AC3":0,"AC4":0,"AC5":0,"AC6":0,"AC7":0,
            }
    

    def __del__(self):

        self.disable_all()
        self.ser.close()
        del self.ser
        # disables all motors and clears variables


    def close(self):

        self.disable_all()
        self.ser.close()
        del self.ser
        # seems to do the same 


    def pattern_from_file(self, patternfile):

        with open(patternfile) as f:
            return json.load(f)


    def activate_motor(self, motor_code, direction=0, speed=100):
        ''' code as in A1 or C2 as marked in the actual board. See the dict motors'''

        shield, motor = self.motors[motor_code] # get shield and motor 
        
        # because sometimes we can send here a speed 0 to disable it
        # the following if will be longer than expected
        if self.matrix[motor_code] < 1 and speed > 0: # we need to activate it
            # The following line is a dirty trick. Some of the motors need to be
            # kickstarted at a higher speed
            command = "A%d M%d D%d S255\n" % (shield, motor, direction)
            # and then we send the desired speed
            command += "A%d M%d D%d S%d\n" % ( shield, motor, direction, speed )
            self.matrix[motor_code] = 1 # mark it as enabled
            self.ser.write(command.encode()) # encode helps program run 

        elif self.matrix[motor_code] < 1 and speed == 0: # we keep it disabled (it's off with 0 speed)
            pass

        elif self.matrix[motor_code] > 0 and speed > 0: # just update speed
            command = "A%d M%d D%d S%d\n" % ( shield, motor, direction, speed )
            self.ser.write(command.encode())

        elif self.matrix[motor_code] > 0 and speed == 0: # we disable it (on with no speed)
            self.disable_motor(motor_code)

        else:
            print("something bad happened when updating a motor") # broken


    def activate_all(self, direction=0, speed=100):

        for key in self.motors.keys(): # set to min stiring speed 
            self.activate_motor(key, direction, speed)
            self.ser.flush() #flush variables


    def activate_pattern(self, pattern, speed=None):

        for i in pattern:
            _, _, speed = self.motors[i] 

            if pattern[i] == 1:
                self.activate_motor(i, speed*2) # x5 before
            else:
                self.activate_motor(i, speed*0) # x1 before if motor is off speed off

    
    def activate_pattern_defined_speed(self, pattern, speed):
        #same as above but speed is defined and costatn across motors
        for i in pattern:
            _, _, speed = self.motors[i] 

            if pattern[i] == 1:
                self.activate_motor(i, speed) # x5 before
            else:
                self.activate_motor(i, speed*0) # x1 before if motor is off speed off            
    

    def activate_rand_all(self, filename): #BZ2 won't be using this, at least for now
        '''Activate a random pattern - each motor at a random speed - and append
        this random configuration to the end of the file filename'''

        # random 5*5 speed
        rand_speed = { 
                    "A1":randint(0,255),"A2":randint(0,255),"A3":randint(0,255),"A4":randint(0,255),"A5":randint(0,255),
                    "B1":randint(0,255),"B2":randint(0,255),"B3":randint(0,255),"B4":randint(0,255),"B5":randint(0,255),
                    "C1":randint(0,255),"C2":randint(0,255),"C3":randint(0,255),"C4":randint(0,255),"C5":randint(0,255),
                    "D1":randint(0,255),"D2":randint(0,255),"D3":randint(0,255),"D4":randint(0,255),"D5":randint(0,255),
                    "E1":randint(0,255),"E2":randint(0,255),"E3":randint(0,255),"E4":randint(0,255),"E5":randint(0,255)
                    }

        # enable the motors with the random speeds
        for i in self.motors.keys():
            speed = rand_speed[i]
            self.activate_motor(i, speed)

        self.save_pattern_in_json(rand_speed, filename)
        return rand_speed


    def repeat_rand(self, filename, inspeeds):
        ''' Repeats a random experiment and saves it into the corresponding
        json file'''
    
        # enable the motors with the random speeds
        for i in self.motors.keys():
            speed = inspeeds[i]
            self.activate_motor(i, speed)

        self.save_pattern_in_json(inspeeds, filename)
        return inspeeds


    def activate_rand_single(self, filename):
        '''Activates only 1 motor at a random speed - and append
        this random configuration to the end of the file filename'''

        # first generate dict as before with all 0s
        speeds = { 
                    "A1":0,"A2":0,"A3":0,"A4":0,"A5":0,
                    "B1":0,"B2":0,"B3":0,"B4":0,"B5":0,
                    "C1":0,"C2":0,"C3":0,"C4":0,"C5":0,
                    "D1":0,"D2":0,"D3":0,"D4":0,"D5":0,
                    "E1":0,"E2":0,"E3":0,"E4":0,"E5":0
                    }

        random_motor = choice("ABCDE")+choice("12345") # choice is from random
        speed = randint(0,255)

        # store the speed and activate the motor
        speeds[random_motor] = speed
        # enable the motors with the random speeds
        for i in self.motors.keys():
            speed = speeds[i]
            self.activate_motor(i, speed)

        self.save_pattern_in_json(speeds, filename)
        return speeds
   

    def save_pattern_in_json(self, pattern, filename):
        '''given a dict with all the motors keys and their speeds, and a filename
        it will append this pattern into that filename with a timestamp
        This function was created for the RNN experiments'''
    
        
        # we will use time as keys in the dict
        exp_time = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        filename = filename +'.json'
        # new data entry for the dict
        new_dict = { exp_time : pattern}
        
        # if the file does not exist, meaning its the first experiment
        if os.path.isfile(filename) is False:
            data = new_dict
        
        else:
            # load the previous json to update with new data
            with open(filename) as f:
                data = json.load(f)
                data.update(new_dict)

        # update the json
        with open(filename, 'w') as f:
            json.dump(data, f)


    def disable_motor(self, motor_code):

        shield, motor = self.motors[motor_code]
        command = "A%d M%d D0 S0\n" % ( shield, motor )

        if self.matrix[motor_code] > 0: # so it was enabled
            self.ser.write(command.encode())
            self.matrix[motor_code] = 0 # mark it disabled


    def disable_all(self):

        for key in self.motors.keys():
            self.disable_motor(key)



if __name__ == "__main__":

    b = BZBoard("/dev/ttyACM0")

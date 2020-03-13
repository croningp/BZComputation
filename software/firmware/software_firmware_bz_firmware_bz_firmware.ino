/*
https://learn.adafruit.com/adafruit-motor-shield-v2-for-arduino
Code based on the above adafruit lib
It doesn't have callbacks or error checking, so the user must be
sure everything sent here is OK beforehand.

The commands are like A_ M_ D_ S_
Each argument starts with a capital letter, followed by numbers (value of arg)
Each argument is separated by 1 space
A means Adafruit board. Depends on the assembly, at the moment 7 (0 to 6) (max is 32)
M means motor. Each adafruit board can hold 4 motors. [1-4]
D meand direction. Either 0 or 1.
S means speed, which will define the PWM signal. Max in 255
Commands must end with '\n'
Example: "A4 M2 D0 S100\n"
*/

#include <Wire.h>
#include <Adafruit_MotorShield.h>

#define BUFFER_SIZE 200

// Init adafruit boards
const int n_shields = 12; //not sure whether it starts from 0 or 1, put it at 11 just in case
Adafruit_MotorShield AFMS[n_shields];

// Pointer to motor that will be reused for each motor
Adafruit_DCMotor *myMotor;


// This function only reads from serial and stores the data read in buffer
int read_command(char *buffer)
{

  static int pos = 0;
  int rpos;

  if (Serial.available() > 0) {
    char readch = Serial.read();

    switch (readch) {

      case '\n':
        rpos = pos;
        pos = 0; // Reset position index ready for next time
        return rpos;

      default:

        if (pos < BUFFER_SIZE -1) {
          buffer[pos++] = readch;
          buffer[pos] = '\0';
        } else {
          Serial.println("666"); //buffer overflow
        }
    }
  }
  // no end line or char found, return -1
  return -1;

}


void parse_command(char* command) 
{

  char* parameter;
  parameter = strtok(command, " ");
  long shield, motor, direction, speed;

  while (parameter != NULL) {

    switch(parameter[0]) {

      case 'A':
        shield = strtol(parameter+1, NULL, 10);
        break;

      case 'M':
        motor = strtol(parameter+1, NULL, 10);
        myMotor = AFMS[shield].getMotor(motor);
        break;

      case 'D':
        direction = strtol(parameter+1, NULL, 10);
        if (direction==0) {
          myMotor->run(BACKWARD);
        } else{
          myMotor->run(FORWARD);
        }
        break;

      case 'S':
        speed = strtol(parameter+1, NULL, 10);
        myMotor->setSpeed(speed);
        if (speed == 0) {
          myMotor->run(RELEASE);
        }
        break;

    }
    parameter = strtok(NULL, " ");
  }
  
  for (int x=0; x < BUFFER_SIZE; x++)
    command[x] = '\0';

}


void setup() 
{
  
  Serial.begin(9600);
  Serial.flush();

  uint8_t base = 0x60;
  for (int i=0; i<n_shields; i++){
    AFMS[i] = Adafruit_MotorShield(base+i);
    AFMS[i].begin();
  }
  
}


void loop() 
{
  
  static char buffer[BUFFER_SIZE];

  if (read_command(buffer) > 0)
    parse_command(buffer);
    
}

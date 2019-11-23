
int motor_pin_1 = 2;
int motor_pin_2 = 3;
int motor_pin_3 = 4;
int motor_pin_4 = 5;

int co2_pin = 0;

int current_motor_step = 0;

int human_count = 0;

double co2_level = 0;

void setup(){

pinMode(motor_pin_1, OUTPUT);
pinMode(motor_pin_2, OUTPUT);
pinMode(motor_pin_3, OUTPUT);
pinMode(motor_pin_4, OUTPUT);

Serial.begin(9600);
  
}

void loop(){

  co2_level = analogRead(co2_pin);
  
  co2_level *= 1.953125;
  
  //15 CFM = 600 PPM = 1 Person

  //700 to 1400 PPM - Ideal
  
  moveMotorClockWise(52);

  delay(2000);
  
  moveMotorAntiClockWise(52);

  delay(2000);

}

void moveMotorClockWise(int steps){

  int i;
  
  for(i = 0; i < steps; i++) {

    moveMotor(1,0,1,0);
    delay(10);
    moveMotor(0,1,1,0);
    delay(10);
    moveMotor(0,1,0,1);
    delay(10);
    moveMotor(1,0,0,1);
    delay(10);

  }
  
}

void moveMotorAntiClockWise(int steps){

  int i;
  
  for(i = 0; i < steps; i++) {
    
    moveMotor(1,0,0,1);
    delay(10);
    moveMotor(0,1,0,1);
    delay(10);
    moveMotor(0,1,1,0);
    delay(10);
    moveMotor(1,0,1,0);
    delay(10);

  }
  
}

void moveMotor(int a, int b, int c, int d){

  digitalWrite(motor_pin_1, a);
  digitalWrite(motor_pin_2, b);
  digitalWrite(motor_pin_3, c);
  digitalWrite(motor_pin_4, d);

}


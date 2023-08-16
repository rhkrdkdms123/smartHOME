#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <softPwm.h>

#define TRUE (1==1)
#define FALSE (!TRUE)
#define CHAN_CONFIG_SINGLE 8
#define CHAN_CONFIG_DIFF 0

static int myFd;

void spiSetup (int spiChannel)
{
	if ((myFd = wiringPiSPISetup (spiChannel, 1000000)) < 0)
	{
		fprintf (stderr, "Can't open the SPI bus: %s\n", strerror (errno));
		exit (EXIT_FAILURE) ;
	}
}

int myAnalogRead(int spiChannel,int channelConfig,int analogChannel)
{
	if(analogChannel<0 || analogChannel>7) return -1;
	unsigned char buffer[3] = {1}; // start bit
	buffer[1] = (channelConfig+analogChannel) << 4; 
	wiringPiSPIDataRW(spiChannel, buffer, 3);
	return ( (buffer[1] & 3 ) << 8 ) + buffer[2];
}

int main(void){
	float rainValue;
	float rainVolt;
	int analogChannel=2;
	int spiChannel=1; //CE1
	int channelConfig=CHAN_CONFIG_SINGLE;
	int pos=10;
	int dir=1;
	
	wiringPiSetup () ;
	spiSetup(spiChannel);
	
	pinMode(0,OUTPUT);
	digitalWrite(0,LOW);
	softPwmCreate(0,0,200);
	
	while(1){
		rainValue=myAnalogRead(spiChannel, channelConfig, analogChannel);
		rainVolt=rainValue*5.0/1023;
		
		printf("rainVolt= %f\n",rainVolt);
		
		if(rainVolt<2.0){
			pos+=dir;
			if(pos<10 || pos>20) dir*=-1;
			softPwmWrite(0,pos);
			delay(50);
		}
	}
	
	close(myFd);
	return 0;
}

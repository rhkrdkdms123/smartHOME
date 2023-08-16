#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <pcf8574.h>
#include <lcd.h>

#define TRUE (1==1)
#define FALSE (!TRUE)
#define CHAN_CONFIG_SINGLE 8
#define CHAN_CONFIG_DIFF 0

#define LCD_RS  11     // Register select pin
#define LCD_E   10     // Enable pin
#define LCD_D4  6     // Data pin 4
#define LCD_D5  5     // Data pin 5
#define LCD_D6  4     // Data pin 6
#define LCD_D7  1     // Data pin 7

#define water_pin 25

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

int main (void)
{
	int analogChannel=0;
	int spiChannel=1; //CE1
	int channelConfig=CHAN_CONFIG_SINGLE;
	float rawDust;
	float DustVolt;
	float DustDensityug;
	int lcdHandle;
	char sbuf[16];
	
	wiringPiSetup () ;
	spiSetup(spiChannel);
	
	pcf8574Setup(120, 0x27); 
	pinMode (121, OUTPUT); 
	digitalWrite (121, LOW); 
	pinMode (123, OUTPUT); 
	digitalWrite (123, HIGH); //- Backlight ON
	
	lcdHandle = lcdInit(2, 16, 4, 120, 122, 124, 125, 126, 127, 0,0,0,0 );
	if (lcdHandle < 0) {
        fprintf(stderr, "LCD error\n");
        return 1;
    }
    
    lcdClear(lcdHandle);
	
	while(1)
	{
		digitalWrite(water_pin, HIGH);
		
		rawDust = myAnalogRead(spiChannel, channelConfig, analogChannel);
		/*
		DustVolt = rawDust*5.0/1023.0;
		printf("DustVolt = %.3fV\n", DustVolt);
		delay(1000);
		*/
		DustDensityug=(0.17*(rawDust*(5.0/1024))-0.1)*1000;
		printf("DustDensityug = %.3f[ug/m3]\n", DustDensityug);
		delay(500);
		
		lcdPosition(lcdHandle,0,0);
		lcdPuts(lcdHandle, "DustDensityug: ");
		sprintf(sbuf,"%.3f\n",DustDensityug);
		lcdPosition(lcdHandle, 0, 1);
		lcdPuts(lcdHandle, sbuf);
	}
	close (myFd) ;
	lcdClear(lcdHandle);
    lcdHome(lcdHandle);

	return 0;
}

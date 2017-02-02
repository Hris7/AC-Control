  #!/usr/bin/env python
# coding: utf-8

'''
Created on 28.01.2017

@author: Christopher Köck
'''

import pigpio
import time

import AC_Settings

class WaveGenerator():
    def __init__(self):
        self.pulseArray = []
        self.periodTime = 1000000.0 / AC_Settings.FREQUENCY  # ????
        self.onDuration = int(round(self.periodTime * AC_Settings.DUTY_CYCLE))  # Wielang Hi
        self.offDuration = int(round(self.periodTime * (1.0 - AC_Settings.DUTY_CYCLE)))  # Wielang Lo

    def add_zero(self):
        self.add_high(AC_Settings.ZERO_PULSE_DURATION)
        self.add_low(AC_Settings.ZERO_GAP_DURATION)
    
    def add_one(self):        
        self.add_high(AC_Settings.ONE_PULSE_DURATION)
        self.add_low(AC_Settings.ONE_GAP_DURATION)
    
    def add_low(self, duration):
        self.pulseArray.append(pigpio.pulse(0, 1 << AC_Settings.GPIO_OUT, duration))
        
    def add_high(self, duration):
        totalPeriods = int(round(duration / self.periodTime))
        totalPulses = totalPeriods * 2
        
        for i in range(totalPulses):
            if i % 2 == 0:
                self.pulseArray.append(pigpio.pulse(1 << AC_Settings.GPIO_OUT, 0, self.onDuration))
            else:
                self.pulseArray.append(pigpio.pulse(0, 1 << AC_Settings.GPIO_OUT, self.offDuration))                

class Sender():
    def __init__(self):
        pass
           
    def send(self, pi, commands):
        # Checksum Berechnen
        commandsWithChecksum = list(commands)
        checkSum = 0
        for commandOn in commands:
            checkSum += commandOn  # Alles zusammenzählen
        if len(commands) == 15:
            checkSum = 670 - checkSum  # Summe von ner Magic-Number abziehen
        elif len(commands) == 6:
            checkSum = 406 - checkSum  # Summe von ner Magic-Number abziehen
        else:
            print("ERROR! Can't handle length " + str(len(commands)))
            return 1        
        print "Checksum = " + str(hex(checkSum))
        commandsWithChecksum.append(checkSum)
        
        # Init Waves
        waveIds = [] 
        pi.wave_clear
        
        # Leading Burst
        print "Generating Leading Burst"
        wG = WaveGenerator()
        wG.add_high(AC_Settings.LEADING_PULSE_DURATION)
        wG.add_low(AC_Settings.LEADING_GAP_DURATION)
        pi.wave_add_generic(wG.pulseArray)    
        waveIds.append(pi.wave_create())
        
        # Wellen konfigurieren
        for command in commandsWithChecksum:
            print "Generating " + str(hex(command))
            wG = WaveGenerator()
            commandBinary = bin(command)[2:].zfill(8)  # in Binär umwandel
            commandBinary = commandBinary[::-1]  # Reverse
            for bit in commandBinary:
                if bit == "0":
                    wG.add_zero()
                elif bit == "1":
                    wG.add_one()
            # Wellen generieren       
            pi.wave_add_generic(wG.pulseArray)    
            waveIds.append(pi.wave_create())
            
        # Trailing Pulse
        print "Generating Trailing Pulse"
        wG = WaveGenerator()
        wG.add_high(AC_Settings.ONE_PULSE_DURATION)
        # wG.add_low(LEADING_GAP_DURATION)
        pi.wave_add_generic(wG.pulseArray)    
        waveIds.append(pi.wave_create())    
        
        # Wellen Senden
        print "Send Waves..."
        pi.wave_chain(waveIds)
        while pi.wave_tx_busy():  # wait for waveform to be sent
            print "Waiting..."
            time.sleep(0.1)
        
        # Aufräumen
        for waveId in waveIds:    
            pi.wave_delete(waveId)
        print "Done!"

class SimpleSendIR():
    
    def __init__(self):
        self.lastTick = 0
        print "Connect to Pi. (SimpleSendIR)"
        self.pi = pigpio.pi()  # Connect to Pi.      
        if not self.pi.connected:
            exit(0)

        # set modes
        self.pi.set_mode(AC_Settings.GPIO_OUT, pigpio.OUTPUT)
        self.pi.set_mode(AC_Settings.GPIO_IN, pigpio.INPUT)
        self.pi.set_mode(AC_Settings.GPIO_BUTTON_1, pigpio.INPUT)
        self.pi.set_mode(AC_Settings.GPIO_BUTTON_2, pigpio.INPUT)
        
        # build commandOn
        self.commandOn = [0x14, 0x63, 0x00, 0x10, 0x10, 0xFE, 0x09, 0x30, 0x41, 0x01, 0x00, 0x00, 0x00, 0x00, 0x20]

        # build commandOff
        self.commandOff = [0x14, 0x63, 0x00, 0x10, 0x10, 0x02]
            
        print "Create Callback"
        self.pi.callback(AC_Settings.GPIO_BUTTON_1, pigpio.RISING_EDGE, self.buttonHandler)
        self.pi.callback(AC_Settings.GPIO_BUTTON_2, pigpio.RISING_EDGE, self.buttonHandler)    
        
     
    def buttonHandler(self, gpio, level, tick):
        print "gpio, level, tick = " + str(gpio) + ", " + str(level) + ", " + str(tick)
        tickDiff = pigpio.tickDiff(self.lastTick, tick)
        print str(tickDiff)
        if tickDiff > 1000 * 1000:
            self.lastTick = tick
            if level == 1:
                if(gpio == AC_Settings.GPIO_BUTTON_1):
                    print "Sending commandOn"
                    Sender().send(self.pi, self.commandOn)                 
                if(gpio == AC_Settings.GPIO_BUTTON_2):
                    print "Sending commandOff"
                    Sender().send(self.pi, self.commandOff)
                
if __name__ == '__main__':
    SimpleSendIR()
    while True:
        pass

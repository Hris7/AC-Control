#!/usr/bin/env python
# coding: utf-8

'''
Created on 29.01.2017

@author: Hris
'''

FIELDS = set(["power", "mode", "temp", "fanSpeed", "swing", "setAirflow", "powerful", "economy"])
POWER_VALUES = set(["on", "off", "stay"])
MODE_VALUES = set(["auto", "cool", "dry", "fan", "heat"])
TEMPERATURE_VALUES = set([16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
TEMPERATURE_VALUES_HEAT_ONLY = set([16, 17])
FANSPEED_VALUES = set(["auto", "fan4", "fan3", "fan2", "fan1"])
SWING_VALUES = set(["on", "off"])

TEMPERATURE_MAPPING = {16:0x00, 17:0x10, 18:0x20, 19:0x30, 20:0x40, 21:0x50, 22:0x60, 23:0x70, 24:0x80, 25:0x90, 26:0xA0, 27:0xB0, 28:0xC0, 29:0xD0, 30:0xE0}
MODE_MAPPING = {"auto":0x00, "cool":0x01, "dry":0x02, "fan":0x03, "heat":0x04}
FANSPEED_MAPPING = {"auto":0x00, "fan4":0x01, "fan3":0x02, "fan2":0x03, "fan1":0x04}

# {
#   "power": "on",
#   "mode": "cool",
#   "temp": 20,
#   "fanSpeed": "auto",
#   "swing": "off",
#   "setAirflow": false,
#   "powerful": false,
#   "economy": false
# }

class CommandBuilder():    
    def __init__(self, data):
        self.data = data
        self.command = []
        
    @staticmethod
    def check(data):
        # check if data present
        if data is not None and type(data) == dict:
            
            # check fields present
            fields = set(FIELDS)
            for key in data:
                try:
                    fields.remove(key)
                except KeyError:
                    pass  # Key nicht in Liste -> auch gut
            if len(fields) > 0:
                return "missing fields: " + str(list(fields))
            
            # check power
            power = data["power"]
            print type(power)
            if not isinstance(power, basestring) or power not in POWER_VALUES:
                return "unknown 'power' value: " + str(power)
            
            # check mode
            mode = data["mode"]
            if not isinstance(mode, basestring) or mode not in MODE_VALUES:
                return "unknown 'mode' value: " + str(mode)
            
            # check temperature
            validTemperatureValues = set(TEMPERATURE_VALUES)
            if mode not in set(["heat", "fan"]):  # execlude 16&17 for auto, cool, dry
                validTemperatureValues.difference_update(TEMPERATURE_VALUES_HEAT_ONLY)
            temp = data["temp"]
            if not isinstance(temp, int) or temp not in validTemperatureValues:
                return "invalid temperature " + str(temp) + " for mode " + str(mode)
            
            # check fanSpeed
            fanSpeed = data["fanSpeed"]
            if not isinstance(fanSpeed, basestring) or fanSpeed not in FANSPEED_VALUES:
                return "unknown 'fanSpeed' value: " + str(fanSpeed)
            
            # check swing
            swing = data["swing"]
            if not isinstance(swing, basestring) or swing not in SWING_VALUES:
                return "unknown 'swing' value: " + str(swing)
            
            # check options (setAirflow, powerful, economy)
            setAirflow = data["setAirflow"]
            powerful = data["powerful"]
            economy = data["economy"]
            if not isinstance(setAirflow, bool):
                return "unknown 'setAirflow' value: " + str(setAirflow)
            if not isinstance(powerful, bool):
                return "unknown 'powerful' value: " + str(powerful)
            if not isinstance(economy, bool):
                return "unknown 'economy' value: " + str(economy)
            sumOptions = setAirflow + powerful + economy
            if sumOptions > 1:  # Max. 1 Wert darf True sein
                return "only max. 1 option can be set:" + " setAirflow = " + str(setAirflow) + ", powerful = " + str(powerful) + ", economy = " + str(economy)
            
            # Alles Gut
            return "ok"
        else:
            return "None"

    def build(self):
        # first check
        checkResult = self.check(self.data)
        if checkResult != "ok":
            raise Exception("invalid data")
        
        c = [0x14, 0x63, 0x00, 0x10, 0x10]  # Header
        power = self.data["power"]
        mode = self.data["mode"]
        temp = self.data["temp"]
        fanSpeed = self.data["fanSpeed"]
        swing = self.data["swing"]
        setAirflow = self.data["setAirflow"]
        powerful = self.data["powerful"]
        economy = self.data["economy"]
        if power == "off":
            c.append(0x02)  # Option for Power Off
        elif setAirflow == True:
            c.append(0x6C)  # Option for setAirflow
        elif powerful == True:
            c.append(0x39)  # Option for powerful   
        elif economy == True:
            c.append(0x09)  # Option for economy  
        else:  # not a Option -> Build full Command
            c.extend([0xFE, 0x09, 0x30])  # Constant
            tempCommand = TEMPERATURE_MAPPING[temp]
            if power == "on":
                tempCommand = tempCommand | 0x01
            c.append(tempCommand)  # Temperature / Power On
            modeCommand = MODE_MAPPING[mode]
            c.append(modeCommand)  # Mode
            fanSpeedCommand = FANSPEED_MAPPING[fanSpeed]
            if swing == "on":
                fanSpeedCommand = fanSpeedCommand | 0x10
            c.append(fanSpeedCommand)  # FanSpeed / Swing
            c.append(0x00)  # Timer
            c.append(0x00)  # Timer
            c.append(0x00)  # Timer
            c.append(0x20)  # Timer?
            
        self.command = c
        
        return self.command

#!/usr/bin/env python3
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

import subprocess
from time import strftime
import time
import sys

def sendPvOutput():
    # Upload the data read from Growatt inverter to pvoutput.org
    # see for http://www.pvoutput.org/help.html detajls
    # Curl is required for this action. Refer to: http://curl.haxx.se/
    SYSTEMID="123"
    APIKEY="APIKEY"
    t_date = format(strftime('%Y%m%d'))
    t_time = format(strftime('%H:%M'))
    #Live update data. To be sent every 5 min
    cmd=('curl -d "d=%s" -d "t=%s" -d "v1=%s" -d "v2=%s" -d "v5=%s" -d "v6=%s" -d "c1=0" -H \
    "X-Pvoutput-Apikey: %s" -H \
    "X-Pvoutput-SystemId: %s" \
    http://pvoutput.org/service/r2/addstatus.jsp'\
    %(t_date, t_time, int(Wh_today_calc), out_watts, inverter_temp, pv_volts,\
    APIKEY,SYSTEMID))
    ret = subprocess.call(cmd,shell=True)

def sendDomoticzOutput(watts, whrs):
    cmd=('curl "%s/json.htm?type=command&param=udevice&idx=%s&nvalue=0&svalue=%s;%s"'\
            %('http://192.168.123.123:8080', '66', watts, whrs))
    ret = subprocess.call(cmd,shell=True)

def readRegister(number):
    rr = client.read_input_registers(number,1)
    value=rr.registers
    return float(value[0])

def getRegister(rr, number1, number2=None):
    value=rr.registers
    result=value[number1]
    if (number2):
        result=result << 16
        result+=value[number2]
    return float(result)
    

# READ VALUES FROM MODBUS SERIAL DEVICE (GROWATT INVERTER)
# choose the serial client
client = ModbusClient(method='rtu', port='/dev/ttyUSB0', baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
 
 
lastPvoutput = int(time.time());
lastDomoticzoutput = int(time.time())
lastKwhrCalc = time.time();
Wh_today_last = 0
Wh_today_calc = 0

while (1 == 1):
    rr = client.read_input_registers(0,44) #Read all registers in 1 go
    if not rr.isError():
        pv_watts=getRegister(rr, 1, 2)/10      # Watts delivered by panels (DC side)
        pv_volts=getRegister(rr, 3)/10      # Volts on DC side
        pv_amps=getRegister(rr, 4)/10       # Amps on DC side??? Not sure.
        out_watts=getRegister(rr, 11, 12)/10# Watts delivered by inverter to net
        ac_hz=getRegister(rr, 13)/100       # frequenzy of AC
        ac_volts1=getRegister(rr, 14)/10    # volts (phase 1) on AC side delivered by inverter
        ac_amps1=getRegister(rr, 15)/10     # amps (phase 1) on AC side delivered by inverter
        ac_volts2=getRegister(rr, 18)/10    # volts (phase 2) on AC side delivered by inverter
        ac_amps2=getRegister(rr, 19)/10     # amps (phase 2) on AC side delivered by inverter
        ac_volts3=getRegister(rr, 22)/10    # volts (phase 3) on AC side delivered by inverter
        ac_amps3=getRegister(rr, 23)/10     # amps (phase 3) on AC side delivered by inverter
        Wh_today=getRegister(rr, 27)*100    # Total energy production today
        Wh_total=getRegister(rr, 29)*100    # Total energy production in inervter storage
        inverter_temp=getRegister(rr, 32)/10    
    
        # I don't like the resolution of the energy (rounded to nearest 100Whr)
        # So calculate our own, based on the current power and the time that has past
        if (Wh_today_last != Wh_today):
            Wh_today_last = Wh_today
            Wh_today_calc = Wh_today
        else:
            secondsElapsed = time.time() - lastKwhrCalc;
            lastKwhrCalc = time.time()  
            calcWhr = secondsElapsed * pv_watts / 3600
            Wh_today_calc += calcWhr 
    
        #print("pv_watts: ", pv_watts)
        #print("pv_volts: ", pv_volts)
        #print("pv_amps: ", pv_amps)
        #print("Wh_today: ", Wh_today)
        #print("Wh_today_calc: ", Wh_today_calc)
    
        #print("out_watts: ", out_watts)
        #print("reg11: ", reg11)
        #print("reg12: ", reg12)
    
        #print("ac_hz: ", ac_hz)
        #print("ac_volts1: ", ac_volts1)
        #print("ac_amps1: ", ac_amps1)
        #print("ac_volts2: ", ac_volts2)
        #print("ac_amps2: ", ac_amps2)
        #print("ac_volts3: ", ac_volts3)
        #print("ac_amps3: ", ac_amps3)
        #print("inverter_temp: ", inverter_temp)
    
    
        if ((int(time.time()) - lastDomoticzoutput) > 5):
            sendDomoticzOutput(out_watts, Wh_total)
            lastDomoticzoutput = int(time.time())

        if ((int(time.time()) - lastPvoutput) > 5 * 60):
            sendPvOutput()
            lastPvoutput = int(time.time())

        sys.stdout.flush()

#!/usr/bin/python

import os
import time
import RPi.GPIO as gpio
from evdev import uinput, UInput, ecodes as e
from smbus import SMBus

key = [ # EDIT KEYCODES IN THIS TABLE TO YOUR PREFERENCES:
	# See /usr/include/linux/input.h for keycode names
	# Keyboard        Bonnet        EmulationStation
	e.KEY_UP, 	# 1A            'A' button
	e.KEY_RIGHT, 	# 1B            'B' button
	e.KEY_DOWN,     # 1C            'X' button
	e.KEY_LEFT,       # 1D            'Y' button
	e.KEY_ENTER,    # 1E            'Select' button
	0,        		# 1F            'Start' button
	0,              # Bit 6 NOT CONNECTED on Bonnet
	0              # Bit 7 NOT CONNECTED on Bonnet
]

addr   = 0x20 # I2C Address of MCP23017
irqPin = 26   # IRQ pin for MCP23017

os.system("sudo modprobe uinput")

ui      = UInput({e.EV_KEY: key}, name="retrogame", bustype=e.BUS_USB)
bus     = SMBus(3)
IODIR   = 0x00
IOCON   = 0x05
INTCAP  = 0x08

# Initial MCP23008 config:
bus.write_byte_data(addr, IOCON, 0x44) # seq, OD IRQ

# Read/modify/write remaining MCP23008 config:
cfg = bus.read_i2c_block_data(addr, IODIR, 7)
cfg[ 0] = 0xF # Input bits
cfg[ 1] = 0x0 # Polarity
cfg[ 2] = 0xF # Interrupt pins
cfg[ 6] = 0xF # Pull-ups

bus.write_i2c_block_data(addr, IODIR, cfg)

# Clear interrupt by reading INTCAP and GPIO registers
x        = bus.read_i2c_block_data(addr, INTCAP, 2)
#oldState = x[2] | (x[3] << 8)
oldState = x[1]

# Callback for MCP23017 interrupt request
def mcp_irq(pin):
	global oldState
	x = bus.read_i2c_block_data(addr, INTCAP, 2)
	newState = x[1]
	for i in range(8):
		bit = 1 << i
		lvl = newState & bit
		if lvl != (oldState & bit):
			ui.write(e.EV_KEY, key[i], 0 if lvl else 1)
	ui.syn()
	oldState = newState

# GPIO init
gpio.setwarnings(False)
gpio.setmode(gpio.BCM)

# Enable pullup and callback on MCP23008 IRQ pin
gpio.setup(irqPin, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.add_event_detect(irqPin, gpio.FALLING, callback=mcp_irq)  


while True: time.sleep(1)

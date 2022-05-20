#!/usr/bin/python

import sys
import signal
from CarlosOnEdge import CarlosOnEdge

# Keyboard interrupt handler
def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

my_carlos = CarlosOnEdge()
my_carlos.start()
my_carlos.wait()

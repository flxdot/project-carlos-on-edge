#!/usr/bin/python

import time
import smbus2


class SDL_Pi_SI1145(object):
    """Interface to the SI1145 UV Light Sensor by Adafruit.

    Note: This sensor has a static I2C Address of 0x60.
    """

    # modified for medium range vis, IR SDL December 2016 and non Adafruit I2C (interfers with others)
    # flxdot: modified code structure, July 2019 to fit to project carlos

    # Original Author: Joe Gutting
    #
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be included in
    # all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    # THE SOFTWARE.

    # COMMANDS
    PARAM_QUERY = 0x80
    PARAM_SET = 0xA0
    NOP = 0x0
    RESET = 0x01
    BUSADDR = 0x02
    PS_FORCE = 0x05
    ALS_FORCE = 0x06
    PSALS_FORCE = 0x07
    PS_PAUSE = 0x09
    ALS_PAUSE = 0x0A
    PSALS_PAUSE = 0xB
    PS_AUTO = 0x0D
    ALS_AUTO = 0x0E
    PSALS_AUTO = 0x0F
    GET_CAL = 0x12

    # Parameters
    PARAM_I2CADDR = 0x00
    PARAM_CHLIST = 0x01
    PARAM_CHLIST_ENUV = 0x80
    PARAM_CHLIST_ENAUX = 0x40
    PARAM_CHLIST_ENALSIR = 0x20
    PARAM_CHLIST_ENALSVIS = 0x10
    PARAM_CHLIST_ENPS1 = 0x01
    PARAM_CHLIST_ENPS2 = 0x02
    PARAM_CHLIST_ENPS3 = 0x04

    PARAM_PSLED12SEL = 0x02
    PARAM_PSLED12SEL_PS2NONE = 0x00
    PARAM_PSLED12SEL_PS2LED1 = 0x10
    PARAM_PSLED12SEL_PS2LED2 = 0x20
    PARAM_PSLED12SEL_PS2LED3 = 0x40
    PARAM_PSLED12SEL_PS1NONE = 0x00
    PARAM_PSLED12SEL_PS1LED1 = 0x01
    PARAM_PSLED12SEL_PS1LED2 = 0x02
    PARAM_PSLED12SEL_PS1LED3 = 0x04

    PARAM_PSLED3SEL = 0x03
    PARAM_PSENCODE = 0x05
    PARAM_ALSENCODE = 0x06

    PARAM_PS1ADCMUX = 0x07
    PARAM_PS2ADCMUX = 0x08
    PARAM_PS3ADCMUX = 0x09
    PARAM_PSADCOUNTER = 0x0A
    PARAM_PSADCGAIN = 0x0B
    PARAM_PSADCMISC = 0x0C
    PARAM_PSADCMISC_RANGE = 0x20
    PARAM_PSADCMISC_PSMODE = 0x04

    PARAM_ALSIRADCMUX = 0x0E
    PARAM_AUXADCMUX = 0x0F

    PARAM_ALSVISADCOUNTER = 0x10
    PARAM_ALSVISADCGAIN = 0x11
    PARAM_ALSVISADCMISC = 0x12
    PARAM_ALSVISADCMISC_VISRANGE = 0x10
    # PARAM_ALSVISADCMISC_VISRANGE = 0x00

    PARAM_ALSIRADCOUNTER = 0x1D
    PARAM_ALSIRADCGAIN = 0x1E
    PARAM_ALSIRADCMISC = 0x1F
    PARAM_ALSIRADCMISC_RANGE = 0x20
    # PARAM_ALSIRADCMISC_RANGE = 0x00

    PARAM_ADCCOUNTER_511CLK = 0x70

    PARAM_ADCMUX_SMALLIR = 0x00
    PARAM_ADCMUX_LARGEIR = 0x03

    # REGISTERS
    REG_PARTID = 0x00
    REG_REVID = 0x01
    REG_SEQID = 0x02

    REG_INTCFG = 0x03
    REG_INTCFG_INTOE = 0x01
    REG_INTCFG_INTMODE = 0x02

    REG_IRQEN = 0x04
    REG_IRQEN_ALSEVERYSAMPLE = 0x01
    REG_IRQEN_PS1EVERYSAMPLE = 0x04
    REG_IRQEN_PS2EVERYSAMPLE = 0x08
    REG_IRQEN_PS3EVERYSAMPLE = 0x10

    REG_IRQMODE1 = 0x05
    REG_IRQMODE2 = 0x06

    REG_HWKEY = 0x07
    REG_MEASRATE0 = 0x08
    REG_MEASRATE1 = 0x09
    REG_PSRATE = 0x0A
    REG_PSLED21 = 0x0F
    REG_PSLED3 = 0x10
    REG_UCOEFF0 = 0x13
    REG_UCOEFF1 = 0x14
    REG_UCOEFF2 = 0x15
    REG_UCOEFF3 = 0x16
    REG_PARAMWR = 0x17
    REG_COMMAND = 0x18
    REG_RESPONSE = 0x20
    REG_IRQSTAT = 0x21
    REG_IRQSTAT_ALS = 0x01

    REG_ALSVISDATA0 = 0x22
    REG_ALSVISDATA1 = 0x23
    REG_ALSIRDATA0 = 0x24
    REG_ALSIRDATA1 = 0x25
    REG_PS1DATA0 = 0x26
    REG_PS1DATA1 = 0x27
    REG_PS2DATA0 = 0x28
    REG_PS2DATA1 = 0x29
    REG_PS3DATA0 = 0x2A
    REG_PS3DATA1 = 0x2B
    REG_UVINDEX0 = 0x2C
    REG_UVINDEX1 = 0x2D
    REG_PARAMRD = 0x2E
    REG_CHIPSTAT = 0x30

    # I2C Address
    ADDR = 0x60

    DARKOFFSETVIS = 259
    DARKOFFSETIR = 253

    def __init__(self):
        """Constructor.
        """

        # Create I2C device.
        self._device = smbus2.SMBus(1)

        # reset device
        self._reset()

        # Load calibration values.
        self._load_calibration()

    # device reset
    def _reset(self):
        """Resets the device

        :return:
        """

        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_MEASRATE0, 0)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_MEASRATE1, 0)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_IRQEN, 0)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_IRQMODE1, 0)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_IRQMODE2, 0)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_INTCFG, 0)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_IRQSTAT, 0xFF)

        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_COMMAND, SDL_Pi_SI1145.RESET)
        time.sleep(.01)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_HWKEY, 0x17)
        time.sleep(.01)

    # write Param
    def writeParam(self, p, v):
        """Write Parameter to the Sensor."""

        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_PARAMWR, v)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_COMMAND, p | SDL_Pi_SI1145.PARAM_SET)
        paramVal = self._device.read_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_PARAMRD)
        return paramVal

    # load calibration to sensor
    def _load_calibration(self):
        """Load calibration data."""

        # /***********************************/
        # Enable UVindex measurement coefficients!
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_UCOEFF0, 0x29)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_UCOEFF1, 0x89)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_UCOEFF2, 0x02)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_UCOEFF3, 0x00)

        # Enable UV sensor
        self.writeParam(SDL_Pi_SI1145.PARAM_CHLIST,
                        SDL_Pi_SI1145.PARAM_CHLIST_ENUV | SDL_Pi_SI1145.PARAM_CHLIST_ENALSIR | SDL_Pi_SI1145.PARAM_CHLIST_ENALSVIS | SDL_Pi_SI1145.PARAM_CHLIST_ENPS1)

        # Enable interrupt on every sample
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_INTCFG, SDL_Pi_SI1145.REG_INTCFG_INTOE)
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_IRQEN,
                                     SDL_Pi_SI1145.REG_IRQEN_ALSEVERYSAMPLE)

        # /****************************** Prox Sense 1 */

        # Program LED current
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_PSLED21, 0x03)  # 20mA for LED 1 only
        self.writeParam(SDL_Pi_SI1145.PARAM_PS1ADCMUX, SDL_Pi_SI1145.PARAM_ADCMUX_LARGEIR)

        # Prox sensor #1 uses LED #1
        self.writeParam(SDL_Pi_SI1145.PARAM_PSLED12SEL, SDL_Pi_SI1145.PARAM_PSLED12SEL_PS1LED1)

        # Fastest clocks, clock div 1
        self.writeParam(SDL_Pi_SI1145.PARAM_PSADCGAIN, 0)

        # Take 511 clocks to measure
        self.writeParam(SDL_Pi_SI1145.PARAM_PSADCOUNTER, SDL_Pi_SI1145.PARAM_ADCCOUNTER_511CLK)

        # in prox mode, high range
        self.writeParam(SDL_Pi_SI1145.PARAM_PSADCMISC,
                        SDL_Pi_SI1145.PARAM_PSADCMISC_RANGE | SDL_Pi_SI1145.PARAM_PSADCMISC_PSMODE)
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSIRADCMUX, SDL_Pi_SI1145.PARAM_ADCMUX_SMALLIR)

        # Fastest clocks, clock div 1
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSIRADCGAIN, 0)
        # self.writeParam(SDL_Pi_SI1145.PARAM_ALSIRADCGAIN, 4)

        # Take 511 clocks to measure
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSIRADCOUNTER, SDL_Pi_SI1145.PARAM_ADCCOUNTER_511CLK)

        # in high range mode
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSIRADCMISC, 0)
        # self.writeParam(SDL_Pi_SI1145.PARAM_ALSIRADCMISC, SDL_Pi_SI1145.PARAM_ALSIRADCMISC_RANGE)

        # fastest clocks, clock div 1
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSVISADCGAIN, 0)
        # self.writeParam(SDL_Pi_SI1145.PARAM_ALSVISADCGAIN, 4)

        # Take 511 clocks to measure
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSVISADCOUNTER, SDL_Pi_SI1145.PARAM_ADCCOUNTER_511CLK)

        # in high range mode (not normal signal)
        # self.writeParam(SDL_Pi_SI1145.PARAM_ALSVISADCMISC, SDL_Pi_SI1145.PARAM_ALSVISADCMISC_VISRANGE)
        self.writeParam(SDL_Pi_SI1145.PARAM_ALSVISADCMISC, 0)

        # measurement rate for auto
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_MEASRATE0, 0xFF)  # 255 * 31.25uS = 8ms

        # auto run
        self._device.write_byte_data(SDL_Pi_SI1145.ADDR, SDL_Pi_SI1145.REG_COMMAND, SDL_Pi_SI1145.PSALS_AUTO)

    def readIR(self):
        """returns IR light levels"""
        data = self._device.read_i2c_block_data(SDL_Pi_SI1145.ADDR, 0x24, 2)
        return data[1] * 256 + data[0]

    def readIRLux(self):
        """returns IR light levels in lux"""

        return self.convertIrToLux(self.readIR())

    def readProx(self):
        """Returns "Proximity" - assumes an IR LED is attached to LED"""
        data = self._device.read_i2c_block_data(SDL_Pi_SI1145.ADDR, 0x26, 2)
        return data[1] * 256 + data[0]

    def readUV(self):
        """Returns the UV index * 100 (divide by 100 to get the index)
        """

        data = self._device.read_i2c_block_data(SDL_Pi_SI1145.ADDR, 0x2C, 2)
        # apply additional calibration of /10 based on sunlight
        return (data[1] * 256 + data[0]) / 10

    def readUVindex(self):
        """Returns the UV Index."""

        return self.readUV() / 100

    def readVisible(self):
        """returns visible + IR light levels"""
        data = self._device.read_i2c_block_data(SDL_Pi_SI1145.ADDR, 0x22, 2)
        return data[1] * 256 + data[0]

    def readVisibleLux(self):
        """returns visible + IR light levels in lux"""

        self.convertVisibleToLux(self.readVisible())

    def convertIrToLux(self, ir):
        """Converts IR levels to lux."""

        # irlux = ir * 14.5 / 2.44 for range = high and gain = 1
        # apply dark offset
        ir = ir - SDL_Pi_SI1145.DARKOFFSETIR
        if ir < 0:
            ir = 0

        lux = 2.44
        irlux = 0
        multiplier = 0
        range = 0
        sensitivity = 0
        gain = 1
        # Get gain multipler
        # These are set to defaults in the Adafruit driver - need to change if you change them in the SI1145 driver
        '''
        range = SDL_Pi_SI1145.Read_Param(fd, (unsigned char)ALS_IR_ADC_MISC)
        if ((range & 32) == 32):
            gain = 14.5
        '''
        # gain = 14.5
        # Get sensitivity
        # These are set to defaults in the Adafruit driver - need to change if you change them in the SI1145 driver
        '''
        sensitivity = SDL_Pi_SI1145.Read_Param(fd, (unsigned char)ALS_IR_ADC_GAIN)
        if ((sensitivity & 7) == 0): 
            multiplier = 1
        if ((sensitivity & 7) == 1): 
            multiplier = 2
        if ((sensitivity & 7) == 2): 
            multiplier = 4
        if ((sensitivity & 7) == 3): 
            multiplier = 8
         if ((sensitivity & 7) == 4): 
             multiplier = 16
        if ((sensitivity & 7) == 5): 
            multiplier = 32
        if ((sensitivity & 7) == 6): 
            multiplier = 64
        if ((sensitivity & 7) == 7): 
            multiplier = 128
        '''
        multiplier = 1

        # calibration factor to sunlight applied
        return ir * (gain / (lux * multiplier)) * 50

    def convertUvToIdx(self, uv):
        """Converts the read UV values to UV index."""

        return uv / 100

    def convertVisibleToLux(self, vis):
        """Converts the visible light level to lux."""

        # vislux = vis * 14.5 / 2.44 for range = high and gain = 1
        # apply dark offset
        vis = vis - SDL_Pi_SI1145.DARKOFFSETVIS
        if vis < 0:
            vis = 0

        lux = 2.44
        vislux = 0
        multiplier = 0
        range = 0
        sensitivity = 0
        gain = 1
        # Get gain multipler
        # These are set to defaults in the Adafruit driver - need to change if you change them in the SI1145 driver
        '''
        range = SDL_Pi_SI1145.Read_Param(fd, (unsigned char)ALS_VIS_ADC_MISC)
        if ((range & 32) == 32):
            gain = 14.5
        '''
        # gain = 14.5
        # Get sensitivity
        # These are set to defaults in the Adafruit driver - need to change if you change them in the SI1145 driver
        '''
        sensitivity = SDL_Pi_SI1145.Read_Param(fd, (unsigned char)ALS_VIS_ADC_GAIN)
        if ((sensitivity & 7) == 0): 
            multiplier = 1
        if ((sensitivity & 7) == 1): 
            multiplier = 2
        if ((sensitivity & 7) == 2): 
            multiplier = 4
        if ((sensitivity & 7) == 3): 
            multiplier = 8
         if ((sensitivity & 7) == 4): 
             multiplier = 16
        if ((sensitivity & 7) == 5): 
            multiplier = 32
        if ((sensitivity & 7) == 6): 
            multiplier = 64
        if ((sensitivity & 7) == 7): 
            multiplier = 128
        '''
        multiplier = 1
        # calibration to bright sunlight added
        vislux = vis * (gain / (lux * multiplier)) * 100
        return vislux

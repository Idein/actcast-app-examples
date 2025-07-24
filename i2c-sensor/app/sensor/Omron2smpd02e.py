#!/usr/bin/python
import smbus2  # require pip install
import time
# SMBusモジュールの設定
bus = smbus2.SMBus(20)
# i2c通信の設定     
# Driver for 2SMPD-02E
# https://github.com/omron-devhub/2smpb02e-grove-raspberrypi
# Copyright (c) OMRON Corporation. All rights reserved.
class Omron2smpd02e:

    I2C_ADDR = 0x70
     
    REG_TEMP_TXD0       = 0xfc
    REG_TEMP_TXD1       = 0xfb
    REG_TEMP_TXD2       = 0xfa
    REG_PRESS_TXD0      = 0xf9
    REG_PRESS_TXD1      = 0xf8
    REG_PRESS_TXD2      = 0xf7
    REG_IO_SETUP        = 0xf5
    REG_CTRL_MEAS       = 0xf4
    REG_DEVICE_STAT     = 0xd3
    REG_I2C_SET         = 0xf2
    REG_IIR_CNT         = 0xf1
    REG_RESET           = 0xe0
    REG_CHIP_ID         = 0xd1
    REG_COE_b00_a0_ex   = 0xb8
    REG_COE_a2_0        = 0xb7
    REG_COE_a2_1        = 0xb6
    REG_COE_a1_0        = 0xb5
    REG_COE_a1_1        = 0xb4
    REG_COE_a0_0        = 0xb3
    REG_COE_a0_1        = 0xb2
    REG_COE_bp3_0       = 0xb1
    REG_COE_bp3_1       = 0xb0
    REG_COE_b21_0       = 0xaf
    REG_COE_b21_1       = 0xae
    REG_COE_b12_0       = 0xad
    REG_COE_b12_1       = 0xac
    REG_COE_bp2_0       = 0xab
    REG_COE_bp2_1       = 0xaa
    REG_COE_b11_0       = 0xa9
    REG_COE_b11_1       = 0xa8
    REG_COE_bp1_0       = 0xa7
    REG_COE_bp1_1       = 0xa6
    REG_COE_bt2_0       = 0xa5
    REG_COE_bt2_1       = 0xa4
    REG_COE_bt1_0       = 0xa3
    REG_COE_bt1_1       = 0xa2
    REG_COE_b00_0       = 0xa1
    REG_COE_b00_1       = 0xa0
 
    AVG_SKIP    = 0x0
    AVG_1       = 0x1
    AVG_2       = 0x2
    AVG_4       = 0x3
    AVG_8       = 0x4
    AVG_16      = 0x5
    AVG_32      = 0x6
    AVG_64      = 0x7
 
    MODE_SLEEP  = 0x0
    MODE_FORCED = 0x1
    MODE_NORMAL = 0x3
 
    def __init__(self,address=0x70):
        self.I2C_ADDR = address
        self.writeByteData(0xf5, 0x00)
        time.sleep(0.5)
        self.setAverage(self.AVG_1,self.AVG_1)
 
    def writeByteData(self,address,data):
        bus.write_byte_data(self.I2C_ADDR, address, data)
 
    def readByte(self,addr):
        data = bus.read_i2c_block_data(self.I2C_ADDR, addr, 1)
        return data[0]
 
    def readByteData(self,addr,num):
        data = bus.read_i2c_block_data(self.I2C_ADDR, addr, num)
        return data
 
    def setAverage(self,avg_tem,avg_pressure):
        bus.write_byte_data(self.I2C_ADDR, self.REG_CTRL_MEAS, 0x27)
 
    def readRawTemp(self):
        temp_txd2 = self.readByte(self.REG_TEMP_TXD2)
        temp_txd1 = self.readByte(self.REG_TEMP_TXD1)
        temp_txd0 = self.readByte(self.REG_TEMP_TXD0)
        Dt = (temp_txd2 << 16 | temp_txd1 << 8 | temp_txd0) - pow(2,23)
        return Dt
 
    def readRawPress(self):
        press_txd2 = self.readByte(self.REG_PRESS_TXD2)
        press_txd1 = self.readByte(self.REG_PRESS_TXD1)
        press_txd0 = self.readByte(self.REG_PRESS_TXD0)
        Dp = (press_txd2 << 16 | press_txd1 << 8 | press_txd0) - pow(2,23)
        return Dp
 
    def readTr(self):
        Dt = self.readRawTemp()
        coe_a0 = self.readByteData(self.REG_COE_a0_1, 2)
        b00_a0_ex = self.readByteData(self.REG_COE_b00_a0_ex, 1)
        a0 = (coe_a0[0] << 12 | coe_a0[1] << 4 | b00_a0_ex[0] & 0x0f)
        a0 = -(a0 & 0b10000000000000000000) | (a0 & 0b01111111111111111111)
        a0 = self.conv_K1(a0)
 
        data = self.readByteData(self.REG_COE_a1_1, 2)
        a1 = (data[0] << 8 | data[1])
        a1 = -(a1 & 0b1000000000000000) | (a1 & 0b0111111111111111)
        a1 = self.conv_K0(a1, -6.3e-3, 4.3e-4)
 
        data = self.readByteData(self.REG_COE_a2_1, 2)
        a2 = (data[0] << 8 | data[1])
        a2 = -(a2 & 0b1000000000000000) | (a2 & 0b0111111111111111)
        a2 = self.conv_K0(a2, -1.9e-11, 1.2e-10)       
 
        Tr = a0 + (a1 + a2 * Dt) * Dt
        return Tr
 
    def readData(self):
        Dp = self.readRawPress()
        Tr = self.readTr()
 
        coe_b00 = self.readByteData(self.REG_COE_b00_1, 2)
        b00_a0_ex = self.readByteData(self.REG_COE_b00_a0_ex, 1)
        b00 = (coe_b00[0] << 12 | coe_b00[1] << 4 | b00_a0_ex[0] >> 4)
        b00 = -(b00 & 0b10000000000000000000) | (b00 & 0b01111111111111111111)
        b00 = self.conv_K1(b00)
 
        data = self.readByteData(self.REG_COE_bt1_1, 2)
        bt1 = (data[0] << 8 | data[1])
        bt1 = -(bt1 & 0b1000000000000000) | (bt1 & 0b0111111111111111)
        bt1 = self.conv_K0(bt1, 1.0e-1, 9.1e-2)
         
        data = self.readByteData(self.REG_COE_bt2_1, 2)
        bt2 = (data[0] << 8 | data[1])
        bt2 = -(bt2 & 0b1000000000000000) | (bt2 & 0b0111111111111111)
        bt2 = self.conv_K0(bt2, 1.2e-8, 1.2e-6)
 
        data = self.readByteData(self.REG_COE_bp1_1, 2)
        bp1 = (data[0] << 8 | data[1])
        bp1 = -(bp1 & 0b1000000000000000) | (bp1 & 0b0111111111111111)
        bp1 = self.conv_K0(bp1, 3.3e-2, 1.9e-2)
 
        data = self.readByteData(self.REG_COE_b11_1, 2)
        b11 = (data[0] << 8 | data[1])
        b11 = -(b11 & 0b1000000000000000) | (b11 & 0b0111111111111111)
        b11 = self.conv_K0(b11, 2.1e-7, 1.4e-7)
 
        data = self.readByteData(self.REG_COE_bp2_1, 2)
        bp2 = (data[0] << 8 | data[1])
        bp2 = -(bp2 & 0b1000000000000000) | (bp2 & 0b0111111111111111)
        bp2 = self.conv_K0(bp2, -6.3e-10, 3.5e-10)
 
        data = self.readByteData(self.REG_COE_b12_1, 2)
        b12 = (data[0] << 8 | data[1])
        b12 = -(b12 & 0b1000000000000000) | (b12 & 0b0111111111111111)
        b12 = self.conv_K0(b12, 2.9e-13, 7.6e-13)
 
        data = self.readByteData(self.REG_COE_b21_1, 2)
        b21 = (data[0] << 8 | data[1])
        b21 = -(b21 & 0b1000000000000000) | (b21 & 0b0111111111111111)
        b21 = self.conv_K0(b21, 2.1e-15, 1.2e-14)
 
        data = self.readByteData(self.REG_COE_bp3_1, 2)
        bp3 = (data[0] << 8 | data[1])
        bp3 = -(bp3 & 0b1000000000000000) | (bp3 & 0b0111111111111111)
        bp3 = self.conv_K0(bp3, 1.3e-16, 7.9e-17)
 
        Pr = b00 + bt1 * Tr + bp1 * Dp + b11 * Dp * Tr + bt2 * pow(Tr,2) + bp2 * pow(Dp,2) + b12 * Dp * pow(Tr,2) + b21 * pow(Dp,2) * Tr + bp3 * pow(Dp,3)
 
        press = Pr / 100.0
        temp = Tr / 256.0
 
        return press, temp
 
    def conv_K0(self,x,a,s):
        return (a + (((s * float(x)) / 32767.0)))
 
    def conv_K1(self,x):
        return (float(x) / 16.0)


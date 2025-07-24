#!/usr/bin/python
import smbus2  # require pip install
import time
# SMBusモジュールの設定
bus = smbus2.SMBus(0)



# (c) Copyright 2019 Sensirion AG, Switzerland
#0x31(0x131)（x^8 + x^5 + x^4 + 1）
class CrcCalculator(object):

    def __init__(self, width=8, polynomial=0x31, init_value=0xFF, final_xor=0x00):

        super(CrcCalculator, self).__init__()
        self._width = width
        self._polynomial = polynomial
        self._init_value = init_value
        self._final_xor = final_xor

    def calc(self, data):

        crc = self._init_value
        for value in data:
            crc ^= value
            for i in range(self._width):
                if crc & (1 << (self._width - 1)):
                    crc = (crc << 1) ^ self._polynomial
                else:
                    crc = crc << 1
                crc &= (1 << self._width) - 1
        return crc ^ self._final_xor



# i2c通信の設定     
# SHT30(温湿度センサ)の測定
class SHT3x:

    #SHT3x command
    CMD_READ_SERIALNBR  = [0x37, 0x80]  # read serial number
    CMD_READ_STATUS     = [0xF3, 0x2D]  # read status register
    CMD_CLEAR_STATUS    = [0x30, 0x41]  # clear status register
    CMD_HEATER_ENABLE   = [0x30, 0x6D]  # enabled heater
    CMD_HEATER_DISABLE  = [0x30, 0x66]  # disable heater
    CMD_SOFT_RESET      = [0x30, 0xA2]  # soft reset
    CMD_MEAS_CLOCKSTR_H = [0x2C, 0x06]  # measurement: clock stretching  high repeatability
    CMD_MEAS_CLOCKSTR_M = [0x2C, 0x0D]  # measurement: clock stretching  medium repeatability
    CMD_MEAS_CLOCKSTR_L = [0x2C, 0x10]  # measurement: clock stretching  low repeatability
    CMD_MEAS_POLLING_H  = [0x24, 0x00]  # measurement: polling  high repeatability
    CMD_MEAS_POLLING_M  = [0x24, 0x0B]  # measurement: polling  medium repeatability
    CMD_MEAS_POLLING_L  = [0x24, 0x16]  # measurement: polling  low repeatability
    CMD_MEAS_PERI_05_H  = [0x20, 0x32]  # measurement: periodic 0.5 mps  high repeatability
    CMD_MEAS_PERI_05_M  = [0x20, 0x24]  # measurement: periodic 0.5 mps  medium repeatability
    CMD_MEAS_PERI_05_L  = [0x20, 0x2F]  # measurement: periodic 0.5 mps  low repeatability
    CMD_MEAS_PERI_1_H   = [0x21, 0x30]  # measurement: periodic 1 mps  high repeatability
    CMD_MEAS_PERI_1_M   = [0x21, 0x26]  # measurement: periodic 1 mps  medium repeatability
    CMD_MEAS_PERI_1_L   = [0x21, 0x2D]  # measurement: periodic 1 mps  low repeatability
    CMD_MEAS_PERI_2_H   = [0x22, 0x36]  # measurement: periodic 2 mps  high repeatability
    CMD_MEAS_PERI_2_M   = [0x22, 0x20]  # measurement: periodic 2 mps  medium repeatability
    CMD_MEAS_PERI_2_L   = [0x22, 0x2B]  # measurement: periodic 2 mps  low repeatability
    CMD_MEAS_PERI_4_H   = [0x23, 0x34]  # measurement: periodic 4 mps  high repeatability
    CMD_MEAS_PERI_4_M   = [0x23, 0x22]  # measurement: periodic 4 mps  medium repeatability
    CMD_MEAS_PERI_4_L   = [0x23, 0x29]  # measurement: periodic 4 mps  low repeatability
    CMD_MEAS_PERI_10_H  = [0x27, 0x37]  # measurement: periodic 10 mps  high repeatability
    CMD_MEAS_PERI_10_M  = [0x27, 0x21]  # measurement: periodic 10 mps  medium repeatability
    CMD_MEAS_PERI_10_L  = [0x27, 0x2A]  # measurement: periodic 10 mps  low repeatability
    CMD_FETCH_DATA      = [0xE0, 0x00]  # readout measurements for periodic mode
    CMD_R_AL_LIM_LS     = [0xE1, 0x02]  # read alert limits  low set
    CMD_R_AL_LIM_LC     = [0xE1, 0x09]  # read alert limits  low clear
    CMD_R_AL_LIM_HS     = [0xE1, 0x1F]  # read alert limits  high set
    CMD_R_AL_LIM_HC     = [0xE1, 0x14]  # read alert limits  high clear
    CMD_W_AL_LIM_HS     = [0x61, 0x1D]  # write alert limits  high set
    CMD_W_AL_LIM_HC     = [0x61, 0x16]  # write alert limits  high clear
    CMD_W_AL_LIM_LC     = [0x61, 0x0B]  # write alert limits  low clear
    CMD_W_AL_LIM_LS     = [0x61, 0x00]  # write alert limits  low set
    CMD_NO_SLEEP        = [0x30, 0x3E]  #

    I2C_ADDR = 0x44
    
    def __init__(self, address=0x44):
        self.I2C_ADDR = address
        # CrcCalculatorのインスタンスを作成
        self.crc8 = CrcCalculator()
        bus.write_byte_data(self.I2C_ADDR, *self.CMD_MEAS_PERI_1_H)
    
    def readData(self):
        # 測定データ取込みコマンド
        bus.write_byte_data(self.I2C_ADDR, *self.CMD_FETCH_DATA)
        time.sleep(0.1)
        data = bus.read_i2c_block_data(self.I2C_ADDR, 0x00, 6)

        # crc8.calcメソッドをself.crc8.calcに変更
        crc1 = data[2]
        crc2 = data[5]
        calc1 = self.crc8.calc(data[0:2])
        calc2 = self.crc8.calc(data[3:5])
        if crc1 == calc1 and crc2 == calc2:
            # 温度計算
            # T[℃] = -45 +175*St/(2^16-1)
            temp_mlsb = ((data[0] << 8) | data[1])
            temp = -45 + 175 * int(str(temp_mlsb), 10) / (pow(2, 16) - 1)

            # 湿度計算
            # RH = 100*Srh/(2^16-1)
            humi_mlsb = ((data[3] << 8) | data[4])
            humi = 100 * int(str(humi_mlsb), 10) / (pow(2, 16) - 1)
        else:
            print ("CRC Error")
            temp = -300
            humi = -300
        return [temp, humi]

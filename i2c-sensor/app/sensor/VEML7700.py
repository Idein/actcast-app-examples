#!/usr/bin/python
import smbus2  # require pip install
import time
# SMBusモジュールの設定
bus = smbus2.SMBus(1)
# i2c通信の設定     
#VEML7700
class VEML7700:

    #クラス変数
    I2C_ADDR = 0x70
    
    #VEML7700 regidters
    ALS_CONF_0 = 0x00 #ALS gain, integration time, interrupt, and shutdown
    ALS_WH = 0x01     #ALS high threshold window setting
    ALS_WL = 0x02     #ALS low threshold window setting
    POW_SAV = 0x03    #Set (15 : 3) 0000 0000 0000 0b
    ALS = 0x04        #ALS 16 bits(R) 
    WHITE = 0x05      #White 16 bits(R) 
    INTERRUPT = 0x06  #ALS INT trigger event(R)  

    # These settings will provide the max range for the sensor (0-120Klx)
    # but at the lowest precision:
    #              LSB   MSB
    confValues = [0x00, 0x13] # 1/8 gain, 25ms IT (Integration Time)
    #Reference data sheet Table 1 for configuration settings

    interrupt_high = [0x00, 0x00] # Clear values
    #Reference data sheet Table 2 for High Threshold

    interrupt_low = [0x00, 0x00] # Clear values
    #Reference data sheet Table 3 for Low Threshold

    power_save_mode = [0x00, 0x00] # Clear values
    #Reference data sheet Table 4 for Power Saving Modes
    def __init__(self, address=0x70):
        
        self.I2C_ADDR = address
        
        bus.write_i2c_block_data(self.I2C_ADDR , self.ALS_CONF_0, self.confValues)
        bus.write_i2c_block_data(self.I2C_ADDR , self.ALS_WH, self.interrupt_high)
        bus.write_i2c_block_data(self.I2C_ADDR , self.ALS_WL, self.interrupt_low)
        bus.write_i2c_block_data(self.I2C_ADDR , self.POW_SAV, self.power_save_mode)
    
    def readData(self):
        time.sleep(0.04) # 40ms 

        word = bus.read_word_data(self.I2C_ADDR ,self.ALS)

        gain = 1.8432 #Gain for 1/8 gain & 25ms IT
        #Reference www.vishay.com/docs/84323/designingveml7700.pdf
        # 'Calculating the LUX Level'

        val = word * gain
        val = round(val,1) #Round value for presentation
        return (val)


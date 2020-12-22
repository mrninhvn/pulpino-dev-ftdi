#!/usb/bin/env python3
from pyftdi.spi import *
from pyftdi.usbtools import UsbTools
import binascii
import argparse
import sys
# Instantiate a SPI controller
## pulpino SPI Slave regs (8-bit width)
## reg 0: bit 0 enables qpi
## reg 1: number of dummy cylces (default = 32)
## reg 2: wrap length, low
## reg 3: wrap length, high

READ_REG_CMD = [0x05, 0x07, 0x21, 0x31]
READ_MEM_CMD=0x0B
WRITE_REG_CMD = [0x01, 0x11, 0x20, 0x30]
WRITE_MEM_CMD=0x02

# Request the JEDEC ID from the SPI slave
def int_to_byte_array(i,num_bytes):
    f = '{:0' + str(num_bytes*2) + 'x}'
    return bytearray.fromhex(f.format(i))
def data_to_byte_array(data):
    return bytearray([ int(data[i:i+2],16) for i in range(0, len(data),2)])
def read_all_regs(spi_slave):
    for i in range(0,4):
        print(binascii.hexlify(spi_slave.exchange([READ_REG_CMD[i]],4)))
def read_spi_slave_configs(spi_slave):
    regs = []
    for i in range(0,4):
        regs.append(spi_slave.exchange([READ_REG_CMD[i]],4))
    return regs
def get_num_dummy_cycles(spi_slave):
    return int(spi_slave.exchange([READ_REG_CMD[1]],4)[3])
def read_mem(spi_slave, address, data_len):
    ## only support 4-byte address
    cmd = int_to_byte_array(READ_MEM_CMD,1) + int_to_byte_array(address, 4)
    print("cmd: %s" %cmd)
    r = spi_slave.exchange(cmd, data_len+4)
    return r[4:len(r)]
def write_mem(spi_slave, address, data):
    cmd = int_to_byte_array(WRITE_MEM_CMD,1) + int_to_byte_array(address, 4) + data_to_byte_array(data)
    spi_slave.exchange(cmd,0)
def read_stim(spi_stim_file):
    with open(spi_stim_file, 'r') as f:
        prev_addr = "00000000"
        start_addr = "00000000"
        data_dict = {}
        data_dict[start_addr] = ""
        for l in f:
            address, data = l.strip().split("_")
            if int(address,16) != int(prev_addr,16)+4:
                start_addr = address
                prev_addr = start_addr
                data_dict[start_addr] = data
            else:
                prev_addr = address
                data_dict[start_addr] += data
    return data_dict
def test_mem1():
    spi = SpiController()

    # Configure the first interface (IF/1) of the FTDI device as a SPI master
    spi.configure('ftdi://ftdi:2232:3:1a/1')

    # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
    
    slave = spi.get_port(cs=0, freq=4E6, mode=0)
    spi_configs = read_spi_slave_configs(slave)
    read_mem(slave,0x1a107008,16)
    # read_all_regs(slave)
    # read_info(slave)
def program_pulpino(slave, stim_file):
    print("Programming pulpino core")
    print("Firstly, set the dummy cycles to 31")
    slave.exchange([WRITE_REG_CMD[1], 0x1f], 0)
    
    data = read_stim(stim_file)
    for addr in data:
        # print(addr, data[addr], len(data[addr])/2.0)
        # data_to_byte_array(data[addr])
        print("Write to address: %s size: %d" % (addr, len(data[addr])/2.0))
        write_mem(slave, int(addr,16), data[addr])
    print("Check if write is successful")
    for addr in data:
        print("Length: %d" % (len(data[addr])/2))
        ret = read_mem(slave, int(addr,16), int(len(data[addr])/2))
        print("Read from address: %s size: %d" % (addr, len(ret)))
        if ret == data_to_byte_array(data[addr]):
            print("Data is good")
        else:
            print("Data is bad: orig: %d; target: %d" % (len(data[addr])/2.0, len(ret)))
    print("Set boot loader address to %08X" % (0))
    write_mem(slave, 0x1a107008, "00000000")
    print("Boot address: ", binascii.hexlify(read_mem(slave, 0x1a107008, 4)))

def test_stim_file(filename):
    spi = SpiController()

    # Configure the first interface (IF/1) of the FTDI device as a SPI master
    spi.configure('ftdi://ftdi:2232:3:1e/2')

    # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
    
    slave = spi.get_port(cs=0, freq=4E6, mode=0)
    program_pulpino(slave,filename)
def test_write_mem():
    spi = SpiController()

    # Configure the first interface (IF/1) of the FTDI device as a SPI master
    spi.configure('ftdi://ftdi:2232:3:1a/1')

    # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
    
    slave = spi.get_port(cs=0, freq=4E6, mode=0)
    slave.exchange([WRITE_REG_CMD[1], 0x1f], 0)
    # write_mem(slave, 0, "0000001300000013")
    read_all_regs(slave)
    write_mem(slave, 0x0, "0102030405060708")
    print(read_mem(slave, 0, 16))
def test_read_boot():
    spi = SpiController()

    # Configure the first interface (IF/1) of the FTDI device as a SPI master
    spi.configure('ftdi://ftdi:2232:3:1a/1')

    # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
    
    slave = spi.get_port(cs=0, freq=4E6, mode=0)
    slave.exchange([WRITE_REG_CMD[1], 0x1f], 0)
    print(binascii.hexlify(slave.exchange([READ_REG_CMD[1]], 4)))
    # write_mem(slave, 0, "0000001300000013")
    # while True:
    print(binascii.hexlify(slave.exchange([0x0B, 0x1a, 0x10, 0x70, 0x10], 8, duplex=False)))
        # slave.exchange([0x0b, 0x1a, 0x10, 0x70, 0x10], 0)
        # print(binascii.hexlify(slave.exchange([0x0, 0x0, 0x0, 0x0],4)))
def test_defaults():
    spi = SpiController()

    # Configure the first interface (IF/1) of the FTDI device as a SPI master
    spi.configure('ftdi://ftdi:2232:3:1a/1')

    # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
    
    slave = spi.get_port(cs=0, freq=4E6, mode=0)
    ## config the dummy cycles of pulpino to 31 
    slave.exchange([WRITE_REG_CMD[1], 0x1f], 0)
    read_all_regs(slave)
    print("SoC control regs")
    print(read_mem(slave, 0x1a107008, 32))
def test_debug(spi):
    pass
def list_devices():
    from pyftdi.ftdi import Ftdi
    Ftdi().open_from_url('ftdi:///?')
def get_info(info):
    print(info)
    version = int(info,16) & 0x1f
    dsize = ((int(info,16) >> 5) & 0xff)*8
    isize = ((int(info,16) >> 13) & 0xff)*8
    rsize = ((int(info,16) >> 21) & 0x1f)*8
    print("Version: %s\nDMEM size: %s (kB)\nIMEM size: %s (kB)\nROM size: %s" % (version, dsize, isize, rsize))
# def parse_args():
#     parser = argparse.ArgumentParser(description='Programming pulpino through FTDI 2232H device')
#     parser.add_argument('--list-devices', dest='list_devices', action='store_const')
if __name__ == '__main__':
    spi = SpiController()

    # Configure the first interface (IF/1) of the FTDI device as a SPI master
    spi.configure(sys.argv[1])
    # slave = spi.get_port(cs=0, freq=4E6, mode=0)
    # program_pulpino(slave, sys.argv[2])

    # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
    
    slave = spi.get_port(cs=0, freq=4E6, mode=0)
    gpio = spi.get_gpio()
    gpio.set_direction(0x30, 0x10)
    gpio.write(0x00)
    slave.exchange([WRITE_REG_CMD[1], 0x1f], 0)
    get_info(binascii.hexlify(read_mem(slave, 0x1a107010,4)))
    print("Boot addr: %s" % binascii.hexlify(read_mem(slave, 0x1a107008,4)))

    program_pulpino(slave, sys.argv[2])
    get_info(binascii.hexlify(read_mem(slave, 0x1a107010,4)))

    print("Boot addr: %s" % binascii.hexlify(read_mem(slave, 0x1a107008,4)))

    
    
    # list_devices()
    # find_ftdi2232h_mini()
    # test_stim_file('spi_stim.txt')
    # test_write_mem()
    # test_read_boot()
    # test_defaults()


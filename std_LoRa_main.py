import numpy as np
# from Demodulators import Demodulators #.Standard_LoRa.Std_LoRa import Std_LoRa
import multiprocessing
# from Client import *
from Client.utils import *
from Client.Active_Period_Detector import Active_Period_Detector
import time


In_Q = multiprocessing.Queue()
Out_Q = multiprocessing.Queue()

def main():

    payload_num = 100  # config.Max_Payload_Num
    check_crc = 1
    num_preamble = 8
    num_sync = 2
    preamble_sym = 1
    num_data_sym = payload_num
    num_DC = 2.25
    pkt_len = num_preamble + num_DC + num_data_sym + 2
    Fs = 500e3  # config.RX_Sampl_Rate
    BW = 125e3  # config.LORA_BW
    upsampling_factor = Fs // BW

    # Load raw signal
    raw_data = np.fromfile('C:/Osama/ACCIO/Data/1chan_Dan_test', dtype=np.complex64)
    rx_pkt_num = list()

    APD = Active_Period_Detector(In_Q, Out_Q)
    SF = 7
    N = int(2 ** SF)
    chunk = raw_data[0 : 10 * upsampling_factor * N]
    APD.configNF(chunk, 'low')
    uplink_wind = APD.Active_Sess_Detect2(raw_data, 'low')
    print(len(uplink_wind))

    # for SF in [7, 8, 9]:
    #
    #     N = int(2 ** SF)
    #
    #     print(f'Data Samples: {raw_data.size}; SF = {SF}; BW = {BW}Hz')
    #
    #     std = Std_LoRa(num_preamble, num_sync, num_DC, num_data_sym, check_crc)
    #     # std.Evaluate(raw_data, SF, BW, Fs, True)
    #
    #     pkt_starts = std.pkt_detection(raw_data, SF, BW, Fs, num_preamble)
    #     print(f'Number of SF {SF} pkts Detected: {len(pkt_starts)}')
    #     demod_sym = std.lora_demod(raw_data, SF, BW, Fs, num_preamble, num_sync, num_DC,
    #                                      num_data_sym, pkt_starts)
    #     std.demod_sym = np.mod(demod_sym, N)
    #     std.pkt_starts = pkt_starts
    #     print(f'Number of SF {SF} pkts Demodulated: {len(demod_sym)}')
    #     final_data = std.decode(SF, False)
    #     print(f'Number of SF {SF} pkts Decoded: {len(final_data)}')
    #     for i in final_data:
    #         rx_pkt_num.append(i[2][10])
    #
    # print(rx_pkt_num)
    # rx_pkt_num.sort()
    # print(rx_pkt_num)
    # sourceFile = open('demo.txt', 'w')
    # for i in rx_pkt_num:
    #     print(i, file=sourceFile)
    # sourceFile.close()

if __name__ == '__main__':
    main()

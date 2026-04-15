from Demodulators.Demod_Interface import Demod_Interface
import numpy as np
import math
from .decode import lora_decoder
from .DC_gen import DC_gen
from .sym_to_data_ang import sym_to_data_ang
from .dnsamp_buff import dnsamp_buff
import matplotlib.pyplot as plt

class Std_LoRa():
    def __init__(self, num_preamble, num_sync, num_DC, num_data_sym, check_crc):
        self.num_preamble = num_preamble
        self.num_sync = num_sync
        self.num_DC = num_DC
        self.num_data_sym = num_data_sym
        self.check_crc = check_crc

        self.pkt_starts = []
        self.demod_sym = []

    def Evaluate(self, Rx, SF: int, BW: int, FS: int, PRINT: False):
        [pkt_start, demod_sym] = self.demodulate(Rx, SF, BW, FS)
        return [pkt_start, demod_sym, self.decode(SF, PRINT)]

    def Evaluate2(self, Rx, SF: int, BW: int, FS: int, PRINT: False):
        self.demodulate2(Rx, SF, BW, FS)
        return self.decode(SF, PRINT)


    def EvaluateRLO(self, Rx, SF: int, BW: int, FS: int, PRINT: False):
        self.demodulate(Rx, SF, BW, FS)
        return self.decodeRLO(SF, PRINT)

    def decode(self, SF, PRINT):
        decoded_packets = 0
        final_data = []

        if len(self.demod_sym) > 0 and len(self.demod_sym[0]) > 0:
            for i, syms in enumerate(self.demod_sym):
                if SF <= 10:
                    # dem = mod(dem - 2, 2 ^ SF)
                    message = lora_decoder(np.mod(np.add(syms, -1), (2 ** SF)), SF, self.check_crc)
                else:
                    # dem = mod(dem - 1, 2 ^ SF)
                    message = lora_decoder(np.mod(np.add(syms, 0), (2 ** SF)), SF, self.check_crc)
                # message = lora_decoder(np.mod(np.add(syms, -1), (2**SF)), SF, self.check_crc)
                if message is not None:
                    decoded_packets += 1
                    final_data.append((self.pkt_starts[i], self.demod_sym[i], message))
            final_data = self.remove_sim(final_data, 10 * (2 ** SF))

        self.demod_sym = []
        self.pkt_starts = []
        if PRINT:
            for d in final_data:
                print(d[2].tolist())
                #print(''.join([chr(int(c)) for c in d[2][7:]]))

        return final_data

    def demodulate(self, Rx, SF: int, BW: int, FS: int) -> list:
        self.pkt_starts = self.pkt_detection(Rx, SF, BW, FS, self.num_preamble)
        # print(self.pkt_starts)
        self.demod_sym = self.lora_demod(Rx, SF, BW, FS, self.num_preamble, self.num_sync, self.num_DC,
                                         self.num_data_sym, self.pkt_starts)
        return [self.pkt_starts, self.demod_sym]

    def demodulate2(self, Rx, SF: int, BW: int, FS: int) -> list:
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        self.pkt_starts = self.pkt_detection(Rx, SF, BW, FS, self.num_preamble)
        Rx = Rx[int(self.pkt_starts - (2*N*upsampling_factor) - 1):len(Rx)]
        temp_buff = Rx[:(len(Rx) // upsampling_factor) * upsampling_factor]

        Rx_Buff_dnsamp = []
        for i in range(upsampling_factor):
            Rx_Buff_dnsamp.append(temp_buff[i::upsampling_factor])
        Rx_Buff_dnsamp = np.array(Rx_Buff_dnsamp)
        Upchirp_ind = []
        Upchirp_ind.append(np.arange(2*N, ((self.num_preamble + 1) * N) + 1, N))
        print(Upchirp_ind)
        [Data_freq_off, Peak, Upchirp_ind, FFO] = dnsamp_buff(Rx_Buff_dnsamp, Upchirp_ind, SF)
        # if Upchirp_ind.shape[0] == 0:
        #     print('nothing found\n')
        pkt_starts = []
        for i in range(len(Upchirp_ind)):
            pkt_starts.append(Upchirp_ind[i][0])
        self.demod_sym = self.lora_demod2(Data_freq_off, SF, BW, BW, self.num_preamble, self.num_sync, self.num_DC,
                                         self.num_data_sym, pkt_starts)
        return [0, 0]


    def pkt_detection(self, Rx_Buffer, SF, BW, FS, num_preamble):
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        # num_preamble -= 1  # need to find n-1 total chirps (later filtered by sync word)

        # DC_upsamp = DC_gen(SF, BW, FS)
        DC_upsamp = np.conj(sym_to_data_ang([1], N, upsampling_factor))

        # Preamble Detection
        # temp_wind_fft = np.array([])
        ind_buff = np.array([])
        count = 0
        Pream_ind = np.array([], int)
        lim = int(np.floor(len(Rx_Buffer)/(upsampling_factor*N)))
        temp_wind_fft_idx = np.concatenate(
            [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])
        for i in range(1,lim+1):
            temp_wind_fft = abs(
                np.fft.fft(Rx_Buffer[((i-1) * upsampling_factor * N):
                                     ((i) * upsampling_factor * N) ] * DC_upsamp , axis=0))
            temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
            # plt.plot(temp_wind_fft)
            # plt.show()
            b = np.argmax(temp_wind_fft)
            if len(ind_buff) >= num_preamble:
                # ind_buff = ind_buff[-(num_preamble - 2):]
                ind_buff = ind_buff[len(ind_buff) - (num_preamble-1):len(ind_buff)]
                ind_buff = np.append(ind_buff, b)
            else:
                ind_buff = np.append(ind_buff, b)

            # print(f"{ind_buff}\n")
            if ((sum(abs(np.diff(np.mod(ind_buff, N + 1)))) <= (num_preamble + 4) or
                 sum(abs(np.diff(np.mod(ind_buff, N    )))) <= (num_preamble + 4) or
                 sum(abs(np.diff(np.mod(ind_buff, N - 1)))) <= (num_preamble + 4)) and
                    ind_buff.size >= num_preamble):
                # if np.sum(np.abs(Rx_Buffer[(i * upsampling_factor * N) + offset:((i + 1) * upsampling_factor * N) + offset])) != 0:
                    count = count + 1
                    Pream_ind = np.append(Pream_ind, ((i-1) - (num_preamble - 1)) * (upsampling_factor * N) + 1)

        # if SF == 7:
        #     print('hwere!')
        # print(f'{Pream_ind}\n')

        # Synchronization
        Pream_ind.sort()
        # shifts = np.arange(-N / 2, N / 2, dtype=int) * upsampling_factor
        shifts = np.arange((-N/2) * upsampling_factor, (N/2) * upsampling_factor, dtype=int)
        new_pream = []
        for i in range(len(Pream_ind)):
            ind_arr = np.array([])
            amp_arr = np.array([])
            for j in shifts:
                if Pream_ind[i] + j < 1:
                    ind_arr = np.append(ind_arr, -1)
                    amp_arr = np.append(amp_arr, -1)
                    continue

                temp_wind_fft = abs(
                    np.fft.fft(Rx_Buffer[(Pream_ind[i] + j - 1): (Pream_ind[i] + j + (upsampling_factor * N) - 1)] * DC_upsamp,
                               upsampling_factor * N, axis=0))
                temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
                b = temp_wind_fft.argmax()
                a = max(temp_wind_fft)
                amp_arr = np.append(amp_arr, a)
                ind_arr = np.append(ind_arr, b)

            temp_ind = (ind_arr == 0).nonzero()
            temp_shift = np.array([])
            temp_amp = np.array([])
            if len(temp_ind[0]) != 0:
                for k in temp_ind[0]:
                    temp_shift = np.append(temp_shift, shifts[k])
                    temp_amp = np.append(temp_amp, amp_arr[k])
                c = temp_amp.argmax()
                Pream_ind[i] = Pream_ind[i] + temp_shift[c]

############################################################################################################################
        temp = np.array([], int)
        for i in range(len(Pream_ind)):
            Pre_fft1 = abs(np.fft.fft(Rx_Buffer[Pream_ind[i]-1:Pream_ind[i]-1+(upsampling_factor*N)] * DC_upsamp, axis=0))
            Pre_fft1 = Pre_fft1[temp_wind_fft_idx]

            Pre_fft2 = abs(
                np.fft.fft(Rx_Buffer[Pream_ind[i] + (upsampling_factor*N)-1:Pream_ind[i] - 1 + (2*upsampling_factor * N)] * DC_upsamp, axis=0))
            Pre_fft2 = Pre_fft2[temp_wind_fft_idx]

            c1 = np.argmax(Pre_fft1)
            c2 = np.argmax(Pre_fft2)
            if (c1<=2 or c1 >=N-3) and (c2<=2 or c2>=N-3):
                temp = np.append(temp, Pream_ind[i])
        Pream_ind = temp

############################################################################################################################
        # SYNC WORD DETECTION
        count = 0
        Pream_ind = list(set(Pream_ind))
        Pream_ind.sort()
        Preamble_ind = np.array([], int)
        for i in range(len(Pream_ind)):
            if ((Pream_ind[i] + (9*upsampling_factor * N) - 1 > Rx_Buffer.size) or (
                    Pream_ind[i] + (10*upsampling_factor * N)-1 > Rx_Buffer.size)):
                continue

            sync_wind1 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + (8 * upsampling_factor * N)-1): (
                    Pream_ind[i] + (9 * upsampling_factor * N)-1)] * DC_upsamp, axis=0))
            sync_wind2 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + (9 * upsampling_factor * N)-1): (
                    Pream_ind[i] + (10 * upsampling_factor * N)-1)] * DC_upsamp, axis=0))
            sync_wind1 = sync_wind1[temp_wind_fft_idx]
            sync_wind2 = sync_wind2[temp_wind_fft_idx]

            s1 = sync_wind1.argmax()
            s2 = sync_wind2.argmax()
            if s1 >= 7 and s1 <= 9 and s2 >= 15 and s2 <= 17:
                count = count + 1
                Preamble_ind = np.append(Preamble_ind, Pream_ind[i])

        return Preamble_ind

    # def pkt_detection(self, Rx_Buffer, SF, BW, FS, num_preamble):
    #     upsampling_factor = int(FS / BW)
    #     N = int(2 ** SF)
    #     num_preamble -= 1  # need to find n-1 total chirps (later filtered by sync word)
    #
    #     DC_upsamp = DC_gen(SF, BW, FS)
    #
    #     # Preamble Detection
    #     ind_buff = np.array([])
    #     count = 0
    #     Pream_ind = np.array([], int)
    #
    #     loop = 0
    #     for off in range(3):
    #         offset = off * upsampling_factor * N // 3
    #         loop = Rx_Buffer.size // (upsampling_factor * N) - 1
    #         for i in range(loop):
    #             temp_wind_fft = abs(
    #                 np.fft.fft(Rx_Buffer[(i * upsampling_factor * N) + offset:
    #                                      ((i + 1) * upsampling_factor * N) + offset] * DC_upsamp, axis=0))
    #             temp_wind_fft_idx = np.concatenate(
    #                 [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])
    #             temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
    #             b = np.argmax(temp_wind_fft)
    #             if len(ind_buff) >= num_preamble:
    #                 ind_buff = ind_buff[-(num_preamble - 1):]
    #                 ind_buff = np.append(ind_buff, b)
    #             else:
    #                 ind_buff = np.append(ind_buff, b)
    #
    #             if ((sum(abs(np.diff(np.mod(ind_buff, N + 1)))) <= (num_preamble + 4) or
    #                  sum(abs(np.diff(np.mod(ind_buff, N)))) <= (num_preamble + 4) or
    #                  sum(abs(np.diff(np.mod(ind_buff, N - 1)))) <= (num_preamble + 4)) and
    #                     ind_buff.size >= num_preamble - 1):
    #                 if np.sum(np.abs(Rx_Buffer[(i * upsampling_factor * N)
    #                                            + offset:((i + 1) * upsampling_factor * N) + offset])) != 0:
    #                     count = count + 1
    #                     Pream_ind = np.append(Pream_ind, (i - (num_preamble - 1)) * (upsampling_factor * N) + offset)
    #
    #     # print('Found ', count, ' Preambles')
    #     if count >= (loop * 0.70):
    #         Preamble_ind = np.array([], int)
    #         return Preamble_ind
    #
    #     # Synchronization
    #     Pream_ind.sort()
    #     shifts = np.arange(-N / 2, N / 2, dtype=int) * upsampling_factor
    #     new_pream = []
    #     for i in range(len(Pream_ind)):
    #         ind_arr = np.array([])
    #
    #         for j in shifts:
    #             if Pream_ind[i] + j < 0:
    #                 ind_arr = np.append(ind_arr, -1)
    #                 continue
    #
    #             temp_wind_fft = abs(
    #                 np.fft.fft(Rx_Buffer[(Pream_ind[i] + j): (Pream_ind[i] + j + upsampling_factor * N)] * DC_upsamp,
    #                            upsampling_factor * N, axis=0))
    #             temp_wind_fft = temp_wind_fft[np.concatenate(
    #                 [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #             b = temp_wind_fft.argmax()
    #             ind_arr = np.append(ind_arr, b)
    #
    #         nz_arr = (ind_arr == 0).nonzero()
    #         if len(nz_arr) != 0:
    #             new_pream = new_pream + (shifts[nz_arr] + Pream_ind[i]).tolist()
    #
    #     # sub-sample sync
    #     Pream_ind = new_pream
    #     shifts = np.arange(-upsampling_factor, upsampling_factor + 1, dtype=int)
    #     for i in range(len(Pream_ind)):
    #         amp_arr = []
    #
    #         for j in shifts:
    #             if Pream_ind[i] + j < 0:
    #                 amp_arr.append([-1, j])
    #                 continue
    #
    #             temp_wind_fft = abs(
    #                 np.fft.fft(Rx_Buffer[(Pream_ind[i] + j): (Pream_ind[i] + j + upsampling_factor * N)] * DC_upsamp,
    #                            upsampling_factor * N, axis=0))
    #             temp_wind_fft = temp_wind_fft[np.concatenate(
    #                 [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #
    #             b = temp_wind_fft.argmax()
    #             if b == 0:
    #                 a = temp_wind_fft[0]
    #                 amp_arr.append([a, j])
    #
    #         if len(amp_arr) != 0:
    #             Pream_ind[i] = Pream_ind[i] + max(amp_arr)[1]
    #
    #     # SYNC WORD DETECTION
    #     count = 0
    #     Pream_ind = list(set(Pream_ind))
    #     Pream_ind.sort()
    #     Preamble_ind = np.array([], int)
    #     for i in range(len(Pream_ind)):
    #         if ((Pream_ind[i] + 9 * (upsampling_factor * N) > Rx_Buffer.size) or (
    #                 Pream_ind[i] + 10 * (upsampling_factor * N) > Rx_Buffer.size)):
    #             continue
    #
    #         sync_wind1 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + 8 * upsampling_factor * N): (
    #                 Pream_ind[i] + 9 * upsampling_factor * N)] * DC_upsamp, axis=0))
    #         sync_wind2 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + 9 * upsampling_factor * N): (
    #                 Pream_ind[i] + 10 * upsampling_factor * N)] * DC_upsamp, axis=0))
    #         sync_wind1 = sync_wind1[np.concatenate(
    #             [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #         sync_wind2 = sync_wind2[np.concatenate(
    #             [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #
    #         s1 = sync_wind1.argmax()
    #         s2 = sync_wind2.argmax()
    #         if s1 >= 7 and s1 <= 9 and s2 >= 15 and s2 <= 17:
    #             count = count + 1
    #             Preamble_ind = np.append(Preamble_ind, Pream_ind[i])
    #
    #     return Preamble_ind

    def lora_demod(self, Rx_Buffer, SF, BW, FS, num_preamble, num_sync, num_DC, num_data_sym, Preamble_ind):
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        fact = 2
        demod_sym = np.array([], int, ndmin=2)

        # DC_upsamp = DC_gen(int(math.log2(N)), BW, FS)
        DC_upsamp = np.conj(sym_to_data_ang([1], N, upsampling_factor))
        Data_frame_st = Preamble_ind + int((num_preamble + num_sync + num_DC) * N * upsampling_factor)

        for j in range(Preamble_ind.shape[0]):
            demod = np.empty((1, num_data_sym), int)
            for i in range(num_data_sym):
                if Data_frame_st[j] + (i + 1) * upsampling_factor * N > Rx_Buffer.size:
                    demod[:, i] = -1
                    continue

                temp_fft = abs(np.fft.fft(Rx_Buffer[(Data_frame_st[j] + (i * upsampling_factor * N)-1): (
                        Data_frame_st[j] + ((i + 1) * upsampling_factor * N))-1] * DC_upsamp, n=fact*upsampling_factor*N , axis=0))
                # temp_fft = temp_fft[np.concatenate(
                #     [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
                temp_fft = temp_fft[np.concatenate(
                    [np.arange(0,fact * (N // 2)), np.arange((fact*(N // 2)) + (upsampling_factor - 1) * fact * N, fact * upsampling_factor * N)])]

                b = temp_fft.argmax()
                demod[:, i] = round(b/fact)

            if j == 0:
                demod_sym = demod
            else:
                demod_sym = np.vstack((demod_sym, demod))

        demod_sym = demod_sym % N
        # print(f'{demod_sym}\n')
        return demod_sym

    def lora_demod2(self, Rx_Buffer, SF, BW, FS, num_preamble, num_sync, num_DC, num_data_sym, Preamble_ind):
        Rx_Buffer = Rx_Buffer[0]
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        fact = 1
        demod_sym = np.array([], int, ndmin=2)

        # DC_upsamp = DC_gen(int(math.log2(N)), BW, FS)
        DC_upsamp = np.conj(sym_to_data_ang([1], N, 0))
        DC_upsamp = np.reshape(DC_upsamp, (1, N))
        Data_frame_st = Preamble_ind[0] + int((num_preamble + num_sync + num_DC) * N * upsampling_factor)

        for j in range(len(Preamble_ind)):
            demod = np.empty((1, num_data_sym), int)
            for i in range(num_data_sym):
                if Data_frame_st + (i + 1) * upsampling_factor * N > Rx_Buffer.size:
                    demod[:, i] = -1
                    continue

                temp_fft = abs(np.fft.fft(Rx_Buffer[(Data_frame_st + (i * upsampling_factor * N)-1): (
                        Data_frame_st + ((i + 1) * upsampling_factor * N))-1] * DC_upsamp, n=fact*upsampling_factor*N , axis=0))
                # temp_fft = temp_fft[np.concatenate(
                #     [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
                temp_fft = temp_fft[np.concatenate(
                    [np.arange(0,fact * (N // 2)), np.arange((fact*(N // 2)) + (upsampling_factor - 1) * fact * N, fact * upsampling_factor * N)])]

                b = temp_fft.argmax()
                demod[:, i] = round(b/fact)

            if j == 0:
                demod_sym = demod
            else:
                demod_sym = np.vstack((demod_sym, demod))

        demod_sym = demod_sym % N
        return demod_sym

    def remove_sim(self, vals, dist):
        if len(vals) <= 1:
            return vals
        ret = []
        curr_index = vals[0][0]
        ret.append(vals[0])
        for i, _ in enumerate(vals):
            if i == 0:
                continue
            else:
                if vals[i][0] - curr_index > dist:
                    ret.append(vals[i])
                    curr_index = vals[i][0]
        return ret

    def decodeRLO(self, SF, PRINT):
        decoded_packets = 0
        final_data = []
        message = []
        if len(self.demod_sym) > 0 and len(self.demod_sym[0]) > 0:
            for i, syms in enumerate(self.demod_sym):
                # print(f'syms = {i}, {syms}')
                message = lora_decoder(np.mod(syms, (2**SF)), SF, self.check_crc)
                if message is not None:
                    decoded_packets += 1
                    # final_data.append((self.pkt_starts[i], self.demod_sym[i], message))
                    final_data.append((self.pkt_starts[0], self.demod_sym[0], message))

            # print(f'Before = {final_data}')
            # final_data = self.remove_sim(final_data, 10 * (2 ** SF))
            # print(f'After = {final_data}')
        self.demod_sym = []
        self.pkt_starts = []
        if PRINT:
            for d in final_data:
                print(d[2].tolist())
                #print(''.join([chr(int(c)) for c in d[2][7:]]))

        return message    # def correlate(self, Rx, SF: int, BW: int, FS: int):
    #     upsampling_factor = int(FS / BW)
    #     N = int(2 ** SF)
    #     # demod_sym = np.array([], int, ndmin=2)
    #
    #     DC_upsamp = DC_gen(int(math.log2(N)), BW, FS)
    #
    #     np.correlate(Rx, "full")
    #     self.demodulate(Rx, SF, BW, FS)
    #     return self.decode(SF, PRINT)

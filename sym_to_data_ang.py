import numpy as np
import math

def sym_to_data_ang(symbol,N,upsamp):

    data = np.zeros((), np.complex64)
    accumulator = 0
    pi = math.pi
    temp = np.zeros((), complex)

    for j in symbol:
    # j = 1
        phase = -pi + (j-1)*(2 * pi/N)
        # print(len(temp))
        for i in range(N):

            accumulator = accumulator + phase
            polar_radius = 1

            x = polar_radius * math.cos(accumulator)
            y = polar_radius * math.sin(accumulator)
            # temp[i] = complex(x, y)
            a = complex(x, y)
            # print(a)
            temp = np.append(temp, a)
            # print(f'{temp}\n')
            phase = phase + (2 * pi/N)

        temp = np.delete(temp,0)
        # print(temp[0])
        # print(temp[1])
        data = temp
    # print(len(data))
    if upsamp != 0:
        data_fft = np.fft.fft(data)
        temp_arr1 = np.append(data_fft[0:int(len(data_fft)/2)], np.zeros((1,(upsamp-1)*len(data_fft)),dtype=np.complex64))
        # print(len(temp_arr1))
        temp_arr2 = np.append(temp_arr1, data_fft[int(len(data_fft)/2) : len(data_fft)])
        # print(len(temp_arr2))
        data_upsamp = np.fft.ifft(temp_arr2)
        data = data_upsamp
    
    return data



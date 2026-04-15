import numpy as np
import math


def stft_v1(Rx_Buffer,N,DC,upsamp,dis):
    # This function produces a spectrogram of LoRa signal using Dechirping
    # operation to get the best frequency Resolution
    tm_ax = [1, int(N/2), N, int(3*N/2), 2*N, int(5*N/2), 3*N]
    Spec = np.zeros((N, len(tm_ax)))
    buff = np.concatenate([Rx_Buffer, np.zeros(N-1)])

    if(upsamp):
        for i in range(Rx_Buffer.shape[1]):
            Spec[:,i] = np.roll(np.abs(np.fft.fft(buff[i:i+N] * DC.conj())) / math.sqrt(N),-round( (i)/8 ))
    else:
        # for i in range(len(Rx_Buffer)):
        for i in range(len(tm_ax)):
            # Spec[:,i] = np.roll(np.abs(np.fft.fft(buff[i:i+N] * DC)) / math.sqrt(N), -(i))
            Spec[:,i] = np.roll(np.abs(np.fft.fft(buff[tm_ax[i]-1:tm_ax[i]+N-1] * DC)) / math.sqrt(N), -(i))
    return Spec

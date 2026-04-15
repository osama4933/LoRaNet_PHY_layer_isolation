
#############################################################
LORA_SF = [7, 8, 9, 10, 11, 12]  # 12;            # LoRa spreading factor
LORA_BW = 125056#125e3        # LoRa bandwidth
LOGGER_LOC = 'DATA_LOG.txt'


# Receiving device parameters
NUM_PREAMBLE = 8  # down sampling factor
NUM_SYNC = 2
NUM_DC = 2.25
MAX_DATA_SYM = 200
SYNC1 = 8
SYNC2 = 16
HAS_CRC = False#True

################# LoRa and SDR info #########################
CENTER_FREQ = 905e6           		# SDR center frequency
RAW_FS = 500224#4096#500e3					# SDR's raw sampling freq
LORA_CHANNELS = [3, 4, 5, 6]#[1]  # channels to process
CHANNELIZE = False				# weather to channelize locally or in gnuradio
FREQ_OFF = 200e3                		# channel size
FC = 70e3                       		# channel cutoff freq

UPSAMPLE_FACTOR = 4             		# factor to downsample to
FS = LORA_BW * UPSAMPLE_FACTOR    		# sampling rate after conversion
BW = LORA_BW                      		# LoRa signal bandwidth
OVERLAP = 10 * UPSAMPLE_FACTOR#int(10 * RAW_FS / BW)
THROTTLE_RATE = 1
QUEUE_SIZE = 10 * min(len(LORA_CHANNELS), 4)

SEND_SIZE = 32                  		# can either be 32 or 16 bit
############################################################

# processing parameters
NUM_CORES = 3

################ Function pointer to IQ stream #############
import IQ_source
IQ_SOURCE = IQ_source.UDP_load2
#IQ_SOURCE = IQ_source.file_load
############################################################

# Xin Yao
# The parameters in this file are basically for the C++ API, some of them are Python parameters
import argparse


def create_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description='USRP Transmitter/Receiver System',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # ===== REQUIRED ARGUMENTS =====
    parser.add_argument('-role',
                        type=str,
                        default='src1',
                        choices=['src1', 'dst1', 'rly1'],  # Name should be changed
                        help='Operation mode')

    """------------USRP Hardware setting (same for transmitter and receiver)------------"""

    parser.add_argument('-ref',
                        type=str,
                        default="internal",
                        help='USRP clock reference, only external when the clock source is connected')

    parser.add_argument('-otw',
                        type=str,
                        default="sc16",
                        help='USRP wire datatype, normally sc16, check C++ API for more options')

    parser.add_argument('-settling_time',
                        type=float,
                        default=0.2,
                        help='USRP hardware settling time, wait for a while for setup')

    parser.add_argument('-uhd_timeout',
                        type=float,
                        default=1000,
                        help='USRP UHD timeout, how long UHD wait for the message pass')

    parser.add_argument('-data_type',
                        type=str,
                        default='float',
                        help='The processing data type (int, float, double), normally float')

    parser.add_argument('-num_taps',
                        type=int,
                        default=151,
                        help='Number of filter taps, should be same for pulse shaping and match filter')

    parser.add_argument('-mod_scheme',
                        type=str,
                        default='DBPSK',
                        help='Modulation scheme (DBPSK, BPSK, DQPSK, QPSK, 16QAM ...)')

    parser.add_argument('-add_preamble',
                        type=bool,
                        default=True,
                        help='Add the preamble for message, use for time / freq / phase synchronization')

    parser.add_argument('-preamble_length',
                        type=int,
                        default=5,
                        help='the power number for preamble sequence, 2^m -> m')

    parser.add_argument('-preamble_type',
                        type=str,
                        default='m-sequence',
                        help='The preamble sequence type, currently m-sequence and Zadoff')

    parser.add_argument('-filter_type',
                        type=str,
                        default='rrc',
                        help='pulse shaping and match filter type, should be consist')

    parser.add_argument('-symbol_rate',
                        type=float,
                        default=0.8e6,
                        help='original symbol message rate before the pulse shaping filter')

    parser.add_argument('-roll_off',
                        type=float,
                        default=0.25,
                        help='roll_off factor, control the shape of pulse')

    parser.add_argument('-num_threads',
                        type=int,
                        default=1,
                        help='Number of threads to do the FFT for Polyphase and Multi-rate filter')

    """------------------Transmitter USRP Setting--------------------"""

    parser.add_argument('-tx_freq',
                        type=float,
                        default=2.412e9,
                        help='Transmit Center frequency in Hz')

    parser.add_argument('--tx_rate',
                        type=float,
                        default=1e6,
                        help='Transmit Sample rate in samples/sec')

    parser.add_argument('-tx_gain',
                        type=float,
                        default=20.0,
                        help='Transmit TX/RX gain in dB')

    parser.add_argument('-tx_bw',
                        type=float,
                        default=500e3,
                        help='Transmit Bandwidth in Hz')

    parser.add_argument('-tx_args',
                        type=str,
                        default="serial=30CD424",
                        help='Transmit USRP args, normally need serial number like 30CD424')

    parser.add_argument('-tx_ant',
                        type=str,
                        default="TX/RX",
                        choices=['TX/RX', 'RX2', 'MIMO'],
                        help='Transmit antenna, normally TX/RX and RX2')

    parser.add_argument('-tx_subdev',
                        type=str,
                        default="A:A",
                        help='Transmit sub-device (the port) of USRP, A:0 for N210, A:A for B210')

    parser.add_argument('-tx_channel',
                        type=int,
                        default=0,
                        help='Transmit channel, same functionality as tx_subdev')

    parser.add_argument('-num_bits',
                        type=int,
                        default=1000,
                        help='Number of bits of original message')

    parser.add_argument('-message_interval',
                        type=int,
                        default=1000,
                        help='Message interval (ms), the time period between two consecutive packets')

    parser.add_argument('-continues_',
                        type=bool,
                        default=False,
                        help='Transmission mode, there is no interval between packets if True')

    parser.add_argument('-repeat_times_',
                        type=int,
                        default=3,
                        help='How many times that one message will be sent')

    parser.add_argument('-Up',
                        type=int,
                        default=5,
                        help='Up-sampling factor for pulse shaping filter')

    parser.add_argument('-Dp',
                        type=int,
                        default=4,
                        help='Down-sampling factor for pulse shaping filter')

    """------------------Receiver USRP Setting--------------------"""

    parser.add_argument('-samps_per_buff',
                        type=int,
                        default=10000,
                        help='Receive buffer size to hold the raw samples')

    parser.add_argument('-num_recv_request',
                        type=int,
                        default=0,
                        help='Number of samples required for receiving, 0 if continues transmission')

    parser.add_argument('-rx_channel',
                        type=int,
                        default=0,
                        help='Receive channel, same functionality as tx_subdev')

    parser.add_argument('-rx_freq',
                        type=float,
                        default=2.412e9,
                        help='Receive Center frequency in Hz')

    parser.add_argument('--rx_rate',
                        type=float,
                        default=1e6,
                        help='Receive Sample rate in samples/sec')

    parser.add_argument('-rx_gain',
                        type=float,
                        default=20.0,
                        help='Receive TX/RX gain in dB')

    parser.add_argument('-rx_bw',
                        type=float,
                        default=500e3,
                        help='Receive Bandwidth in Hz')

    parser.add_argument('-rx_args',
                        type=str,
                        default="",
                        help='Receive USRP args, normally need serial number like 30CD424')

    parser.add_argument('-rx_ant',
                        type=str,
                        default="TX/RX",
                        choices=['TX/RX', 'RX2', 'MIMO'],
                        help='Receive antenna, normally TX/RX and RX2')

    parser.add_argument('-rx_subdev',
                        type=str,
                        default="A:A",
                        help='Receive sub-device (the port) of USRP, A:0 for B210, A:A for N210')

    parser.add_argument('-energy_packet_size',
                        type=int,
                        default=1340,
                        help='IIR Energy detector packet size, how many samples need to save')

    parser.add_argument('-IIR_window_size',
                        type=int,
                        default=1,
                        help='IIR window size, how many samples average over')

    parser.add_argument('-alpha',
                        type=float,
                        default=0.96,
                        help='IIR filter alpha, control how fast IIR acts, larger -> faster')

    parser.add_argument('-energy_threshold',
                        type=float,
                        default=0.2,
                        help='Fix Energy Detector threshold if not use the adaptive threshold')

    parser.add_argument('-IIR_threshold_multiplier',
                        type=float,
                        default=8.0,
                        help='IIR Detector How many times detected samples over adaptive threshold')

    parser.add_argument('-IIR_threshold_adaptive',
                        type=bool,
                        default=True,
                        help='Use Adaptive Energy Detector threshold or not to compute noise floor')

    parser.add_argument('-AGC_type',
                        type=str,
                        default='Feed',
                        help='AGC type, Feed: Feedforward / Close: CloseLoop')

    parser.add_argument('-Um',
                        type=int,
                        default=4,
                        help='Up-sampling factor for match filter')

    parser.add_argument('-Dm',
                        type=int,
                        default=1,
                        help='Down-sampling factor for match filter')

    parser.add_argument('-sps_sync',
                        type=int,
                        default=5,
                        help='samples per symbol for symbol synchronization')

    parser.add_argument('-recv_msg_len',
                        type=int,
                        default=1025,
                        help='Expected demodulated message length, +1 if using differential coding')

    parser.add_argument('-sync_threshold',
                        type=float,
                        default=4.0,
                        help='Symbol synchronization threshold, boundary for max correlation value')

    """---------------------- Additional Options ---------------------"""

    parser.add_argument('-message_type',
                        type=str,
                        default='bits',
                        help='the data type which pushes to the C++ API')

    return parser


def get_args():
    """Parse and return arguments"""
    parser = create_parser()
    return parser.parse_args()

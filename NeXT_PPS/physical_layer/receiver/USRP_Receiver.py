import receiver
import time
import signal
import sys
from typing import Optional, List, Callable

class USRPReceiver:
    
    def __init__(self,
                 # USRP Parameters
                 rx_channel: int = 0,
                 samps_per_buff: int = 10000,
                 num_recv_request: int = 0,
                 rx_freq: float = 2.412e9,
                 rx_rate: float = 1e6,
                 rx_gain: float = 20.0,
                 rx_bw: float = 500e3,
                 settling_time: float = 0.2,
                 uhd_timeout: float = 1000.0,
                 rx_args: str = "",
                 rx_ant: str = "RX2",
                 rx_subdev: str = "A:0",
                 ref: str = "internal",
                 otw: str = "sc16",
                 data_type: str = "float",
                 
                 # Energy Detection and AGC parameters
                 energy_packet_size: int = 1340,
                 IIR_window_size: int = 1,
                 alpha: float = 0.96,
                 energy_threshold: float = 0.2,
                 IIR_threshold_multiplier: float = 8.0,
                 IIR_threshold_adaptive: bool = True,
                 AGC_type: str = "Feed",

                 # Filter Parameters
                 num_taps: int = 151,
                 U: int = 4,
                 D: int = 1,
                 num_threads: int = 1,
                 symbol_rate: float = 0.8e6,
                 roll_off: float = 0.25,
                 filter_type: str = "rrc",
                 
                 # Synchronization Parameters
                 recv_msg_len: int = 1017,
                 sps_sync: int = 5,
                 sync_threshold: float = 16.0,

                 # Demodulation Parameters
                 preamble_length: int = 5,
                 add_preamble: bool = True,
                 preamble_type: str = "m-sequence",
                 demod_scheme: str = "DBPSK"):

        """Initialize receiver with parameters."""
        
        print("[Python RX API] Initializing receiver...")
        
        self._rx = receiver.Receiver()
        
        # Configure USRP
        self._rx.set_rx_channel(rx_channel)
        self._rx.set_samps_per_buff(samps_per_buff)
        self._rx.set_num_recv_request(num_recv_request)
        self._rx.set_settling_time(settling_time)
        self._rx.set_uhd_timeout(uhd_timeout)
        self._rx.set_rx_freq(rx_freq)
        self._rx.set_rx_rate(rx_rate)
        self._rx.set_rx_gain(rx_gain)
        self._rx.set_rx_bw(rx_bw)
        if rx_args:
            self._rx.set_rx_args(rx_args)
        self._rx.set_rx_antenna(rx_ant)
        self._rx.set_rx_subdev(rx_subdev)
        self._rx.set_ref(ref)
        self._rx.set_otw(otw)
        self._rx.set_data_type(data_type)
        
        # Configure Energy Detector
        self._rx.set_energy_detector(energy_packet_size, IIR_window_size, alpha, energy_threshold,
                                     IIR_threshold_multiplier, IIR_threshold_adaptive, AGC_type)
        
        # Configure Match Filter
        self._rx.set_filter(num_taps, U, D, num_threads, symbol_rate, roll_off, filter_type)

        # Configure Time Synchronization and Demodulation
        self._rx.set_sync_and_demod(recv_msg_len, sps_sync, sync_threshold, preamble_length,
                                add_preamble, preamble_type, demod_scheme)

        self._is_running = False
        self._signal_handler_installed = False
        
        print(f"\n[Python RX API] Configuration:")
        print(f"  USRP:")
        print(f"    Frequency: {rx_freq/1e6:.3f} MHz")
        print(f"    Sample Rate: {rx_rate/1e6:.3f} MSPS")
        print(f"    Gain: {rx_gain} dB")
        print(f"  Demodulation:")
        print(f"    Scheme: {demod_scheme}")
        print(f"    Preamble: {add_preamble} (length={preamble_length})")
        print(f"  Filter:")
        print(f"    Type: {filter_type}")
        print(f"    Symbol Rate: {symbol_rate/1e6:.3f} MHz\n")
    
    def _install_signal_handler(self):
        """Install Python signal handler for graceful Ctrl+C"""
        if self._signal_handler_installed:
            return
        
        def signal_handler(sig, frame):
            print("\n[Python RX API] Ctrl+C detected - stopping receiver...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        self._signal_handler_installed = True
    
    def start(self, install_signal_handler: bool = True):
        """Start the receiver pipeline."""
        if self._is_running:
            print("[Python RX API] Already running")
            return False
        
        if install_signal_handler:
            self._install_signal_handler()
        
        print("[Python RX API] Starting receiver...")
        success = self._rx.start()
        
        if success:
            self._is_running = True
            time.sleep(0.5)
            print("[Python RX API] Receiver started ✓")
            print("[Python RX API] Press Ctrl+C to stop")
        else:
            print("[Python RX API] Failed to start receiver ✗")
        
        return success
    
    def stop(self):
        """Stop the receiver pipeline."""
        if not self._is_running:
            return
        
        print("[Python RX API] Stopping receiver...")
        self._rx.stop()
        self._is_running = False
        print("[Python RX API] Receiver stopped ✓")
    
    def receive_message(self) -> Optional[str]:
        """
        Receive a demodulated message.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Decoded message string, or None if timeout
        """
        if not self._is_running:
            raise RuntimeError("Receiver not running. Call start() first.")
        
        return self._rx.receive_message()
    
    def receive_bits(self) -> Optional[List[int]]:
        """
        Receive demodulated bits.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            List of bits, or None if timeout
        """
        if not self._is_running:
            raise RuntimeError("Receiver not running. Call start() first.")
        
        return self._rx.receive_bits()
    
    def get_status(self) -> dict:
        """Get receiver status."""
        return self._rx.get_status()
    
    def get_config(self) -> dict:
        """Get receiver configuration."""
        return self._rx.get_config()
    
    def clear_queues(self):
        """Clear all queues."""
        self._rx.clear_queues()
    
    def __enter__(self):
        """Context manager entry."""
        if not self._is_running:
            self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
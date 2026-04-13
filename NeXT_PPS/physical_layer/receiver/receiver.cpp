// UHD related library
# include <uhd/utils/safe_main.hpp>
# include <uhd/utils/static.hpp>
# include <uhd/utils/thread.hpp>
# include <uhd/usrp/multi_usrp.hpp>
# include <uhd/exception.hpp>

// Boost library
# include <boost/program_options.hpp>  // for arguments input
# include <boost/format.hpp>

// Basic library
# include <iostream>
# include <csignal>  // deal with signal
# include <cmath>
# include <functional>  // funtion / bind / std::ref / std::greater/less
# include <thread>
# include <vector>
# include <mutex>  // for FIFO queue and multi-thread processing
# include <fftw3.h>

// Unused but useful library
// # include <fstream>  // File reading / writing

# include "filters.hpp"
# include "messages.hpp"
# include "FIFO.hpp"
// # include "taps.hpp"
# include "modulator.hpp"
# include "transceiver.hpp"
# include "synchronization.hpp"

namespace po = boost::program_options;

static bool stop_signal_called = false;
void sig_int_handler(int){
    stop_signal_called = true;
}

static std::shared_ptr<std::vector<std::complex<float>>> preamble_ptr;

int UHD_SAFE_MAIN(int argc, char* argv[]) {

    // Message parameters
    int num_bits, interval, preamble_length;
    bool continues, add_preamble;
    std::string preamble;

    // Modulation parameters
    // samples per symbol (sps) = U / D

    // Filter parameters
    int U, D, num_taps, num_threads, sps;
    double rx_rate, rx_freq, symbol_rate, roll_off;
    std::string filter_type;

    // Energy Detection parameters
    float alpha, energy_threshold, IIR_threshold_multiplier;
    size_t energy_packet_size, IIR_window_size;
    bool IIR_threshold_adaptive;

    // Synchronization parameters
    int sps_sync, message_length;
    float sync_threshold;

    // Receiver parameters
    std::string rx_args, rx_ant, type, rx_subdev, scheme, data_type, ref, otw, AGC_type;
    double rx_gain, rx_bw, settling_time, uhd_timeout;
    int rx_channel, samps_per_buff, num_recv_request;

    po::options_description desc("Allowed Options");

    desc.add_options()
        ("help", "help message")
        
        // Message settings
        ("num_bits", po::value<int>(&num_bits)->default_value(1000), "number of bits of original message")
        ("interval", po::value<int>(&interval)->default_value(1000), "interval time in ms between packets, set to 0 if continues mode")
        ("data_type", po::value<std::string>(&data_type)->default_value("float"), "data tyoe for transmission, only consider float now")
        ("preamble", po::value<std::string>(&preamble)->default_value("None"), "m-sequence or Zadoff-chu sequence")
        ("m", po::value<int>(&preamble_length)->default_value(5), "The preamble length (m-sequence) and root (Zadoff sequence)")
        ("add_preamble", po::value<bool>(&add_preamble)->default_value(true), "Add preamble before the header + payload or not")

        // Energy Detection Settings
        ("alpha", po::value<float>(&alpha)->default_value(0.02), "The alpha value for IIR filter energy detector (large -> fast response -> not smooth)")
        ("energy_threshold", po::value<float>(&energy_threshold)->default_value(0.2), "the fixed energy detection threshold")
        ("energy_packet_size", po::value<size_t>(&energy_packet_size)->default_value(1350), "number of samples collected after energy detected")
        ("IIR_window_size", po::value<size_t>(&IIR_window_size)->default_value(20), "IIR window size for window energy computation -> smoothness")
        ("IIR_threshold_adaptive", po::value<bool>(&IIR_threshold_adaptive)->default_value(true), "Apply adaptive threshold or not")
        ("IIR_threshold_multiplier", po::value<float>(&IIR_threshold_multiplier)->default_value(5.0), "how many times nosie level for threshold")

        // Synchronization Settings
        ("sps_sync", po::value<int>(&sps_sync)->default_value(5), "The samples per symbol using in Synchronization U_t/D_t * U_r (5/4 * 4)")
        ("sync_threshold", po::value<float>(&sync_threshold)->default_value(1.0), "The synchronization threshold")
        ("recv_msg_len", po::value<int>(&message_length)->default_value(1017), "header + message length, 1000+16, +1 if use differential encoding")

        // Filter settings
        ("U", po::value<int>(&U)->default_value(4), "Upsampling factor")
        ("D", po::value<int>(&D)->default_value(1), "Downsampling factor")
        ("filter_type", po::value<std::string>(&filter_type)->default_value("rrc"), "Filter taps type: RRC / RC / Low Pass")
        ("symbol_rate", po::value<double>(&symbol_rate)->default_value(double(0.8e6)), "symbol rate")
        ("num_taps", po::value<int>(&num_taps)->default_value(151), "Number of taps, normally 6-15 * sps")
        ("roll_off", po::value<double>(&roll_off)->default_value(0.25), "Roll-off factor of RRC / RC filter, no use in Low pass filter")
        ("num_threads", po::value<int>(&num_threads)->default_value(1), "Number of threads using for FFT processing")

        // Receiver settings
        ("rx-args", po::value<std::string>(&rx_args)->default_value(""), "uhd transmitter device address args")
        ("rx-rate", po::value<double>(&rx_rate)->default_value(double(1e6)), "transmit rate (sample rate)")
        ("rx-freq", po::value<double>(&rx_freq)->default_value(2.412e9), "transmite central frequency")
        ("rx-gain", po::value<double>(&rx_gain)->default_value(20.0), "transmit gain for USRP")
        ("rx-bw", po::value<double>(&rx_bw)->default_value(500e3), "transmit bandwidth")
        ("rx-ant", po::value<std::string>(&rx_ant)->default_value("RX2"), "transmit antenna TX/RX")
        ("rx-channel", po::value<int>(&rx_channel)->default_value(0), "transmit channel (0 or 1)")
        ("rx-subdev", po::value<std::string>(&rx_subdev)->default_value("A:0"), "transmit subdev specification")
        ("rx-int-n", "tune USRP TX with integer-N tuning")
        
        ("continues", po::value<bool>(&continues)->default_value(false), "transmit mode: continues or not")
        ("uhd_timeout", po::value<double>(&uhd_timeout)->default_value(1000.0), "UHD transmitter timeout in ms, upper bound for waiting time")
        ("ref", po::value<std::string>(&ref)->default_value("internal"), "clock reference (internal, external, mimo)")
        ("otw", po::value<std::string>(&otw)->default_value("sc16"), "specifty the over the wire sample mode")
        ("settling", po::value<double>(&settling_time)->default_value(0.2), "settling time for transmitter")
        ("samps_per_buff", po::value<int>(&samps_per_buff)->default_value(10000), "samples per buffer for receive thread")
        ("num_recv_request", po::value<int>(&num_recv_request)->default_value(0), "number of receive samples, 0 is the continues mode")

        ("AGC_type", po::value<std::string>(&AGC_type)->default_value("Feed"), "Auto Gain Control type (Feed / Closed) ")

        // Modulation settings
        ("scheme", po::value<std::string>(&scheme)->default_value("DBPSK"), "modulation scheme")
        ("sps", po::value<int>(&sps)->default_value(2), "samples per symbol, specify sps inside the modulation scheme, otherwise sps = U/D");
    
    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    if (vm.count("help")){
        std::cout << desc << std::endl;
        return EXIT_SUCCESS;
    }

    // Generate preamble message if needed
    MSequenceGenerator mseq(preamble_length);  // m=5 → 31 bits
    auto dbpsk_preamble = mseq.modulate(PreambleModType::DBPSK);
    // mseq.computeAutocorrelation(dbpsk_preamble);  // Verify the m-sequence has correct autocorrelation.
    save_block_to_txt(dbpsk_preamble, 0, "preamble_sequence_receiver");

    std::signal(SIGINT, sig_int_handler);

    // Create USRP device
    uhd::usrp::multi_usrp::sptr rx_usrp = uhd::usrp::multi_usrp::make(rx_args);

    std::cout << "-------------------------------------------Setting start------------------------------------------------" << std::endl;

    // Setup the USRP parameters
    // Always select subdevice first
    if (vm.count("rx-subdev")){
        rx_usrp->set_rx_subdev_spec(rx_subdev);
    }
    std::cout << "Using RX Device: " << rx_usrp->get_pp_string() << std::endl;

    // Set clock reference
    if (vm.count("ref")){
        rx_usrp->set_clock_source(ref);
    }
    
    rx_usrp->set_rx_rate(rx_rate);
    
    uhd::tune_request_t rx_tune_request(rx_freq);
    if (vm.count("rx-int-n")){
        rx_tune_request.args = uhd::device_addr_t("mode_n=integer");
    }

    rx_usrp->set_rx_freq(rx_tune_request);
    rx_usrp->set_rx_gain(rx_gain);
    rx_usrp->set_rx_antenna(rx_ant);
    rx_usrp->set_rx_bandwidth(rx_bw);
    rx_usrp->set_rx_dc_offset(true);

    // Check LO locked
    std::vector<std::string> rx_sensor_names = rx_usrp->get_rx_sensor_names(0);
    if (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "lo_locked") != rx_sensor_names.end()){
        uhd::sensor_value_t lo_locked = rx_usrp->get_rx_sensor("lo_locked", 0);
        std::cout << boost::format("Checking Rx: %s ...") % lo_locked.to_pp_string() << std::endl;
        UHD_ASSERT_THROW(lo_locked.to_bool());
    }

    // Allow for soem setup time
    std::this_thread::sleep_for(std::chrono::milliseconds(long(settling_time * 1000)));

    std::cout << "-------------------------------------------Main start----------------------------------------------" << std::endl;

    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> recv_fifo;
    std::vector<unsigned long> channel = {static_cast<unsigned long>(rx_channel)};

    // Receiver thread
    std::thread receive(receive_thread, rx_usrp, channel, rx_rate, settling_time,
                        std::ref(recv_fifo), num_recv_request, samps_per_buff,
                        std::ref(stop_signal_called));

    // Energy detection
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> detected_fifo;

    EnergyDetectorIIR Detector(alpha, energy_threshold, energy_packet_size, IIR_window_size, IIR_threshold_adaptive, IIR_threshold_multiplier);
    std::thread energy_detection(EnergyDetection_thread, 
                                 std::ref(recv_fifo), std::ref(detected_fifo),
                                 std::ref(Detector), std::ref(stop_signal_called));
    
    // AGC implementation
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> agc_fifo;
    std::thread AGC(AGC_thread, std::ref(detected_fifo), std::ref(agc_fifo), std::ref(stop_signal_called), AGC_type);

    // Filter thread (Match Filter)
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> filtered_fifo;
    std::thread match_filter(match_filter_thread, std::ref(agc_fifo), std::ref(filtered_fifo),
                              filter_type, symbol_rate, rx_rate, num_taps, U, int(1), roll_off, 
                              num_threads, std::ref(stop_signal_called), "receiver");
    
    // Time synchronization (simple synchronization ACQ, using known preamble sequence)
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> synced_fifo;

    std::thread simple_synchronization(TimeSync_thread, std::ref(filtered_fifo), std::ref(synced_fifo),
                                       std::ref(dbpsk_preamble), U, D, sps_sync, std::ref(stop_signal_called),
                                       message_length, sync_threshold);
                
    // Demodulated the sychronized bits
    MutexFIFO<std::pair<size_t, std::vector<uint8_t>>> demodulated_bits;
    std::thread demodulation(demodulation_thread, std::ref(synced_fifo), std::ref(demodulated_bits),
                             std::ref(scheme), std::ref(stop_signal_called));


    receive.join();
    energy_detection.join();
    AGC.join();
    match_filter.join();
    simple_synchronization.join();
    demodulation.join();

    return EXIT_SUCCESS;
}

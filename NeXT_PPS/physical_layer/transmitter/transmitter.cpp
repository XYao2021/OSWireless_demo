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
# include <map>

// Unused but useful library
// # include <fstream>  // File reading / writing

# include "filters.hpp"
# include "messages.hpp"
# include "FIFO.hpp"
// # include "taps.hpp"
# include "modulator.hpp"
# include "transceiver.hpp"

namespace po = boost::program_options;

static bool stop_signal_called = false;
void sig_int_handler(int){
    stop_signal_called = true;
}

int UHD_SAFE_MAIN(int argc, char* argv[]) {

    // Message parameters
    int num_bits, interval, preamble_length;
    bool continues, add_preamble;
    std::string preamble;

    // Modulation parameters
    // samples per symbol (sps) = U / D

    // Filter parameters
    int U, D, num_taps, num_threads, sps;
    double tx_rate, tx_freq, symbol_rate, roll_off;
    std::string filter_type;

    // Transmitter parameters
    std::string tx_args, tx_ant, type, tx_subdev, scheme, data_type, ref, otw;
    double tx_gain, tx_bw, settling_time, uhd_timeout;
    int tx_channel;

    po::options_description desc("Allowed Options");

    desc.add_options()
        ("help", "help message")
        
        // Message settings
        ("num_bits", po::value<int>(&num_bits)->default_value(1000), "number of bits send to FIFO")
        ("interval", po::value<int>(&interval)->default_value(1000), "interval time in ms between packets, set to 0 if continues mode")
        ("data_type", po::value<std::string>(&data_type)->default_value("float"), "data tyoe for transmission, only consider float now")
        ("preamble", po::value<std::string>(&preamble)->default_value("None"), "m-sequence or Zadoff-chu sequence")
        ("m", po::value<int>(&preamble_length)->default_value(5), "The preamble length (m-sequence) and root (Zadoff sequence)")
        ("add_preamble", po::value<bool>(&add_preamble)->default_value(true), "Add preamble before the header + payload or not")

        // Filter settings
        ("U", po::value<int>(&U)->default_value(5), "Upsampling factor")
        ("D", po::value<int>(&D)->default_value(4), "Downsampling factor")
        ("filter_type", po::value<std::string>(&filter_type)->default_value("rrc"), "Filter taps type: RRC / RC / Low Pass")
        ("symbol_rate", po::value<double>(&symbol_rate)->default_value(double(0.8e6)), "symbol rate")
        ("num_taps", po::value<int>(&num_taps)->default_value(151), "Number of taps, normally 6-15 * sps")
        ("roll_off", po::value<double>(&roll_off)->default_value(0.25), "Roll-off factor of RRC / RC filter, no use in Low pass filter")
        ("num_threads", po::value<int>(&num_threads)->default_value(1), "Number of threads using for FFT processing")

        // Transmitter settings
        ("tx-args", po::value<std::string>(&tx_args)->default_value(""), "uhd transmitter device address args")
        ("tx-rate", po::value<double>(&tx_rate)->default_value(double(1e6)), "transmit rate (sample rate)")
        ("tx-freq", po::value<double>(&tx_freq)->default_value(2.412e9), "transmite central frequency")
        ("tx-gain", po::value<double>(&tx_gain)->default_value(20.0), "transmit gain for USRP")
        ("tx-bw", po::value<double>(&tx_bw)->default_value(500e3), "transmit bandwidth")
        ("tx-ant", po::value<std::string>(&tx_ant)->default_value("TX/RX"), "transmit antenna TX/RX")
        ("tx-channel", po::value<int>(&tx_channel)->default_value(0), "transmit channel (0 or 1)")
        ("tx-subdev", po::value<std::string>(&tx_subdev)->default_value("A:0"), "transmit subdev specification")
        ("tx-int-n", "tune USRP TX with integer-N tuning")
        
        ("continues", po::value<bool>(&continues)->default_value(false), "transmit mode: continues or not")
        ("uhd_timeout", po::value<double>(&uhd_timeout)->default_value(1000.0), "UHD transmitter timeout in ms, upper bound for waiting time")
        ("ref", po::value<std::string>(&ref)->default_value("internal"), "clock reference (internal, external, mimo)")
        ("otw", po::value<std::string>(&otw)->default_value("sc16"), "specifty the over the wire sample mode")
        ("settling", po::value<double>(&settling_time)->default_value(0.2), "settling time for transmitter")

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

    std::signal(SIGINT, sig_int_handler);

    // Create USRP device
    uhd::usrp::multi_usrp::sptr tx_usrp = uhd::usrp::multi_usrp::make(tx_args);

    // std::cout << "----------------------------------------Setting start----------------------------------------------" << std::endl;

    // Setup the USRP parameters
    // Always select subdevice first

    if (vm.count("tx-subdev")){
        tx_usrp->set_tx_subdev_spec(tx_subdev);
    }
    std::cout << "Using TX Device: " << tx_usrp->get_pp_string() << std::endl;

    // Set clock reference
    if (vm.count("ref")){
        tx_usrp->set_clock_source(ref);
    }
    
    tx_usrp->set_tx_rate(tx_rate);

    uhd::tune_request_t tx_tune_request(tx_freq);

    if (vm.count("tx-int-n")){
        tx_tune_request.args = uhd::device_addr_t("mode_n=integer");
    }
    tx_usrp->set_tx_freq(tx_tune_request);
    tx_usrp->set_tx_gain(tx_gain);
    tx_usrp->set_tx_antenna(tx_ant);
    tx_usrp->set_tx_bandwidth(tx_bw);

    // Check LO locked
    std::vector<std::string> tx_sensor_names = tx_usrp->get_tx_sensor_names(0);
    if (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "lo_locked") != tx_sensor_names.end()){
        uhd::sensor_value_t lo_locked = tx_usrp->get_tx_sensor("lo_locked", 0);
        std::cout << boost::format("Checking Tx: %s ...") % lo_locked.to_pp_string() << std::endl;
        UHD_ASSERT_THROW(lo_locked.to_bool());
    }

    // Allow for some setup time
    std::this_thread::sleep_for(std::chrono::milliseconds(long(settling_time * 1000)));

    std::cout << "-------------------------------------------Main start----------------------------------------------" << std::endl;
    
    // Generate the preamble in case for using
    // Generate preamble message if needed  -> m-sequence is correct after checking
    MSequenceGenerator mseq(preamble_length);  // m=5 → 31 bits
    auto dbpsk_preamble = mseq.modulate(PreambleModType::DBPSK);
    // mseq.computeAutocorrelation(dbpsk_preamble);
    save_block_to_txt(dbpsk_preamble, 0, "preamble_sequence_transmitter");

    // Transmit message
    std::vector<std::string> messages = {
        "Hello World!"
    };

    // Message generator (dertermine the packte interval using sleep_time, determine the mode using continues_transmit and sleep_time)
    MutexFIFO<std::vector<uint8_t>> message_fifo;
    std::thread message_generator(message_generator_thread,  // & means give function's pointer to the thread (same with or without it, only matters for variables)
                                 std::ref(message_fifo),
                                 std::ref(messages),
                                 std::ref(stop_signal_called),  // Parameters do not have default value need to placed before the parameters with default value.
                                 num_bits,
                                 continues,
                                 interval);
    
    // Modulation Process
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> mod_fifo;

    std::thread modulation(modulation_thread, 
                          std::ref(message_fifo), 
                          std::ref(mod_fifo), 
                          std::ref(scheme), 
                          std::ref(stop_signal_called),
                          dbpsk_preamble, std::ref(add_preamble));
    
    //Filter design (need to define the data type here)
    std::cout << "[MAIN] Symbol rate: " << symbol_rate << " Sample rate: " << tx_rate << std::endl;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> filter_fifo;

    // double roll_off_computed = static_cast<double>(U) / D - 1;
    // std::cout << "[MAIN DEBUGGING] U = " << U << " D = " << D << " computed roll_off = " << roll_off_computed << " Assigned roll_off = " << roll_off << std::endl;
    std::thread filter(pulse_shaping_filter_thread, 
                       std::ref(mod_fifo),
                       std::ref(filter_fifo),
                       filter_type, 
                       symbol_rate, tx_rate, num_taps, U, D, roll_off, num_threads,
                       std::ref(stop_signal_called), "transmitter");

    // Transmitter
    std::vector<unsigned long> channel = {static_cast<unsigned long>(tx_channel)};
    std::thread transmit(transmit_thread,
                         tx_usrp,
                         std::ref(filter_fifo),
                         tx_rate, channel, uhd_timeout,
                         std::ref(stop_signal_called));

    std::cout << "Press Ctrl+C to stop..." << std::endl;

    message_generator.join();
    modulation.join();
    filter.join();
    transmit.join();

    return EXIT_SUCCESS;
}

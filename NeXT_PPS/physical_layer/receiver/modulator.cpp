# include "modulator.hpp"
# include <iostream>  // needed for std::cout
# include <cmath>
# include <iostream>
# include <cmath>
# include <string>
# include <thread>
# include <cstdint>
# include <fstream>
# include "messages.hpp"
# include "transceiver.hpp"

// Constructor IMPLMENTATION
// Modulator::Modulator(ModulationType type) : mod_type(type) {  // called a memeber initializer list mod_type before the constructor body runs
//     create_constellation();
// }

Modulator::Modulator(ModulationType type) : mod_type(type)
{
    create_constellation();
    is_differential = check_differential();
}

void Modulator::create_constellation()
{
    constellation.clear();

    switch(mod_type){
        case ModulationType::BPSK:
        case ModulationType::DBPSK:
            create_bpsk_constellation();
            break;
        case ModulationType::QPSK:
        case ModulationType::DQPSK:
            create_qpsk_constellation();
            break;
        case ModulationType::PSK8:
        case ModulationType::DPSK8:
            create_8psk_constellation();
            break;
        case ModulationType::QAM16:
            create_16QAM_constellation();
            break;
        case ModulationType::QAM32:
            create_32QAM_constellation();
            break;
        case ModulationType::QAM64:
            create_64QAM_constellation();
            break;
        case ModulationType::QAM128:
            create_128QAM_constellation();
            break;
        case ModulationType::QAM256:
            create_256QAM_constellation();
            break;
        default:
            std::cout << "[CONSTELLATION] Unknown Modulation Scheme!\n";
    }
}

void Modulator::create_bpsk_constellation()
{
    bps = 1;
    constellation = {std::complex<float>(+1.0f, 0.0f),  // bit: 0
                     std::complex<float>(-1.0f, 0.0f)};  // bit: 1
    normalize_constellation();
}

void Modulator::create_qpsk_constellation()
{
    bps = 2;
    float val = 1.0f / std::sqrt(2.0f);  // 0.707
    constellation = {
        std::complex<float>(val, val),  // 00
        std::complex<float>(-val, val),  // 01
        std::complex<float>(-val, -val),  // 11
        std::complex<float>(val, -val)  // 10  
    };
    normalize_constellation();
}

void Modulator::create_8psk_constellation()
{
    bps = 3;
    for (int i = 0; i < 8; i++){
        float angle = 2.0f * M_PI * i / 8.0f;
        constellation.push_back(std::complex<float>(std::cos(angle), std::sin(angle)));
    }
    normalize_constellation();
}

void Modulator::create_16QAM_constellation()
{
    bps = 4;
    std::vector<float> levels = {-3.0f, -1.0f, 1.0f, 3.0f};

    for (int i = 0; i < 4; i++){
        for (int j = 0; j < 4; j++){
            constellation.push_back(std::complex<float>(levels[j], levels[i]));
        }
    }
    normalize_constellation();
}

void Modulator::create_32QAM_constellation()
{
    bps = 5;

    // 32QAM uses a cross pattern
    // Inner square: 4x4 = 16 points (same as 8-PSK)
    std::vector<float> inner_levels = {-3.0f, -1.0f, 1.0f, 3.0f};
    for (float i : inner_levels){
        for (float j : inner_levels){
            constellation.push_back(std::complex<float>(j, i));
        }
    }

    // Outer points: 4 on each axis -> 16 points
    std::vector<float> outer_levels = {-5.0, 5.0};
    for (float val : outer_levels){
        constellation.push_back(std::complex<float>(val, -3.0f));
        constellation.push_back(std::complex<float>(val, -1.0f));
        constellation.push_back(std::complex<float>(val, 1.0f));
        constellation.push_back(std::complex<float>(val, 3.0f));
        constellation.push_back(std::complex<float>(-3.0f, val));
        constellation.push_back(std::complex<float>(-1.0f, val));
        constellation.push_back(std::complex<float>(1.0f, val));
        constellation.push_back(std::complex<float>(3.0f, val));
    }

    // Keep only first 32 points (symmetric selection)
    constellation.resize(32);
    normalize_constellation();
}

void Modulator::create_64QAM_constellation()
{
    bps = 6;
    std::vector<float> levels = {-7.0f, -5.0f, -3.0f, -1.0f, 1.0f, 3.0f, 5.0f, 7.0f};

    for (int i = 0; i < 8; i++){
        for (int j = 0; j < 8; j++){
            constellation.push_back(std::complex<float>(levels[j], levels[i]));
        }
    }
    normalize_constellation();
}

void Modulator::create_128QAM_constellation()
{
    bps = 7;
    
    // 128-QAM typically uses a comnination pattern
    // Here use a simplified version: select from a larger grid
    std::vector<float> levels = {-7.0f, -5.0f, -3.0f, -1.0f, 1.0f, 3.0f, 5.0f, 7.0f};

    for (int i = 0; i < 8; i++){
        for (int j = 0; j < 8; j++){
            constellation.push_back(std::complex<float>(levels[j], levels[i]));
        }
    }

    std::vector<float> outer = {-9.0, 9.0};
    for (float i : levels){
        for (float j : outer){
            constellation.push_back(std::complex<float>(j, i));
            constellation.push_back(std::complex<float>(i, j));
        }
    }

    constellation.resize(128);
    normalize_constellation();
}

void Modulator::create_256QAM_constellation()
{
    bps = 8;

    std::vector<float> levels;
    for (int i = -15; i <= 15; i+=2){
        levels.push_back(static_cast<float>(i));  // static_cast<type>(i) convert i to type(i)
    }

    for (int i = 0; i < 16; i++){
        for (int j = 0; j < 16; j++){
            constellation.push_back(std::complex<float>(levels[j], levels[i]));
        }
    }
    normalize_constellation();
}

void Modulator::normalize_constellation()
{
    float avg_power = 0.0f;
    for (const auto& point : constellation){
        avg_power += std::norm(point);  // |Z|^2 = real^2 + imag^2
    }
    avg_power /= constellation.size();

    float scale = 1.0f / std::sqrt(avg_power);

    for (auto& point : constellation){
        point *= scale;
    }
}

int Modulator::bits_to_index(const std::vector<uint8_t>& bits, int start_position)
{
    int index = 0;
    for (int i = 0; i < bps; i++){
        if (start_position + i < bits.size()){
            index = (index << 1) | bits[start_position + i];  // build binary number bit by bit
        }
    }
    return index;  // return the index of binary number in the constellation vector
}

int Modulator::get_bits_per_symbol() const {
    return bps;
}

std::string Modulator::get_modulation_name() const {
    // static: 
    // value persists between calls (inside function)
    // private to other files (global / file scope)
    // shared by all objects (inside a class (variable))
    // can be called without object (inside a class (function)) -> this case
    static std::map<ModulationType, std::string> names = {
        {ModulationType::BPSK, "BPSK"},
        {ModulationType::QPSK, "QPSK"},
        {ModulationType::PSK8, "8-PSK"},
        {ModulationType::QAM16, "16-QAM"},
        {ModulationType::QAM32, "32-QAM"},
        {ModulationType::QAM64, "64-QAM"},
        {ModulationType::QAM128, "128-QAM"},
        {ModulationType::QAM256, "256-QAM"}
    };
    return names[mod_type];
}

int Modulator::get_constellation_size() const {
    return constellation.size();
}

const std::vector<std::complex<float>>& Modulator::get_constellation() const {
    return constellation;
}

// // Differential encoder and decoder if is_differential is true
// std::vector<std::complex<float>> Modulator::differential_encode(const std::vector<std::complex<float>>& symbols)
// {
//     if (symbols.empty()) return {};

//     std::vector<std::complex<float>> encoded;
//     encoded.reserve(symbols.size());

//     std::complex<float> pre_symbol = constellation[0];  // fixed reference phase 0°
//     // std::cout << "[DIFFERENTIAL ENCODING] The starting point: " << pre_symbol << std::endl;

//     for (size_t i = 0; i < symbols.size(); ++i) {
//         std::complex<float> current_symbol = pre_symbol * symbols[i];
//         encoded.push_back(current_symbol);
//         pre_symbol = current_symbol;
//     }

//     return encoded;
// }

std::vector<std::complex<float>> Modulator::differential_encode(
    const std::vector<std::complex<float>>& symbols, std::complex<float> pre_symbol)
{
    if (symbols.empty()) return {};

    std::vector<std::complex<float>> encoded;
    encoded.reserve(symbols.size());

    // // ========== ADD DEBUG ==========
    // std::cout << "[DIFF_ENCODE] Starting symbol: " << constellation[0] << std::endl;
    // std::cout << "[DIFF_ENCODE] Input symbol[0]: " << symbols[0] << std::endl;
    // std::cout << "[DIFF_ENCODE] Input symbol[1]: " << symbols[1] << std::endl;
    // // ===============================

    // encoded.push_back(pre_symbol);

    for (size_t i = 0; i < symbols.size(); ++i) {
        std::complex<float> current_symbol = pre_symbol * symbols[i];
        encoded.push_back(current_symbol);
        
        // // ========== ADD DEBUG (first 5 iterations) ==========
        // if (i < 20) {
        //     std::cout << "[DIFF_ENCODE] i=" << i 
        //               << " | pre=" << pre_symbol 
        //               << " | input=" << symbols[i]
        //               << " | output=" << current_symbol << std::endl;
        // }
        // // ====================================================
        
        pre_symbol = current_symbol;
    }

    return encoded;
}

std::vector<std::complex<float>> Modulator::differential_decode(const std::vector<std::complex<float>>& symbols)
{
    // std::cout << "[DIFFERENTIAL] differential_decode(): input size = " << symbols.size() << std::endl;

    if (symbols.size() < 2) {
        std::cout << "[DEBUG] input too small, returning empty\n";
        return {};
    }

    std::vector<std::complex<float>> decoded;
    decoded.reserve(symbols.size() - 1);

    for (size_t i = 1; i < symbols.size(); i++) {
        decoded.push_back(symbols[i] * std::conj(symbols[i-1]));
    }

    // std::cout << "[DIFFERENTIAL] differential_decode(): output size = " << decoded.size() << std::endl;
    return decoded;
}

// Main modulation fucntion: bits -> symbols
std::vector<std::complex<float>> Modulator::modulate(const std::vector<uint8_t>& bits,
                                                     std::vector<std::complex<float>>& preamble_sequence, 
                                                     bool& add_preamble)
{
    std::vector<std::complex<float>> symbols;

    int num_symbols = (bits.size() + bps - 1) / bps;  // forces to round up -> enough symbol for all bits
    symbols.reserve(num_symbols);

    // Convert bits to symbol
    for (int i = 0; i < bits.size(); i += bps){
        int index = bits_to_index(bits, i);

        // Check bounds
        if (index < constellation.size()){
            symbols.push_back(constellation[index]); 
            // std::cout << "[MODULATE DEBUG]" << constellation[index] << std::endl;
        } else {
            // Shouldn't happen with proper implementation
            std::cerr << "[WARNING] Invalid symbol index " << index << std::endl;
            symbols.push_back(constellation[0]);
        }
    }

    std::vector<std::complex<float>> encoded_symbols;
    std::complex<float> pre_symbol = preamble_sequence.back();

    if (is_differential){
        encoded_symbols = differential_encode(symbols, pre_symbol);
    } else {
        encoded_symbols = symbols;
    }

    std::vector<std::complex<float>> returned_symbols;
    if (add_preamble){
        returned_symbols = encoded_symbols;
        returned_symbols.insert(returned_symbols.begin(), preamble_sequence.begin(), preamble_sequence.end());
        returned_symbols.insert(returned_symbols.begin(), preamble_sequence.end()-10, preamble_sequence.end());
    } else {
        returned_symbols = encoded_symbols;
    }

    return returned_symbols;
}

std::vector<uint8_t> Modulator::demodulate(const std::vector<std::complex<float>>& symbols)
{
    std::vector<std::complex<float>> decoded_symbols;

    if (is_differential){
        decoded_symbols = differential_decode(symbols);
    } else {
        decoded_symbols = symbols;
    }

    std::vector<uint8_t> bits;
    bits.reserve(decoded_symbols.size() * bps);

    for (const auto& symbol : decoded_symbols){
        // Find nearest constellation point (this is a hard decision)
        int nearest_index = 0;
        float min_distance = std::norm(symbol - constellation[0]);

        for (int i = 1; i < static_cast<int>(constellation.size()); i++){
            float distance = std::norm(symbol - constellation[i]);
            if (distance < min_distance){
                min_distance = distance;
                nearest_index = i;
            }
        }

        for (int i = bps - 1; i >= 0; i--){  // // shift right -> extract from MSB least significant bit (LSB) (inverse if loop i++)
            bits.push_back((nearest_index >> i) & 1); 
        }
    }

    return bits;
}

void Modulator::print_constellation_info()
{
    std::cout << "\n================" << get_modulation_name() << "Constellation ==================" << std::endl;
    std::cout << "Bits per symbol: " << bps <<std::endl;
    std::cout << "Constellation size: " << constellation.size() << std::endl;
    std::cout << "Points: " << std::endl;

    for (int i = 0; i < constellation.size(); i++){
        std::string bits_str = "";
        for (int j = bps - 1; j >= 0; j--){
            bits_str += ((i >> j) & 1) ? "1" : "0";
        }
        std::cout << "  [" << bits_str << "] -> (" << constellation[i].real() << ", " << constellation[i].imag() << ")" << std::endl;
    }
}

float calculate_ser(const std::vector<std::complex<float>>& tx_symbols, const std::vector<std::complex<float>>& rx_symbols)
{
    if (tx_symbols.size() != rx_symbols.size()){
        std::cerr << "[ERROR] Symbol vectors have different sizes!\n";
        return -1.0f;
    }
    int errors = 0;
    for (size_t i = 0; i < tx_symbols.size(); i++){
        if (std::abs(tx_symbols[i] - rx_symbols[i]) > 0.01f){
            errors++;
        }
    }
    return static_cast<float>(errors) / tx_symbols.size();
}

float calculate_ber(const std::vector<uint8_t>& tx_bits, const std::vector<uint8_t>& rx_bits)
{
    size_t min_size = std::min(tx_bits.size(), rx_bits.size());
    int errors = 0;

    for (size_t i = 0; i < min_size; i++){
        if (tx_bits[i] != rx_bits[i]){
            errors++;
        }
    }
    return static_cast<float>(errors) / min_size;
}

void modulation_thread(MutexFIFO<std::vector<uint8_t>>& fifo, 
                       MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>>& fifo_out,
                       std::string& scheme, std::atomic<bool>& stop_sign,
                       std::vector<std::complex<float>> preamble_sequence, bool& add_preamble)
{   
    ModulationType mod_type;
    if (scheme == "BPSK") mod_type = ModulationType::BPSK;
    else if (scheme == "QPSK") mod_type = ModulationType::QPSK;
    else if (scheme == "8-PSK") mod_type = ModulationType::PSK8;
    else if (scheme == "16-QAM") mod_type = ModulationType::QAM16;
    else if (scheme == "32-QAM") mod_type = ModulationType::QAM32;
    else if (scheme == "64-QAM") mod_type = ModulationType::QAM64;
    else if (scheme == "128-QAM") mod_type = ModulationType::QAM128;
    else if (scheme == "256-QAM") mod_type = ModulationType::QAM256;
    else if (scheme == "DBPSK") mod_type = ModulationType::DBPSK;
    else if (scheme == "DQPSK") mod_type = ModulationType::DQPSK;
    else if (scheme == "8-DPSK") mod_type = ModulationType::DPSK8;
    else throw std::invalid_argument("Unknown modulation scheme");

    Modulator Modulation = Modulator(mod_type);
    std::vector<std::complex<float>> symbols;
    std::vector<uint8_t> bits;
    size_t message_block_id = 0;
    size_t tried_time = 0;

    // std::ofstream mod_out("modulated_samples.txt");

    while (!stop_sign.load() || fifo.size() > 0){
        // Debugging printout
        // std::cout << "[MODULATION] Number " << tried_time << " Input FIFO size: " << fifo.size() << std::endl;

        if (!fifo.pop(bits)){
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            tried_time++;
            continue;
        }
        tried_time = 0;

        // save_bits_to_txt(bits, static_cast<int>(message_block_id), "before_modulate");
        symbols = Modulation.modulate(bits, preamble_sequence, add_preamble);

        // float rms=0, peak=0;
        // for (auto& s : symbols) {
        //     float mag = std::abs(s);
        //     rms += mag*mag;
        //     peak = std::max(peak, mag);
        // }
        // rms = std::sqrt(rms / symbols.size());
        // std::cout << "[CHECK AFTER MODULATION] Stage MODULATION: RMS=" << rms << " Peak=" << peak << std::endl;


        // push the FIFO out for further filtering
        // Push to fifo_out successfully
        fifo_out.push({message_block_id, symbols});
        // save_block_to_txt(symbols, message_block_id, "modulated");

        // std::cout << "[MODULATION] Output FIFO size: " << fifo_out.size() << std::endl;
    
        message_block_id += 1;

    }
    std::cout << "[MODULATION] Thread stopped gracefully." << std::endl;
}

void demodulation_thread(MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>>& fifo, 
                       MutexFIFO<std::pair<size_t, std::vector<uint8_t>>>& fifo_out,
                       std::string& scheme, std::atomic<bool>& stop_sign)
{   
    ModulationType mod_type;
    if (scheme == "BPSK") mod_type = ModulationType::BPSK;
    else if (scheme == "QPSK") mod_type = ModulationType::QPSK;
    else if (scheme == "8-PSK") mod_type = ModulationType::PSK8;
    else if (scheme == "16-QAM") mod_type = ModulationType::QAM16;
    else if (scheme == "32-QAM") mod_type = ModulationType::QAM32;
    else if (scheme == "64-QAM") mod_type = ModulationType::QAM64;
    else if (scheme == "128-QAM") mod_type = ModulationType::QAM128;
    else if (scheme == "256-QAM") mod_type = ModulationType::QAM256;
    else if (scheme == "DBPSK") mod_type = ModulationType::DBPSK; 
    else if (scheme == "DQPSK") mod_type = ModulationType::DQPSK; // The magintude is not correct
    else if (scheme == "8-DPSK") mod_type = ModulationType::DPSK8;
    else throw std::invalid_argument("Unknown modulation scheme");

    Modulator Modulation = Modulator(mod_type);
    std::pair<size_t, std::vector<std::complex<float>>> symbols;
    std::vector<uint8_t> bits;
    size_t message_block_id = 0;
    size_t tried_time = 0;

    while (!stop_sign.load() || fifo.size() > 0){
        // Debugging printout
        // std::cout << "[MODULATION] Number " << tried_time << " Input FIFO size: " << fifo.size() << std::endl;

        if (!fifo.pop(symbols)){
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            tried_time++;
            continue;
        }

        // std::cout << "[DEMODULATION] Original bits length is: " << symbols.second.size() << std::endl;
        tried_time = 0;
        bits = Modulation.demodulate(symbols.second);

        // push the FIFO out for further filtering
        // Push to fifo_out successfully
        fifo_out.push({symbols.first, bits});
        // save_bits_to_txt(bits, symbols.first, "demodulated");
        // std::cout << std::endl;
        message_block_id += 1;

        // std::string message = decode_message_block(bits);
        // std::cout << "[DEMODULATION] The demodulated success number " << message_block_id << std::endl;
        // std::cout << std::endl;

        // std::cout << "[DEMODULATION] Output FIFO size: " << fifo_out.size() << std::endl;
    }
    std::cout << "[DEMODULATION] Thread stopped gracefully." << std::endl;
}
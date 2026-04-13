# include <iostream>
# include <csignal>
# include <cmath>
# include <functional>
# include <mutex>  // for FIFO queue and multi-thread processing
# include <vector>
# include <list>
# include <random>
# include <bitset>
# include "messages.hpp"
# include "transceiver.hpp"
# include <cstdint>  // for uint8_t
# include <mutex>
# include "FIFO.hpp"
# include <complex>
# include <stdexcept>
# include <string>
# include <thread>
# include <fstream>

// ---------------------------------------------------- Message related functions ---------------------------------------------------- //
std::vector<uint8_t> string_to_bits(const std::string& message)
{
    std::vector<uint8_t> bits;
    bits.reserve(message.length() * 8);
    for (char c : message){
        // Convert each character to 8 bits (MSB first)
        for (int i = 7; i >= 0; i--){  
            // This counts down extracts bits from Most Significant Bit (MSB) to Least Significant Bit (LSB).
            // Standard way to represent binary -> leftmost bit first
            // Example: c='H' -> 'H' >>(right shift) 7 & 1 (extracts only the rightmost bit)
            // 'H' = 72 (ASCII) -> 01001000
            bits.push_back((c >> i) & 1);
        }
    }
    return bits;
}

std::vector<uint8_t> bits_to_bytes(const std::vector<uint8_t>& bits)
{
    std::vector<uint8_t> bytes;

    for (size_t i = 0; i + 7 < bits.size(); i += 8){
        uint8_t byte = 0;

        for (int j = 0; j < 8; j++){
            byte |= (bits[i + j] << (7 - j));
        }

        bytes.push_back(byte);
    }

    return bytes;
}

std::string bits_to_string(const std::vector<uint8_t> bits, size_t num_bytes){
    std::string message;
    message.reserve(num_bytes);

    for (size_t i=0; i<num_bytes; i++){
        uint8_t byte = 0;  // start from 00000000
        for (int j = 0; j < 8; j++){
            if (i * 8 + j < bits.size()){
                // << (left shift) 1: moves all bits one position to left
                // | bits[i*8+j]: Adds the new bit to the rightmost position
                byte = (byte << 1) | bits[i * 8 + j];
            }
        }
        message.push_back(byte);
    }
    return message;
}

// Generate a message block with padding
std::vector<uint8_t> generate_message_block(std::string& message,
                                            size_t block_idx,
                                            size_t target_bits = 1000)
{
    std::vector<uint8_t> bits;
    bits.reserve(target_bits);

    // std::cout << "[GENERATOR] Added 16-bit header (block index = " << block_idx << ")" << std::endl;

    // uint16_t msg_length = static_cast<uint16_t>(message.length());
    // for (int i = 15; i >= 0; i--) {
    //     bits.push_back((msg_length >> i) & 1);
    // }
    // std::cout << "[GENERATOR] Added 16-bit message length (" << msg_length << " chars)" << std::endl;

    // Convert message to bits
    // std::vector<uint8_t> msg_bits = string_to_bits(message);
    // bits.insert(bits.end(), msg_bits.begin(), msg_bits.end());

    // Pad with random bits if needed
    if (bits.size() < target_bits){
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 1);

        size_t padding_needed = target_bits - bits.size();
        for (size_t i=0; i<padding_needed; i++){
            bits.push_back(dis(gen));
        }
        // std::cout << "[GENERATOR] Added " << padding_needed << " random padding bits" << std::endl;
    } else if (bits.size() == target_bits) {
        std::cout << "[MESSAGE] The message length satisfy the requirement.\n";
    } else {
        std::cout << "[MESSAGE] [WARNING] Message length exceed the requirement!\n";
    }

    // Add header: message index
    std::vector<uint8_t> header;
    uint16_t block_id = static_cast<uint16_t>(block_idx + 19999);

    for (int i = 15; i >= 0; i--){
        header.push_back((block_id >> i) & 1);
    }

    bits.insert(bits.begin(), header.begin(), header.end());
    
    return bits;
}

// Decode a message block (extract message from bits)
std::string decode_message_block(const std::vector<uint8_t>& bits)
{
    if (bits.size() < 16){
        return "Not enough bits for Header!\n";
    }

    // Read message length from header
    uint16_t msg_length = 0;
    for (int i = 0; i < 16; i++){
        msg_length = (msg_length << 1) | bits[i];
    }

    // Extract message bits (skip header)
    std::vector<uint8_t> msg_bits(bits.begin()+16, bits.begin() + 16 + 8 * msg_length);

    // Convert bits to string
    return bits_to_string(msg_bits, msg_length);
}

// --------------------------------------------------- Message thread used in main ------------------------------------------------------ //
void message_generator_thread(MutexFIFO<std::vector<uint8_t>>& fifo,
                              const std::vector<std::string>& messages,
                              std::atomic<bool>& stop_flag,  // Parameters do not have default value need to placed before the parameters with default value.
                              size_t target_bits = 1000,
                              bool continuous = false,
                              size_t sleep_time = 1000)  // sleep time in ms
{
    // Input validation
    if (messages.empty()) {
        std::cerr << "[GENERATOR] ERROR: Empty message list!" << std::endl;
        return;
    }

    size_t msg_index = 0;
    size_t block_count = 0;

    std::string current_message = messages[msg_index % messages.size()];
    std::vector<uint8_t> bit_block = generate_message_block(current_message, block_count, target_bits);
    // save_bits_to_txt(bit_block, static_cast<int>(0), "message");

    while (!stop_flag.load()){
        fifo.push(bit_block);
        
        block_count++;
        msg_index++;

        // Wait for interval seconds if the transmit mode is not continues
        if (!continuous && sleep_time > 0) {
            std::this_thread::sleep_for(std::chrono::milliseconds(sleep_time));
        }
    }
    std::cout << "[Generator] Stopped. Generated " << block_count << " blocks. " << std::endl;
}

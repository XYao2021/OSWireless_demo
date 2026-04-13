#include <iostream>
#include <complex>
#include <vector>
#include <cmath>
#include <mutex>
#include <algorithm>
#include <thread>

#include "FIFO.hpp"
#include "synchronization.hpp"
#include "transceiver.hpp"


void TimeSync_thread(MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>>& detected_fifo,
                     MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>>& synced_fifo,
                     std::vector<std::complex<float>>& preamble_sequence,
                     size_t U, size_t D, int sps, std::atomic<bool>& stop_sign,
                     int Data_length, float threshold)
{
    size_t processed_blocks = 0;
    std::pair<size_t, std::vector<std::complex<float>>> detected_message;

    ACQSynchronizer ACQ(preamble_sequence, sps, threshold, Data_length, true);

    while (!stop_sign.load() || detected_fifo.size() > 0){
        
        if (!detected_fifo.pop(detected_message)){
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;;
        }

        // Perform ACQ
        auto result = ACQ.PerformACQOptimized(detected_message.second);
        // auto result = ACQ.SamplesACQPerformance(detected_message.second);
        
        if (result.PacketDetected) {
            // std::cout << "\n✓ Packet detected successfully!" << std::endl;
            // std::cout << "  Decision statistics ready for demodulation" << std::endl;
            // std::cout << "  Number of symbols: " << result.DecisionStats.size() << std::endl;
            
            // Push to demodulation FIFO
            synced_fifo.push({detected_message.first, result.DecisionStats});     
            processed_blocks++;
            // save_block_to_txt(result.DecisionStats, detected_message.first, "sync");
        } else {
            std::cout << "\n✗ No packet detected in this block" << std::endl;
        }
    }
}
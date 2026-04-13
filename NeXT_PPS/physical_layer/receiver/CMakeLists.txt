cmake_minimum_required(VERSION 3.12)
project(receiver_python_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python and pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Find UHD (USRP Hardware Driver)
# If you're using USRP, uncomment this:
find_package(UHD REQUIRED)

find_library(FFTW3F_LIB fftw3f REQUIRED)
find_library(FFTW3F_THREADS_LIB fftw3f_threads REQUIRED)
find_path(FFTW3_INCLUDE_DIRS fftw3.h REQUIRED)

# Add your existing source files here
set(YOUR_SOURCES
    messages.cpp 
    modulator.cpp 
    filters.cpp 
    transceiver.cpp
    synchronization.cpp
)

# Create the Python module
pybind11_add_module(receiver 
    receiver_python.cpp
    ${YOUR_SOURCES}
)

# Include directories for your headers
target_include_directories(receiver PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    # Add your include directories, for example:
    # ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link libraries
find_package(Threads REQUIRED)
target_link_libraries(receiver PRIVATE 
    Threads::Threads
)

# If using UHD, uncomment:
target_link_libraries(receiver PRIVATE ${UHD_LIBRARIES})
target_include_directories(receiver PRIVATE ${UHD_INCLUDE_DIRS})

target_include_directories(receiver PRIVATE ${FFTW3_INCLUDE_DIRS})

target_link_libraries(receiver PRIVATE
    ${FFTW3F_LIB}
    ${FFTW3F_THREADS_LIB}
)

# Set output directory
set_target_properties(receiver PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)
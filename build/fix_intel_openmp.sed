s/find_library(IOMP5_LIBRARY iomp5 libiomp5md/# find_library(IOMP5_LIBRARY iomp5 libiomp5md/
s/message(FATAL_ERROR "Intel OpenMP runtime libiomp5 not found")/message(STATUS "Using ROCm OpenMP")\n      set(OPENMP_FOUND 1)\n      set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp")/

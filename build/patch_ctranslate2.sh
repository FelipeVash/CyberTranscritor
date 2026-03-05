#!/bin/bash

# Aplicar patch no CMakeLists.txt
CTRANSLATE_DIR="$1"
cd "$CTRANSLATE_DIR"

# Backup
cp CMakeLists.txt CMakeLists.txt.original

# Remover verificações OpenMP
sed -i '/find_package.*OpenMP.*REQUIRED/d' CMakeLists.txt
sed -i '/if.*OpenMP_FOUND.*/,/endif/d' CMakeLists.txt
sed -i 's/OpenMP::OpenMP_CXX//g' CMakeLists.txt

# Adicionar configuração ROCm
echo "# ROCm configuration" >> CMakeLists.txt
echo "set(ROCM_PATH /opt/rocm CACHE PATH \"Path to ROCm\")" >> CMakeLists.txt
echo "list(APPEND CMAKE_PREFIX_PATH \"${ROCM_PATH}/lib/cmake\" \"${ROCM_PATH}/hip/cmake\")" >> CMakeLists.txt
echo "find_package(hip REQUIRED)" >> CMakeLists.txt
echo "find_package(rocblas REQUIRED)" >> CMakeLists.txt
echo "find_package(hipblas REQUIRED)" >> CMakeLists.txt

echo "Patch aplicado"

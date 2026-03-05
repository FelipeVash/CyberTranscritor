#!/bin/bash

# Compilar ctranslate2
CTRANSLATE_DIR="/home/felipevash/projetos/transcritor/build/CTranslate2-rocm"
ROCM_PATH="/opt/rocm"

# Aplicar patch
echo "Aplicando patch..."
/home/felipevash/projetos/transcritor/build/patch_ctranslate2.sh "$CTRANSLATE_DIR"

# Criar diretório de build
mkdir -p "$CTRANSLATE_DIR/build"
cd "$CTRANSLATE_DIR/build"

# CMake command
cmake \
    -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_PREFIX_PATH="$ROCM_PATH" \
    -DCMAKE_BUILD_TYPE=Release \
    -DWITH_ROCM=ON \
    -DROCM_PATH="$ROCM_PATH" \
    -DWITH_CUDA=OFF \
    -DWITH_MKL=OFF \
    -DOPENMP_FOUND=1 \
    -DOpenMP_CXX_FLAGS="-fopenmp" \
    -DOpenMP_CXX_LIB_NAMES="omp" \
    -DOpenMP_omp_LIBRARY="$ROCM_PATH/lib/libomp.so" \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    ..

# Compilar
echo "Compilando (pode levar 10-20 minutos)..."
make -j$(nproc)

# Instalar
echo "Instalando..."
sudo make install
sudo ldconfig

echo "Compilação concluída!"
ls -la /usr/local/lib/libctranslate2.so

#!/bin/bash

# Warna untuk output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== BEJO AI API Server ===${NC}"
echo ""

# Cek apakah Python terinstall (python atau python3)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}Python 3 terdeteksi.${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}Python terdeteksi.${NC}"
else
    echo -e "${RED}Python tidak ditemukan. Pastikan Python terinstall.${NC}"
    exit 1
fi

# Cek apakah uv terinstall
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    echo -e "${GREEN}uv terdeteksi, menggunakan uv untuk dependensi.${NC}"
else
    echo -e "${YELLOW}uv tidak terdeteksi, menggunakan pip.${NC}"
    echo -e "${YELLOW}Untuk performance lebih baik, install uv: https://github.com/astral-sh/uv${NC}"
fi

# Buat file .env jika belum ada
if [ ! -f .env ]; then
    echo -e "${YELLOW}File .env tidak ditemukan, membuat file .env default...${NC}"
    cat > .env << EOL
# API Keys (you can leave this empty for now)
GOOGLE_API_KEY=

# Server Config
PORT=8000
HOST=0.0.0.0
EOL
    echo -e "${GREEN}File .env berhasil dibuat.${NC}"
fi

# Cek apakah dependensi sudah terinstall
echo -e "${YELLOW}Memeriksa dependensi...${NC}"
MISSING_DEPS=false
MISSING_DEP_LIST=""

# Fungsi untuk memeriksa dependensi Python
check_dep() {
    $PYTHON_CMD -c "import $1" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}Dependensi '$1' tidak ditemukan.${NC}"
        MISSING_DEPS=true
        MISSING_DEP_LIST="$MISSING_DEP_LIST $1"
    fi
}

# Cek dependensi utama
check_dep fastapi
check_dep uvicorn
check_dep sse_starlette

# Jika ada dependensi yang hilang, install
if [ "$MISSING_DEPS" = true ]; then
    echo -e "${YELLOW}Beberapa dependensi tidak ditemukan. Menginstall...${NC}"
    echo -e "${YELLOW}Akan menginstall: $MISSING_DEP_LIST${NC}"
    if [ "$USE_UV" = true ]; then
        uv sync
    else
        $PYTHON_CMD -m pip install fastapi uvicorn sse-starlette
    fi
fi

# Jalankan API
echo -e "${GREEN}Menjalankan API server...${NC}"
echo -e "${YELLOW}Tekan Ctrl+C untuk menghentikan server${NC}"
echo ""

# Jalankan API
$PYTHON_CMD app/main_api.py 
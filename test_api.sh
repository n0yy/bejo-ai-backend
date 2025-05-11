#!/bin/bash

# Warna untuk output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== BEJO AI API Tester ===${NC}"
echo ""

API_URL="http://localhost:8000"
USER_ID="test-user-$(date +%s)"

# Cek apakah jq terinstall untuk format JSON yang lebih baik
USE_JQ=false
if command -v jq &> /dev/null; then
    USE_JQ=true
    echo -e "${GREEN}jq terdeteksi, akan memformat JSON dengan lebih baik.${NC}"
else
    echo -e "${YELLOW}jq tidak terdeteksi, gunakan 'apt install jq' untuk instalasi.${NC}"
fi

# Fungsi untuk menampilkan command yang dijalankan
run_cmd() {
    echo -e "${YELLOW}Running: $1${NC}"
    eval "$1"
    echo ""
}

# 1. Buat session
echo -e "${GREEN}1. Membuat session baru...${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\"}")

# Format JSON response jika jq tersedia
if [ "$USE_JQ" = true ]; then
    echo -e "${BLUE}Response:${NC}"
    echo $SESSION_RESPONSE | jq
fi

SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"session_id":"[^"]*' | sed 's/"session_id":"//')

if [ -z "$SESSION_ID" ]; then
    echo -e "${RED}ERROR: Tidak bisa mendapatkan session_id!${NC}"
    exit 1
fi

echo -e "${GREEN}Session ID: $SESSION_ID${NC}"
echo -e "${GREEN}User ID: $USER_ID${NC}"
echo ""

# 2. Kirim pertanyaan
echo -e "${GREEN}2. Mengirim pertanyaan...${NC}"
echo -e "${BLUE}Streaming response dimulai...${NC}"
echo -e "${BLUE}Tekan Ctrl+C untuk berhenti menerima data${NC}"
echo ""

# Gunakan pertanyaan tentang SQL
SQL_QUESTIONS=(
  "Jelaskan apa itu SQL JOIN dan berikan contoh"
  "Tampilkan PIC dari mesin ilapak dan unifill"
  "Perbandingan OEE Unifill A dan B di tahun 2020"
)

# Pilih pertanyaan secara acak
RANDOM_INDEX=$((RANDOM % ${#SQL_QUESTIONS[@]}))
QUESTION="${SQL_QUESTIONS[$RANDOM_INDEX]}"

echo -e "${BLUE}Pertanyaan: $QUESTION${NC}"

# Gunakan fifo untuk menangkap output curl
FIFO="/tmp/curl_fifo_$$"
mkfifo $FIFO
echo "" > $FIFO &

# Mulai curl dengan output ke fifo
curl -N -X POST "$API_URL/ask/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{\"user_id\": \"$USER_ID\", \"question\": \"$QUESTION\"}" > $FIFO &

CURL_PID=$!

# Tunggu beberapa detik agar curl mulai
sleep 1

# Membaca dari FIFO dan memproses output secara real-time
cat $FIFO | while read -r line; do
    if [[ $line == data:* ]]; then
        # Ekstrak JSON data
        json_data=${line#data: }
        
        if [ "$USE_JQ" = true ] && [ ! -z "$json_data" ]; then
            # Format dengan jq jika tersedia
            echo -e "${GREEN}Received:${NC}"
            echo $json_data | jq
        else
            # Tampilkan raw jika jq tidak ada
            echo -e "${GREEN}Received:${NC} $json_data"
        fi
        
        # Cek apakah ada interrupt
        if [[ $json_data == *"interrupt"* ]]; then
            echo -e "${YELLOW}Interrupt terdeteksi, mengirim konfirmasi...${NC}"
            
            # Kirim konfirmasi interrupt (approve=true)
            INTERRUPT_RESPONSE=$(curl -s -X POST "$API_URL/ask/$SESSION_ID/interrupt" \
              -H "Content-Type: application/json" \
              -d "{\"user_id\": \"$USER_ID\", \"approved\": true}")
            
            if [ "$USE_JQ" = true ]; then
                echo -e "${BLUE}Interrupt Response:${NC}"
                echo $INTERRUPT_RESPONSE | jq
            else
                echo -e "${BLUE}Interrupt Response:${NC} $INTERRUPT_RESPONSE"
            fi
        fi
    elif [[ $line == event:* ]]; then
        event_type=${line#event: }
        echo -e "${BLUE}Event: $event_type${NC}"
    fi
done &

PROCESSOR_PID=$!

# Tunggu user untuk membaca response
echo -e "${BLUE}Tekan Enter untuk keluar...${NC}"
read

# Bersihkan
kill $CURL_PID 2>/dev/null
kill $PROCESSOR_PID 2>/dev/null
rm $FIFO 2>/dev/null

echo -e "${GREEN}Test selesai!${NC}" 
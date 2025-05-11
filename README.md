# Dokumentasi BEJO AI Backend untuk Frontend Engineer

## Pengenalan

BEJO AI adalah aplikasi chatbot berbasis AI yang mampu menjawab pertanyaan, terutama dengan mengakses database SQL. Sistem ini dibuat menggunakan Python, FastAPI, dan LangGraph.

## Cara Aplikasi Bekerja

Aplikasi ini berjalan sebagai API server yang bisa dihubungkan dengan aplikasi frontend. BEJO AI dapat:

1. Menerima pertanyaan dari pengguna
2. Menentukan apakah pertanyaan memerlukan akses database
3. Membuat dan menjalankan query SQL jika diperlukan
4. Menunjukkan hasil query kepada pengguna
5. Meminta persetujuan sebelum menjalankan query yang berpotensi berbahaya
6. Menghasilkan jawaban berdasarkan hasil query

## API Endpoints untuk Frontend

### 1. Membuat Session Baru

Setiap percakapan dimulai dengan membuat session baru.

**Endpoint:** `POST /ask`

**Request:**

```json
{
  "user_id": "user123"
}
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Simpan `session_id` ini untuk digunakan pada permintaan selanjutnya.

### 2. Mengirim Pertanyaan

Gunakan endpoint ini untuk mengirim pertanyaan dalam session yang telah dibuat.

**Endpoint:** `POST /ask/{session_id}`

**Request:**

```json
{
  "user_id": "user123",
  "question": "Berapa total penjualan di bulan Mei 2023?"
}
```

**Response:**
Respons berupa Server-Sent Events (SSE) stream dengan format berikut:

#### Event Types:

1. **start** - Awal proses

   ```json
   { "type": "info", "data": "Processing question..." }
   ```

2. **message** - Jawaban dari AI

   ```json
   {
     "type": "answer",
     "data": "Total penjualan di bulan Mei 2023 adalah Rp 5.000.000"
   }
   ```

3. **result** - Hasil query

   ```json
   {
     "type": "result",
     "data": "| Month | Total |\n|-------|-------|\n| May   | 5000000 |"
   }
   ```

4. **interrupt** - Permintaan persetujuan

   ```json
   { "type": "interrupt", "data": "Do you want to execute this query?" }
   ```

5. **error** - Pesan kesalahan

   ```json
   { "type": "error", "data": "Error message" }
   ```

6. **end** - Akhir proses
   ```json
   { "type": "info", "data": "Finished processing question" }
   ```

### 3. Menanggapi Permintaan Persetujuan (Interrupt)

Ketika AI perlu menjalankan query, sistem akan meminta persetujuan pengguna. Frontend harus merespons dengan:

**Endpoint:** `POST /ask/{session_id}/interrupt`

**Request:**

```json
{
  "user_id": "user123",
  "approved": true
}
```

**Response:**

```json
{
  "status": "success",
  "approved": true
}
```

### 4. Cek Kesehatan Server

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2023-06-15T08:30:45.123456",
  "active_sessions": 5
}
```

## Implementasi di Frontend

### 1. Mengelola SSE di Frontend

Contoh implementasi menggunakan JavaScript:

```javascript
// Fungsi untuk membuat session baru
async function createSession(userId) {
  const response = await fetch("http://localhost:8000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });

  const data = await response.json();
  return data.session_id;
}

// Fungsi untuk mengirim pertanyaan dan mendengarkan respons streaming
function askQuestion(sessionId, userId, question, callbacks) {
  const url = `http://localhost:8000/ask/${sessionId}`;

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, question: question }),
  }).then((response) => {
    const eventSource = new EventSource(response.url);

    eventSource.addEventListener("start", (event) => {
      const data = JSON.parse(event.data);
      callbacks.onStart?.(data);
    });

    eventSource.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      callbacks.onMessage?.(data);
    });

    eventSource.addEventListener("result", (event) => {
      const data = JSON.parse(event.data);
      callbacks.onResult?.(data);
    });

    eventSource.addEventListener("interrupt", (event) => {
      const data = JSON.parse(event.data);
      callbacks.onInterrupt?.(data);
    });

    eventSource.addEventListener("error", (event) => {
      const data = JSON.parse(event.data);
      callbacks.onError?.(data);
      eventSource.close();
    });

    eventSource.addEventListener("end", (event) => {
      const data = JSON.parse(event.data);
      callbacks.onEnd?.(data);
      eventSource.close();
    });
  });
}

// Fungsi untuk merespons permintaan persetujuan
async function respondToInterrupt(sessionId, userId, approved) {
  const response = await fetch(
    `http://localhost:8000/ask/${sessionId}/interrupt`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, approved: approved }),
    }
  );

  return await response.json();
}
```

### 2. Contoh Penggunaan dalam Komponen React

```jsx
import React, { useState, useEffect } from "react";

function Chat() {
  const [userId] = useState("user123");
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isWaitingForApproval, setIsWaitingForApproval] = useState(false);

  // Buat session baru saat komponen dimuat
  useEffect(() => {
    async function initSession() {
      const id = await createSession(userId);
      setSessionId(id);
    }
    initSession();
  }, [userId]);

  // Kirim pertanyaan
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    // Tambahkan pertanyaan pengguna ke daftar pesan
    setMessages((prev) => [...prev, { type: "user", content: question }]);

    // Kirim pertanyaan ke API
    askQuestion(sessionId, userId, question, {
      onStart: (data) => {
        console.log("Mulai memproses pertanyaan");
      },
      onMessage: (data) => {
        setMessages((prev) => [...prev, { type: "bot", content: data.data }]);
      },
      onResult: (data) => {
        setMessages((prev) => [
          ...prev,
          { type: "result", content: data.data },
        ]);
      },
      onInterrupt: (data) => {
        setIsWaitingForApproval(true);
        setMessages((prev) => [
          ...prev,
          {
            type: "interrupt",
            content: "Apakah kamu ingin menjalankan query ini?",
          },
        ]);
      },
      onError: (data) => {
        setMessages((prev) => [...prev, { type: "error", content: data.data }]);
      },
      onEnd: () => {
        console.log("Selesai memproses pertanyaan");
      },
    });

    setQuestion("");
  };

  // Merespons permintaan persetujuan
  const handleInterrupt = async (approved) => {
    await respondToInterrupt(sessionId, userId, approved);
    setIsWaitingForApproval(false);

    setMessages((prev) => [
      ...prev,
      {
        type: "system",
        content: approved ? "Query dijalankan" : "Query dibatalkan",
      },
    ]);
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            {msg.type === "result" ? (
              <div dangerouslySetInnerHTML={{ __html: marked(msg.content) }} />
            ) : (
              <p>{msg.content}</p>
            )}
          </div>
        ))}
      </div>

      {isWaitingForApproval && (
        <div className="interrupt-buttons">
          <button onClick={() => handleInterrupt(true)}>Ya</button>
          <button onClick={() => handleInterrupt(false)}>Tidak</button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Tanyakan sesuatu..."
          disabled={isWaitingForApproval}
        />
        <button type="submit" disabled={isWaitingForApproval}>
          Kirim
        </button>
      </form>
    </div>
  );
}
```

## Tips untuk Developer Frontend

1. **Kendalikan Status Session**

   - Simpan `session_id` di state aplikasi atau local storage
   - Pastikan `user_id` konsisten di semua permintaan

2. **Tangani Event Streaming dengan Benar**

   - Gunakan `EventSource` untuk menangani SSE
   - Tutup koneksi SSE ketika tidak diperlukan lagi

3. **Tampilkan Hasil Query dengan Menarik**

   - Gunakan library seperti `marked` untuk menampilkan markdown
   - Tampilkan tabel hasil query dengan format yang menarik

4. **Tangani Interrupt dengan Jelas**

   - Tampilkan dialog konfirmasi yang jelas
   - Gunakan tombol "Ya" dan "Tidak" yang mudah dilihat
   - Tampilkan indikator loading saat menunggu persetujuan

5. **Tangani Error dengan Baik**
   - Tampilkan pesan error yang ramah
   - Berikan opsi untuk mencoba lagi

## Troubleshooting

### Koneksi Terputus

Jika koneksi ke server terputus, pastikan:

- Endpoint API benar
- CORS sudah dikonfigurasi dengan benar di server
- Server sedang berjalan

### Timeout pada Interrupt

- Server menunggu maksimum 60 detik untuk respons
- Pastikan menanggapi permintaan persetujuan sebelum timeout

### Hasil Query Tidak Muncul

- Pastikan event handler `result` terimplementasi dengan benar
- Cek apakah markdown dirender dengan benar

## Kesimpulan

BEJO AI Backend menyediakan API yang kuat untuk membuat aplikasi chatbot yang dapat mengakses database melalui bahasa natural. Dengan mengikuti dokumentasi ini, frontend developer dapat dengan mudah mengintegrasikan backend ini ke dalam aplikasi mereka.

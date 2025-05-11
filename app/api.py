import uuid
import json
import datetime
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from graph.builder import build_graph
from langgraph.checkpoint.memory import MemorySaver

# Inisialisasi MemorySaver untuk menyimpan state
memory = MemorySaver()
# Inisialisasi graph
graph = build_graph(memory)

# Buat dict untuk menyimpan session
active_sessions: Dict[str, Any] = {}

# Simpan status interrupt
interrupt_status = {}

app = FastAPI(title="BEJO AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    user_id: str

class MessageRequest(BaseModel):
    user_id: str
    question: str

class InterruptResponse(BaseModel):
    user_id: str
    approved: bool

@app.post("/ask")
async def create_session(request: AskRequest):
    """
    Membuat session baru untuk chat dengan AI
    
    Args:
        request: Object dengan user_id
        
    Returns:
        Dict dengan session_id yang baru dibuat
    """
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "user_id": request.user_id,
        "created_at": datetime.datetime.now(),
    }
    
    return {"session_id": session_id}

@app.post("/ask/{session_id}")
async def ask_question(session_id: str, request: MessageRequest):
    """
    Mengirim pertanyaan ke AI dalam session tertentu
    
    Args:
        session_id: ID session chat
        request: Object dengan user_id dan question
        
    Returns:
        StreamingResponse dengan jawaban dari AI
    """
    # Validasi session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")
        
    # Validasi user_id match dengan session
    if active_sessions[session_id]["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="User ID tidak sesuai dengan session")
    
    # Reset interrupt status jika ada
    if session_id in interrupt_status:
        del interrupt_status[session_id]
    
    # Konfigurasi untuk graph
    config = {"configurable": {"thread_id": session_id}}
    
    async def generate_stream():
        """Generator untuk streaming response dari AI"""
        try:
            # Kirim pesan awal
            yield {"event": "start", "data": json.dumps({"type": "info", "data": "Memproses pertanyaan..."})}
            
            step_data = {"question": request.question}
            
            # Stream langsung dari graph
            for step in graph.stream(step_data, config, stream_mode="updates"):
                # Jika ada interrupt, kirim notifikasi dan tunggu konfirmasi
                if "__interrupt__" in step:
                    # Kirim event interrupt
                    yield {"event": "interrupt", "data": json.dumps({"type": "interrupt", "data": "Apakah Anda ingin melaksanakan query ini?"})}
                    
                    # Tunggu respon dari user
                    wait_count = 0
                    max_wait = 60  # 60 detik timeout
                    while session_id not in interrupt_status and wait_count < max_wait:
                        await asyncio.sleep(1)
                        wait_count += 1
                    
                    # Cek apakah ada respon
                    if session_id not in interrupt_status:
                        yield {"event": "error", "data": json.dumps({"type": "error", "data": "Timeout menunggu konfirmasi"})}
                        return
                    
                    # Jika user menyetujui, lanjutkan
                    if interrupt_status[session_id]:
                        for cont_step in graph.stream(None, config, stream_mode="updates"):
                            if "answer" in cont_step:
                                yield {"event": "message", "data": json.dumps({"type": "answer", "data": cont_step["answer"]})}
                    else:
                        yield {"event": "message", "data": json.dumps({"type": "answer", "data": "Operasi dibatalkan oleh pengguna"})}
                    
                    # Hapus status interrupt
                    del interrupt_status[session_id]
                            
                # Jika ada hasil pemrosesan normal
                elif "answer" in step:
                    yield {"event": "message", "data": json.dumps({"type": "answer", "data": step["answer"]})}
                # Jika ada hasil intermediate (misalnya hasil SQL)
                elif "result_query" in step:
                    yield {"event": "result", "data": json.dumps({"type": "result", "data": step["result_query"]})}
                # Debug - kirim semua step yang diterima
                else:
                    # Kirim konten step sebagai debug
                    yield {"event": "debug", "data": json.dumps({"type": "debug", "data": str(step)})}
            
            # Kirim pesan selesai
            yield {"event": "end", "data": json.dumps({"type": "info", "data": "Selesai memproses pertanyaan"})}
            
        except Exception as e:
            # Tangani error dan kirim sebagai event
            yield {"event": "error", "data": json.dumps({"type": "error", "data": str(e)})}
    
    return EventSourceResponse(generate_stream())

@app.post("/ask/{session_id}/interrupt")
async def handle_interrupt(session_id: str, response: InterruptResponse):
    """
    Menangani respon interrupt dari user
    
    Args:
        session_id: ID session chat
        response: Object dengan user_id dan approved
        
    Returns:
        Konfirmasi bahwa interrupt telah ditangani
    """
    # Validasi session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")
        
    # Validasi user_id match dengan session
    if active_sessions[session_id]["user_id"] != response.user_id:
        raise HTTPException(status_code=403, detail="User ID tidak sesuai dengan session")
    
    # Simpan status interrupt
    interrupt_status[session_id] = response.approved
    
    return {"status": "success", "approved": response.approved}

if __name__ == "__main__":
    import uvicorn
    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8000) 
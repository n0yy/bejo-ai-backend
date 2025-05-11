import unittest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

class TestAPI(unittest.TestCase):
    def test_create_session(self):
        """Test endpoint /ask untuk membuat session baru"""
        response = client.post("/ask", json={"user_id": "test_user"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("session_id", response.json())
        self.assertIsNotNone(response.json()["session_id"])
        
    def test_ask_question(self):
        """Test endpoint /ask/{session_id} untuk mengirim pertanyaan"""
        # Buat session dulu
        create_response = client.post("/ask", json={"user_id": "test_user"})
        session_id = create_response.json()["session_id"]
        
        # Kirim pertanyaan dengan session_id yang valid
        ask_response = client.post(
            f"/ask/{session_id}", 
            json={"user_id": "test_user", "question": "What is SQL?"}
        )
        self.assertEqual(ask_response.status_code, 200)
        
    def test_invalid_session(self):
        """Test mengirim pertanyaan dengan session_id yang tidak valid"""
        invalid_session_id = "invalid_session"
        response = client.post(
            f"/ask/{invalid_session_id}", 
            json={"user_id": "test_user", "question": "What is SQL?"}
        )
        self.assertEqual(response.status_code, 404)
        
    def test_invalid_user(self):
        """Test mengirim pertanyaan dengan user_id yang tidak cocok dengan session"""
        # Buat session dengan user_id tertentu
        create_response = client.post("/ask", json={"user_id": "test_user_1"})
        session_id = create_response.json()["session_id"]
        
        # Kirim pertanyaan dengan user_id yang berbeda
        ask_response = client.post(
            f"/ask/{session_id}", 
            json={"user_id": "test_user_2", "question": "What is SQL?"}
        )
        self.assertEqual(ask_response.status_code, 403)

if __name__ == "__main__":
    unittest.main() 
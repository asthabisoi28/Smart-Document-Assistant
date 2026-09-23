import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from unittest.mock import patch, MagicMock
from app.rag_service import classify_gemini_error, RAGService

def test_classify_gemini_error():
    print("==================================================")
    print("Testing Gemini Error Classification (Offline)")
    print("==================================================")

    # 1. Test 503 Service Unavailable / High Demand
    err_503 = Exception("503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}")
    cat_503, _ = classify_gemini_error(err_503)
    assert cat_503 == "service unavailable", f"Expected 'service unavailable', got '{cat_503}'"
    print(f"[OK] 503 Exception correctly classified as '{cat_503}'")

    # 2. Test 404 Model Not Found
    err_404 = Exception("404 Model gemini-invalid not found")
    cat_404, _ = classify_gemini_error(err_404)
    assert cat_404 == "model not available", f"Expected 'model not available', got '{cat_404}'"
    print(f"[OK] 404 Exception correctly classified as '{cat_404}'")

    # 3. Test 429 Quota Exceeded
    err_429 = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for quota metric")
    cat_429, _ = classify_gemini_error(err_429)
    assert cat_429 == "quota/rate limit", f"Expected 'quota/rate limit', got '{cat_429}'"
    print(f"[OK] 429 Exception correctly classified as '{cat_429}'")

    # 4. Test 401 Invalid Key
    err_401 = Exception("401 API_KEY_INVALID: Invalid API key provided")
    cat_401, _ = classify_gemini_error(err_401)
    assert cat_401 == "invalid API key", f"Expected 'invalid API key', got '{cat_401}'"
    print(f"[OK] 401 Exception correctly classified as '{cat_401}'")

    print("==================================================")
    print("ALL ERROR CLASSIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

def test_gemini_503_retry_behavior():
    print("==================================================")
    print("Testing Gemini 503 Retry Logic (Offline)")
    print("==================================================")

    rag = RAGService(vector_store=MagicMock(), embedding_service=MagicMock())

    # Case 1: 503 error on all attempts (1 initial + 2 retries = 3 attempts total)
    with patch("time.sleep", return_value=None) as mock_sleep, \
         patch("google.genai.Client") as mock_client_cls:
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE: High demand spike")

        answer, is_ans, err_msg = rag._call_gemini_llm("test question", "test context", "test-api-key")

        assert is_ans is False, "Expected is_answerable=False when all retries fail"
        assert mock_client.models.generate_content.call_count == 3, f"Expected exactly 3 calls (1 initial + 2 retries), got {mock_client.models.generate_content.call_count}"
        assert mock_sleep.call_count == 2, f"Expected 2 sleep delays between retries, got {mock_sleep.call_count}"
        assert "Gemini is temporarily unavailable due to high demand" in err_msg, f"Unexpected error message: {err_msg}"
        print("[OK] Case 1 passed: 503 retried exactly 2 times (3 total attempts), returns friendly 503 message on final failure.")

    # Case 2: 503 on first attempt, succeeds on 2nd attempt (1 retry)
    with patch("time.sleep", return_value=None) as mock_sleep, \
         patch("google.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        success_response = MagicMock()
        success_response.text = "This is a synthesized answer from the second attempt."
        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE: High demand spike"),
            success_response
        ]

        answer, is_ans, err_msg = rag._call_gemini_llm("test question", "test context", "test-api-key")

        assert is_ans is True
        assert answer == "This is a synthesized answer from the second attempt."
        assert err_msg is None
        assert mock_client.models.generate_content.call_count == 2, f"Expected 2 calls, got {mock_client.models.generate_content.call_count}"
        assert mock_sleep.call_count == 1, f"Expected 1 sleep delay, got {mock_sleep.call_count}"
        print("[OK] Case 2 passed: 503 succeeded on retry, returned synthesized answer.")

    # Case 3: Permanent error (404 Model Not Found) -> must NOT retry (only 1 attempt)
    with patch("time.sleep", return_value=None) as mock_sleep, \
         patch("google.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("404 Model not found")

        answer, is_ans, err_msg = rag._call_gemini_llm("test question", "test context", "test-api-key")

        assert is_ans is False
        assert mock_client.models.generate_content.call_count == 1, f"Expected only 1 call for 404, got {mock_client.models.generate_content.call_count}"
        assert mock_sleep.call_count == 0, "Sleep should not be called for non-retryable errors"
        assert "model is currently unavailable" in err_msg
        print("[OK] Case 3 passed: 404 permanent error was NOT retried (only 1 attempt).")

    # Case 4: Permanent error (401 Invalid Key) -> must NOT retry (only 1 attempt)
    with patch("time.sleep", return_value=None) as mock_sleep, \
         patch("google.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("401 API_KEY_INVALID")

        answer, is_ans, err_msg = rag._call_gemini_llm("test question", "test context", "test-api-key")

        assert is_ans is False
        assert mock_client.models.generate_content.call_count == 1, f"Expected only 1 call for 401, got {mock_client.models.generate_content.call_count}"
        assert mock_sleep.call_count == 0
        assert "API key is invalid" in err_msg
        print("[OK] Case 4 passed: 401 invalid API key error was NOT retried (only 1 attempt).")

    print("==================================================")
    print("ALL RETRY LOGIC TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_classify_gemini_error()
    test_gemini_503_retry_behavior()


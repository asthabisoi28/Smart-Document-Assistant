import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.rag_service import classify_gemini_error

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

if __name__ == "__main__":
    test_classify_gemini_error()

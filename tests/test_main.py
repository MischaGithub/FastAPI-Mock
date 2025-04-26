from fastapi.testclient import TestClient
from src.main import app

# Initialize test client
client = TestClient(app)

# Base valid payment data that will be resued across test
VALID_PAYMENT = {
    "amount": "15.99",
    "currency": "USD",
    "method": {"type": "card", "token": "tok_123"},
    "merchant_id": "merch_123"
}


# Test create payment
def test_create_payment():
    """
    Test successful payment creation:
    - Valid request should return 201 status
    - Response should contain payment_id and PROCESSING status
    """
    response = client.post("/payments", json=VALID_PAYMENT)
    
    # Verify HTTP status code
    assert response.status_code == 201
    
    # Parse response data
    data = response.json()
    
    # Verify required fields exist
    assert "payment_id" in data
    assert data["status"] == "PROCESSING"
    
    # Verify payment method matches input
    assert data["method"]["type"] == VALID_PAYMENT["method"]["type"]

# Test invalid currency
def test_invalid_currency():
    
    """ 
    Test currency validation:
    
    - Request with invalid currency should return 422
    - Error message should display support currencies
    """
    
    bad_payment = VALID_PAYMENT.copy()
    bad_payment["currency"] = "JPY"
    
    response = client.post("/payments", json=bad_payment)
    
    assert response.status_code == 422
    assert "Currency must be one USD, EUR, or GBP." in response.text
    
    error_detail = response.json()["detail"][0]
    
    assert error_detail["loc"] == ["body"]
    assert "USD, EUR, or GBP." in error_detail["msg"]
    
    error_detail = response.json()["detail"][0]
    assert error_detail["loc"] == ["body", "currency"]  # Error location
    assert "USD, EUR, or GBP" in error_detail["msg"]  # Error message
    

# Test minimum amount
def test_minimum_amount():
    """
    Test amount validation:
    - Amounts below $1.00 should be rejected
    - Should return 422 with appropriate error
    """
    bad_payment = VALID_PAYMENT.copy()
    bad_payment["amount"] = "0.99"  # Below minimum
    
    response = client.post("/payments", json=bad_payment)
    
    assert response.status_code == 422
    assert "Minimum amount is $1.00." in response.text


# Test idempotency 
def test_idempotency():
    
    """ Test idempotency behavior """
    
    header = {"idempotency-key": "test_key_123"}

    response1 = client.post("/payments", json=VALID_PAYMENT, headers=header)
    
    payment_id = response1.json()["payment_id"]
    
    response2 = client.post("/payments", json=VALID_PAYMENT, headers=header)
    
    assert response2.json()["payment_id"] == payment_id
    

# Test get payment
def test_get_payment():
    """
    Test payment retrieval:
    - Create payment then fetch it
    - Verify returned data matches created payment
    """
    # Create test payment
    create_res = client.post("/payments", json=VALID_PAYMENT)
    payment_id = create_res.json()["payment_id"]
    
    # Retrieve payment
    get_res = client.get(f"/payments/{payment_id}")
    
    # Verify successful retrieval
    assert get_res.status_code == 200
    
    # Verify payment ID matches
    assert get_res.json()["payment_id"] == payment_id
    
    # Verify amount matches original
    assert get_res.json()["amount"] == VALID_PAYMENT["amount"]
    

# Test get a payment that does not exists
def test_get_nonexistent_payment():
    """
    Test error handling for unknown payments:
    - Request for non-existent ID should return 404
    - Should include helpful error message
    """
    response = client.get("/payments/non_existent_123")
    
    # Verify not found status
    assert response.status_code == 404
    
    # Verify error message
    assert "Payment not found" in response.text
    
    
    
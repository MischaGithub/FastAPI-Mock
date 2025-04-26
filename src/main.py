from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, ConfigDict, field_validator, field_serializer
from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid

# Initialzie FastAPI app
app = FastAPI(title="Primer payments mock API.")

# In-memory storage dict to simulate a database
# Key: payment_id or idempotency key
# Value: payment_data in payment_db

payments_db = {}

# Data Model

# Create a Payment Method Model
class PaymentMethod(BaseModel):
    type: str       # The payment processer (e.g. "card", "paypal")
    token: str      # Secure token representing a payment method
    

# Create Payment Request Model
class PaymentRequest(BaseModel):
    amount: Decimal                 # Use Decimal for precise monetry calculations
    currency: str = "USD"           # Use Default currency but this would normally load from a config
    method: PaymentMethod   # Payment method information
    merchant_id: str               # Indetify the merchant
    
    
    # Validate both the currency and the amount
    @field_validator('currency')
    def validate_currency(cls, value):
        """
        Ensure that the currency is one of the supported currencies
        """
        
        support_currencies = ["USD", "EUR", "GBP"]
        if value not in support_currencies:
            raise ValueError("Currency must be one USD, EUR, or GBP.")  # Simplified message
        return value
    
    
    @field_serializer('amount')
    def validate_amount(cls, value):
        """ Ensure the amount meet the minimum requiresments  """
     
        
        # Check that the value of the amount
        if value < Decimal('1.00'):
            raise ValueError("Minimum amount is $1.00.")
        return value
    
# Create Payment Response Model
class PaymentResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)    # Allow arbitary type needed for Decimal support
    payment_id: str             # Unique identifier for the payment
    status: str                 # Current status of payment
    method: PaymentMethod       # Payment method details
    created_at: str             # Created iso-formatted stamp
    amount: Decimal             # Payment amount (kept as a decimal for this test)
    currency: str               # Currency code
    merchant_id: str            # Merchant identifier
    
    
    # Serialize the amount field 
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal, _info):
        """ Convert the Decimal to a string for JSON serialization """
        return str(value)
    

# --- API Endpoint ---

# Create a payment
@app.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment: PaymentRequest, 
    idempotency_key: Optional[str] = Header(None)
    ):
    
    """ Process a new payment with validation and idempotency support """
    
    # Check for an existing payment with the idempotency key
    if idempotency_key and idempotency_key in payments_db:
        return payments_db[idempotency_key]
    
    # Generate a unique ID for a new payment
    payment_id = f"pay_{uuid.uuid4().hex[:8]}"
    
    # Create the payment response object
    payment_data = PaymentResponse(
        payment_id=payment_id,
        status="PROCESSING",
        method=payment.method,
        created_at=datetime.now(timezone.utc).isoformat(),   # Current UTC time
        amount=payment.amount,
        currency=payment.currency,
        merchant_id=payment.merchant_id
        
    )
    
    # Store payment in memory (both ID and idempotency key if provided)
    payments_db[payment_id] = payment_data
    if idempotency_key:
        payments_db[idempotency_key] = payment_data
    
    
    return payment_data

# Get the payment 
@app.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str):
    
    """ Get the payment by ID """
    
    # Check if the payment exist in the database by payment_id
    if payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found.")
    
    return payments_db[payment_id]

        
    
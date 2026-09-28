"""
Realistic educational demo samples for ReviewMind hackathon demonstration.
Each sample illustrates a realistic vulnerability or anti-pattern,
along with the team memory standard and corrected implementation.
"""

from typing import Dict, List
from src.models import DemoSample

DEMO_SAMPLES: List[DemoSample] = [
    DemoSample(
        id="sql_injection",
        title="1. SQL Injection (String Concatenation in Query)",
        language="python",
        category="Security & Database",
        description=(
            "A query constructed by concatenating unsanitized user input directly into an SQL string, "
            "allowing malicious actors to execute arbitrary SQL commands."
        ),
        vulnerable_code='''def get_user_profile(request, db_connection):
    """Fetch user profile by user ID passed in request arguments."""
    user_id = request.args.get("id")
    
    # DANGEROUS: Constructing SQL using direct string concatenation with user input
    query = "SELECT id, username, email, role FROM users WHERE id = " + user_id
    
    cursor = db_connection.cursor()
    cursor.execute(query)
    return cursor.fetchone()
''',
        fixed_code='''def get_user_profile(request, db_connection):
    """Fetch user profile safely using parameterized queries."""
    user_id = request.args.get("id")
    if not user_id:
        return None
        
    # SECURE: Using parameterized queries ensures input is treated strictly as data
    query = "SELECT id, username, email, role FROM users WHERE id = %s"
    
    cursor = db_connection.cursor()
    cursor.execute(query, (user_id,))
    return cursor.fetchone()
''',
        expected_team_rule=(
            "Never construct SQL queries using string concatenation or f-strings with user input. "
            "Always use parameterized queries or the approved team ORM."
        ),
        why_it_matters=(
            "SQL injection allows attackers to bypass authentication, read or modify sensitive data, "
            "and in severe cases compromise the underlying operating system."
        ),
    ),
    DemoSample(
        id="raw_exception",
        title="2. Raw Exception Exposure (Information Disclosure)",
        language="python",
        category="Security & Error Handling",
        description=(
            "An API endpoint catching general exceptions and returning raw exception messages "
            "and internal stack traces directly in the HTTP JSON response."
        ),
        vulnerable_code='''from flask import Flask, request, jsonify
import traceback

app = Flask(__name__)

@app.route("/api/v1/process-payment", methods=["POST"])
def process_payment():
    try:
        payload = request.get_json()
        card_number = payload["card_number"]
        amount = float(payload["amount"])
        
        result = charge_customer_card(card_number, amount)
        return jsonify({"status": "success", "charge_id": result.id})
    except Exception as e:
        # DANGEROUS: Exposing raw exception strings and system stack trace to external callers
        return jsonify({
            "status": "error",
            "exception_type": str(type(e).__name__),
            "exception_details": str(e),
            "stack_trace": traceback.format_exc(),
            "received_payload": request.get_data(as_text=True)
        }), 500
''',
        fixed_code='''from flask import Flask, request, jsonify
import logging
import uuid

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route("/api/v1/process-payment", methods=["POST"])
def process_payment():
    correlation_id = str(uuid.uuid4())
    try:
        payload = request.get_json()
        card_number = payload.get("card_number")
        amount = float(payload.get("amount", 0))
        
        result = charge_customer_card(card_number, amount)
        return jsonify({"status": "success", "charge_id": result.id})
    except Exception as e:
        # SECURE: Log internal details securely on the server with correlation ID
        logger.error(f"Payment failed [ref={correlation_id}]: {str(e)}", exc_info=True)
        # Return sanitized, opaque error response to client
        return jsonify({
            "status": "error",
            "message": "Payment processing failed. Please contact support.",
            "error_reference": correlation_id
        }), 500
''',
        expected_team_rule=(
            "Never expose raw exception messages or stack traces in HTTP responses to client callers. "
            "Log internal errors securely and return sanitized error codes or friendly messages."
        ),
        why_it_matters=(
            "Exposing internal stack traces leaks sensitive architectural details, file paths, database schemas, "
            "third-party library versions, and even credit card / PII data to potential attackers."
        ),
    ),
    DemoSample(
        id="missing_validation",
        title="3. Missing Input Validation (Business Logic Vulnerability)",
        language="python",
        category="Data Integrity & Security",
        description=(
            "A funds transfer endpoint that directly accepts numerical amounts without validation, "
            "allowing negative numbers (siphoning funds backwards) and invalid account states."
        ),
        vulnerable_code='''def transfer_account_balance(db, from_account_id, to_account_id, amount):
    """Transfer money between two bank accounts."""
    # FLAW: Missing validation! 
    # Negative amount reverses transfer direction, letting attackers withdraw from destination!
    # No check whether from_account_id == to_account_id
    
    from_acc = db.get_account(from_account_id)
    to_acc = db.get_account(to_account_id)
    
    # Direct balance manipulation without bounds checking
    from_acc.balance -= amount
    to_acc.balance += amount
    
    db.save(from_acc)
    db.save(to_acc)
    return {"success": True, "transferred": amount}
''',
        fixed_code='''from decimal import Decimal
from typing import Dict, Any

def transfer_account_balance(db, from_account_id: str, to_account_id: str, amount_raw: Any) -> Dict[str, Any]:
    """Transfer money safely with strict input and business bounds validation."""
    try:
        amount = Decimal(str(amount_raw))
    except (ValueError, TypeError):
        raise ValueError("Invalid amount format. Must be a valid positive number.")
        
    # VALIDATION: Strict positive bounds and account validation
    if amount <= Decimal("0.00"):
        raise ValueError("Transfer amount must be strictly greater than zero.")
    if from_account_id == to_account_id:
        raise ValueError("Source and destination accounts cannot be identical.")
        
    with db.transaction():
        from_acc = db.get_account_for_update(from_account_id)
        to_acc = db.get_account_for_update(to_account_id)
        
        if from_acc.balance < amount:
            raise ValueError("Insufficient balance for transfer.")
            
        from_acc.balance -= amount
        to_acc.balance += amount
        db.save(from_acc)
        db.save(to_acc)
        
    return {"success": True, "transferred": str(amount)}
''',
        expected_team_rule=(
            "All public API endpoints and controller functions must validate and bounds-check all "
            "incoming parameters before passing data to service or persistence layers."
        ),
        why_it_matters=(
            "Missing input validation leads to financial vulnerabilities, data corruption, "
            "buffer overflows, and unexpected application state mutations."
        ),
    ),
    DemoSample(
        id="controller_business_logic",
        title="4. Business Logic in Controller (Architectural Violation)",
        language="python",
        category="Architecture & Maintainability",
        description=(
            "An HTTP controller function embedding business domain logic, pricing algorithms, "
            "discount tier rules, and direct database queries/commits instead of utilizing a service layer."
        ),
        vulnerable_code='''from flask import Blueprint, request, jsonify
from models import db, CartItem, Product, Order, User

checkout_bp = Blueprint("checkout", __name__)

@checkout_bp.route("/checkout", methods=["POST"])
def checkout():
    # ARCHITECTURAL ANTI-PATTERN: Business calculations, pricing tiers, and
    # direct database persistence embedded directly inside HTTP controller!
    user_id = request.json.get("user_id")
    user = User.query.get(user_id)
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    subtotal = 0.0
    for item in cart_items:
        prod = Product.query.get(item.product_id)
        unit_price = prod.price
        
        # Embedded business pricing rules
        if user.tier == "VIP":
            unit_price *= 0.80
        elif user.tier == "REGULAR":
            unit_price *= 0.95
            
        subtotal += unit_price * item.quantity
        
    tax = subtotal * 0.0825
    grand_total = subtotal + tax
    
    # Direct database mutation and commit in controller
    order = Order(user_id=user.id, subtotal=subtotal, tax=tax, total=grand_total)
    db.session.add(order)
    db.session.commit()
    
    return jsonify({"order_id": order.id, "total": grand_total})
''',
        fixed_code='''from flask import Blueprint, request, jsonify
from services.order_service import OrderService
from dtos.checkout_request import CheckoutRequestDTO

checkout_bp = Blueprint("checkout", __name__)
order_service = OrderService()

@checkout_bp.route("/checkout", methods=["POST"])
def checkout():
    # CLEAN ARCHITECTURE: Controller only validates request, delegates domain logic
    # to domain service, and returns formatted HTTP response.
    dto = CheckoutRequestDTO.from_dict(request.get_json())
    order_result = order_service.process_checkout(user_id=dto.user_id)
    return jsonify(order_result.to_dict()), 201
''',
        expected_team_rule=(
            "Keep business logic out of controllers and HTTP route handlers. Controllers should only "
            "validate inputs, invoke domain services, and return responses. Use a dedicated service layer."
        ),
        why_it_matters=(
            "Embedding business logic into controllers prevents code reuse across CLI/jobs/webhooks, "
            "makes unit testing painful, couples web framework with business rules, and leads to maintenance nightmares."
        ),
    ),
]

SAMPLES_BY_ID: Dict[str, DemoSample] = {sample.id: sample for sample in DEMO_SAMPLES}


def get_sample_by_id(sample_id: str) -> DemoSample:
    """Retrieve demo sample by identifier."""
    return SAMPLES_BY_ID.get(sample_id, DEMO_SAMPLES[0])

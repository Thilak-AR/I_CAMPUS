from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from flask_jwt_extended import get_jwt_identity
from auth_utils import role_required
import datetime, random

finance_bp = Blueprint("finance_bp", __name__)

# ---------------------------------------------------------------
# 1️⃣  View Student Fee Bills
# ---------------------------------------------------------------
@finance_bp.route("/finance/bills", methods=["GET"])
@role_required(["student", "accounts", "admin"])
def get_student_bills():
    token = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT B.BillID, F.ComponentName, B.Description, B.Amount, B.Status, B.BillDate, B.DueDate
        FROM StudentBills B
        JOIN FeeComponents F ON B.ComponentID = F.ComponentID
        WHERE B.TokenNumber = ?
        ORDER BY B.BillDate DESC
    """, (token,))
    rows = cursor.fetchall()
    conn.close()

    bills = [{
        "bill_id": r[0],
        "component": r[1],
        "description": r[2],
        "amount": float(r[3]),
        "status": r[4],
        "bill_date": str(r[5]),
        "due_date": str(r[6]) if r[6] else None
    } for r in rows]
    return jsonify({"status": "success", "bills": bills})


# ---------------------------------------------------------------
# 2️⃣  Create Manual Bill (Accounts / Admin)
# ---------------------------------------------------------------
@finance_bp.route("/finance/bill/create", methods=["POST"])
@role_required(["accounts", "admin"])
def create_bill():
    data = request.json
    token = data.get("token_number")
    component_id = data.get("component_id")
    description = data.get("description")
    amount = data.get("amount")
    due_date = data.get("due_date")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO StudentBills (TokenNumber, ComponentID, Description, Amount, DueDate, Status, AddedBy, SourceModule)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?, 'Manual')
    """, (token, component_id, description, amount, due_date, get_jwt_identity()))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Bill created successfully"})


# ---------------------------------------------------------------
# 3️⃣  Simulated Payment (Student pays manually or online)
# ---------------------------------------------------------------
@finance_bp.route("/finance/pay", methods=["POST"])
@role_required(["student"])
def make_payment():
    data = request.json
    token = get_jwt_identity()
    bills = data.get("bills", [])
    total = data.get("total_amount")
    payment_mode = data.get("mode", "UPI")

    # Simulate transaction
    txn_id = f"TXN{random.randint(100000,999999)}"
    payment_date = datetime.datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert payment record
    cursor.execute("""
        INSERT INTO Payments (TokenNumber, TotalAmount, PaymentMode, TransactionID, PaymentStatus, PaymentDate)
        VALUES (?, ?, ?, ?, 'Success', ?)
    """, (token, total, payment_mode, txn_id, payment_date))
    payment_id = cursor.execute("SELECT @@IDENTITY").fetchval()

    # Link to bills
    for b in bills:
        cursor.execute("""
            INSERT INTO PaymentDetails (PaymentID, BillID, AmountPaid)
            VALUES (?, ?, ?)
        """, (payment_id, b["bill_id"], b["amount"]))
        cursor.execute("UPDATE StudentBills SET Status='Paid' WHERE BillID=?", (b["bill_id"],))
        cursor.execute("""
            INSERT INTO StudentLedger (TokenNumber, TransactionType, Description, Amount, LinkedPaymentID, LinkedBillID)
            VALUES (?, 'Credit', 'Fee Payment', ?, ?, ?)
        """, (token, b["amount"], payment_id, b["bill_id"]))

    # Generate receipt
    receipt_no = f"RCT{datetime.datetime.now().strftime('%y%m%d')}{random.randint(100,999)}"
    cursor.execute("""
        INSERT INTO Receipts (PaymentID, ReceiptNumber, GeneratedBy)
        VALUES (?, ?, ?)
    """, (payment_id, receipt_no, token))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Payment processed successfully",
        "transaction_id": txn_id,
        "receipt_number": receipt_no
    })


# ---------------------------------------------------------------
# 4️⃣  View Payment History
# ---------------------------------------------------------------
@finance_bp.route("/finance/payments", methods=["GET"])
@role_required(["student", "accounts"])
def get_payments():
    token = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT PaymentID, TotalAmount, PaymentMode, TransactionID, PaymentStatus, PaymentDate
        FROM Payments WHERE TokenNumber=? ORDER BY PaymentDate DESC
    """, (token,))
    rows = cursor.fetchall()
    conn.close()

    payments = [{
        "payment_id": r[0],
        "amount": float(r[1]),
        "mode": r[2],
        "transaction_id": r[3],
        "status": r[4],
        "date": str(r[5])
    } for r in rows]

    return jsonify({"status": "success", "payments": payments})


# ---------------------------------------------------------------
# 5️⃣  Get Student Ledger
# ---------------------------------------------------------------
@finance_bp.route("/finance/ledger", methods=["GET"])
@role_required(["student", "accounts"])
def get_ledger():
    token = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TransactionType, Description, Amount, TransactionDate
        FROM StudentLedger
        WHERE TokenNumber=?
        ORDER BY TransactionDate DESC
    """, (token,))
    rows = cursor.fetchall()
    conn.close()

    ledger = [{
        "type": r[0],
        "description": r[1],
        "amount": float(r[2]),
        "date": str(r[3])
    } for r in rows]

    return jsonify({"status": "success", "ledger": ledger})

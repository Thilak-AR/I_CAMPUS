from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

library_bp = Blueprint('library_bp', __name__)

# ==============================================================
# 📚 LIBRARY MODULE
# ==============================================================

# 1️⃣ Add new book
@library_bp.route('/library/book/add', methods=['POST'])
@role_required(["admin", "librarian"])
def add_book():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LibraryBooks (ISBN, Title, Author, Publisher, Edition, Category, Quantity, Available)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("isbn"), data.get("title"), data.get("author"), data.get("publisher"),
        data.get("edition"), data.get("category"), data.get("quantity"), data.get("quantity")
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Book added successfully"}), 201


# 2️⃣ View all books
@library_bp.route('/library/books', methods=['GET'])
@role_required(["admin", "librarian", "student"])
def list_books():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT BookID, ISBN, Title, Author, Category, Available FROM LibraryBooks")
    rows = cursor.fetchall()
    conn.close()
    books = [{
        "book_id": r[0],
        "isbn": r[1],
        "title": r[2],
        "author": r[3],
        "category": r[4],
        "available": r[5]
    } for r in rows]
    return jsonify({"status": "success", "books": books})


# 3️⃣ Issue a book to student
@library_bp.route('/library/book/issue', methods=['POST'])
@role_required(["librarian", "admin"])
def issue_book():
    data = request.json
    token = data.get("token_number")
    book_id = data.get("book_id")
    due_days = int(data.get("due_days", 7))
    due_date = (datetime.date.today() + datetime.timedelta(days=due_days))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check availability
    cursor.execute("SELECT Available FROM LibraryBooks WHERE BookID=?", (book_id,))
    row = cursor.fetchone()
    if not row or row[0] <= 0:
        conn.close()
        return jsonify({"status": "error", "message": "Book not available"}), 400

    # Issue book
    cursor.execute("""
        INSERT INTO BookTransactions (BookID, TokenNumber, DueDate, Status)
        VALUES (?, ?, ?, 'Issued')
    """, (book_id, token, due_date))
    cursor.execute("UPDATE LibraryBooks SET Available = Available - 1 WHERE BookID=?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Book issued successfully", "due_date": str(due_date)}), 201


# 4️⃣ Return book and calculate fine if overdue
@library_bp.route('/library/book/return', methods=['POST'])
@role_required(["librarian", "admin"])
def return_book():
    data = request.json
    transaction_id = data.get("transaction_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT BookID, DueDate FROM BookTransactions
        WHERE TransactionID=? AND Status='Issued'
    """, (transaction_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Transaction not found or already returned"}), 404

    book_id, due_date = row
    today = datetime.date.today()
    fine = 0
    if today > due_date:
        fine = (today - due_date).days * 5  # ₹5 per day fine

    cursor.execute("""
        UPDATE BookTransactions
        SET ReturnDate=?, FineAmount=?, Status='Returned'
        WHERE TransactionID=?
    """, (today, fine, transaction_id))

    cursor.execute("UPDATE LibraryBooks SET Available = Available + 1 WHERE BookID=?", (book_id,))

    # Record fine if any
    if fine > 0:
        cursor.execute("""
            INSERT INTO LibraryFines (TokenNumber, TransactionID, FineAmount, Reason)
            SELECT TokenNumber, TransactionID, ?, 'Late Return'
            FROM BookTransactions WHERE TransactionID=?
        """, (fine, transaction_id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Book returned successfully",
        "fine_amount": fine
    }), 200


# 5️⃣ View borrowed books by a student
@library_bp.route('/library/student/<string:token>/books', methods=['GET'])
@role_required(["student", "librarian", "admin"])
def student_books(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT BT.TransactionID, L.Title, BT.IssueDate, BT.DueDate, BT.ReturnDate, BT.Status, BT.FineAmount
        FROM BookTransactions BT
        JOIN LibraryBooks L ON BT.BookID = L.BookID
        WHERE BT.TokenNumber=?
        ORDER BY BT.IssueDate DESC
    """, (token,))
    rows = cursor.fetchall()
    conn.close()

    transactions = [{
        "transaction_id": r[0],
        "book_title": r[1],
        "issue_date": str(r[2]),
        "due_date": str(r[3]),
        "return_date": str(r[4]) if r[4] else None,
        "status": r[5],
        "fine": float(r[6])
    } for r in rows]

    return jsonify({"status": "success", "transactions": transactions})


# 6️⃣ Mark fine as paid
@library_bp.route('/library/fine/pay', methods=['POST'])
@role_required(["librarian", "admin"])
def pay_fine():
    data = request.json
    fine_id = data.get("fine_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE LibraryFines SET PaidStatus='Paid', PaidOn=GETDATE() WHERE FineID=?
    """, (fine_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Fine marked as paid"}), 200


# ==============================================================
# 🧰 INVENTORY MODULE
# ==============================================================

# 7️⃣ Add item to inventory
@library_bp.route('/inventory/add', methods=['POST'])
@role_required(["admin", "librarian", "lab_incharge"])
def add_item():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO InventoryItems (ItemName, Category, Quantity, Location, Status)
        VALUES (?, ?, ?, ?, 'Available')
    """, (
        data.get("item_name"), data.get("category"),
        data.get("quantity"), data.get("location")
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Item added successfully"}), 201


# 8️⃣ Issue / return inventory item
@library_bp.route('/inventory/transaction', methods=['POST'])
@role_required(["lab_incharge", "librarian", "admin"])
def inventory_transaction():
    data = request.json
    action = data.get("action")  # Issued / Returned / Damaged
    item_id = data.get("item_id")
    token = data.get("token_number")
    qty = int(data.get("quantity", 1))
    remarks = data.get("remarks", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Record transaction
    cursor.execute("""
        INSERT INTO InventoryTransactions (ItemID, TokenNumber, Action, Quantity, Remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (item_id, token, action, qty, remarks))

    # Update quantity
    if action == "Issued":
        cursor.execute("UPDATE InventoryItems SET Quantity = Quantity - ?, Status='In Use' WHERE ItemID=?", (qty, item_id))
    elif action == "Returned":
        cursor.execute("UPDATE InventoryItems SET Quantity = Quantity + ?, Status='Available' WHERE ItemID=?", (qty, item_id))
    elif action == "Damaged":
        cursor.execute("UPDATE InventoryItems SET Quantity = Quantity - ? WHERE ItemID=?", (qty, item_id))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Item {action.lower()} recorded"}), 201


# 9️⃣ View all inventory items
@library_bp.route('/inventory/items', methods=['GET'])
@role_required(["admin", "librarian", "lab_incharge", "student"])
def list_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ItemID, ItemName, Category, Quantity, Location, Status FROM InventoryItems")
    rows = cursor.fetchall()
    conn.close()
    items = [{
        "item_id": r[0],
        "name": r[1],
        "category": r[2],
        "quantity": r[3],
        "location": r[4],
        "status": r[5]
    } for r in rows]
    return jsonify({"status": "success", "items": items})

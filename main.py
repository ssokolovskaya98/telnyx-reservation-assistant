# main.py
from fastapi import FastAPI, HTTPException, Request
import psycopg2
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env")

def get_conn():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

# ----------------------------
# Business Logic
# ----------------------------
def search_availability(params: dict):
    """Find available restaurants by cuisine, date, time, and party size."""
    cuisine = params.get("cuisine")
    party_size = params.get("party_size")
    date = params.get("date")   # format: '2025-09-24'
    time = params.get("time")   # format: '19:00:00'

    query = """
        SELECT a.availability_id,
               r.restaurant_id,
               r.restaurant,
               r.city,
               r.cuisine,
               r.price,
               a.date,
               a.time,
               a.available_seats
        FROM availability a
        JOIN restaurants r ON a.restaurant_id = r.restaurant_id
        WHERE (%s IS NULL OR r.cuisine ILIKE %s)
          AND a.available_seats >= %s
          AND a.date = %s
          AND a.time = %s
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (cuisine, cuisine, party_size, date, time))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

    return [dict(zip(cols, row)) for row in rows]

def create_reservation(params: dict):
    """Book a reservation and decrement available seats."""
    restaurant_id = params["restaurant_id"]
    availability_id = params["availability_id"]
    user_name = params["user_name"]
    party_size = params["party_size"]
    date = params["date"]
    time = params["time"]

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Check availability
            cur.execute("SELECT available_seats FROM availability WHERE availability_id=%s FOR UPDATE", (availability_id,))
            avail = cur.fetchone()
            if not avail or avail[0] < party_size:
                raise HTTPException(status_code=400, detail="Not enough seats available")

            # Insert reservation
            cur.execute(
                """
                INSERT INTO reservations (restaurant_id, user_name, reservation_date, reservation_time, party_size)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reservation_id
                """,
                (restaurant_id, user_name, date, time, party_size)
            )
            reservation_id = cur.fetchone()[0]

            # Update availability
            cur.execute(
                "UPDATE availability SET available_seats = available_seats - %s WHERE availability_id=%s",
                (party_size, availability_id)
            )

    return {"reservation_id": reservation_id, "message": "Reservation confirmed!"}

def cancel_reservation(params: dict):
    """Cancel a reservation and restore available seats."""
    reservation_id = params["reservation_id"]

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Look up reservation
            cur.execute("SELECT * FROM reservations WHERE reservation_id=%s FOR UPDATE", (reservation_id,))
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Reservation not found")

            colnames = [desc[0] for desc in cur.description]
            rowdict = dict(zip(colnames, res))

            # Delete the reservation (since your schema has no status column)
            cur.execute("DELETE FROM reservations WHERE reservation_id=%s", (reservation_id,))

            # Restore seats in availability
            cur.execute(
                """
                UPDATE availability
                SET available_seats = available_seats + %s
                WHERE restaurant_id=%s AND date=%s AND time=%s
                """,
                (rowdict["party_size"], rowdict["restaurant_id"], rowdict["reservation_date"], rowdict["reservation_time"])
            )

    return {"message": "Reservation cancelled"}

# ----------------------------
# REST Endpoints (testing)
# ----------------------------
@app.post("/search")
def search_endpoint(params: dict):
    return search_availability(params)

@app.post("/reserve")
def reserve_endpoint(params: dict):
    return create_reservation(params)

@app.post("/cancel")
def cancel_endpoint(params: dict):
    return cancel_reservation(params)

# ----------------------------
# MCP Endpoint (for Telnyx)
# ----------------------------

@app.post("/mcp")
async def mcp_handler(req: Request):
    try:
        body = await req.json()
    except Exception:
        # Return empty JSON-RPC response if request isn’t proper
        return {"jsonrpc": "2.0", "id": None, "error": {"message": "Invalid JSON"}}

    method = body.get("method")
    params = body.get("params") or {}
    rpc_id = body.get("id")

    try:
        if method == "search_availability":
            result = search_availability(params)
        elif method == "create_reservation":
            result = create_reservation(params)
        elif method == "cancel_reservation":
            result = cancel_reservation(params)
        else:
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"message": "Unknown method"}}

        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}
    
    except Exception as e:
        return {"jsonrpc": "2.0", "id": rpc_id, "error": {"message": str(e)}}

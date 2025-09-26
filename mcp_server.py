from fastapi import FastAPI, HTTPException, Request
from mcp.server.fastmcp import FastMCP
import psycopg2
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from typing import Any

# Load environment variables
load_dotenv(".env")

# Initialize FastAPI and MCP server
app = FastAPI()
mcp = FastMCP("restaurant_reservation")

# Database connection function
def get_conn():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

# Helper function to fetch all restaurants
async def get_all_restaurants() -> list[dict[str, Any]]:
    query = "SELECT restaurant_id, restaurant, city, cuisine FROM restaurants"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in rows]

# Define MCP tools
@mcp.tool("list_restaurants")
async def list_restaurants() -> list[dict[str, Any]]:
    """Retrieve all restaurants."""
    return await get_all_restaurants()

@mcp.tool("check_availability")
async def check_availability(cuisine: str, party_size: int, date: str, time: str) -> list[dict[str, Any]]:
    """Check availability for a given cuisine, party size, date, and time."""
    query = """
        SELECT a.availability_id, r.restaurant_id, r.restaurant, r.city, r.cuisine, r.price, a.date, a.time, a.available_seats
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

@mcp.tool("book_reservation")
async def book_reservation(restaurant_id: int, availability_id: int, user_name: str, party_size: int, date: str, time: str) -> dict[str, Any]:
    """Book a reservation and decrement available seats."""
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

@mcp.tool("cancel_reservation")
async def cancel_reservation(reservation_id: int) -> dict[str, Any]:
    """Cancel a reservation and restore available seats."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Look up reservation
            cur.execute("SELECT * FROM reservations WHERE reservation_id=%s FOR UPDATE", (reservation_id,))
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Reservation not found")

            colnames = [desc[0] for desc in cur.description]
            rowdict = dict(zip(colnames, res))

            # Delete the reservation
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

# Define MCP resources
@mcp.resource("restaurant_schema")
async def restaurant_schema() -> dict[str, Any]:
    """Provide schema for restaurant data."""
    return {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "integer"},
            "restaurant": {"type": "string"},
            "city": {"type": "string"},
            "cuisine": {"type": "string"},
            "price": {"type": "string"}
        },
        "required": ["restaurant_id", "restaurant", "city", "cuisine"]
    }

# Define MCP prompts
@mcp.prompt("book_reservation_prompt")
async def book_reservation_prompt() -> dict[str, Any]:
    """Provide a prompt template for booking a reservation."""
    return {
        "template": "Book a reservation at {restaurant} for {party_size} people on {date} at {time}.",
        "inputs": ["restaurant", "party_size", "date", "time"]
    }

# Start the MCP server
if __name__ == "__main__":
    mcp.run()


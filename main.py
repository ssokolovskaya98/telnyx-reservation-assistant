from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel
from datetime import date, time

app = FastAPI()

from dotenv import load_dotenv
import os

load_dotenv(".env")

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

# ---- Models for booking/canceling ----
class Booking(BaseModel):
    restaurant_id: int
    user_name: str
    reservation_date: date
    reservation_time: time

class CancelReservation(BaseModel):
    reservation_id: int

# ---- Endpoints ----
@app.get("/restaurants")
def get_restaurants():
    cur.execute("SELECT restaurant_id, price, cancellation_fee FROM public.restaurants;")
    rows = cur.fetchall()
    return [{"restaurant_id": r[0], "price": r[1], "cancellation_fee": r[2]} for r in rows]

from typing import Optional
from datetime import date, time

@app.get("/availability")
def get_availability(
    restaurant_id: Optional[int] = None,
    restaurant_name: Optional[str] = None,
    cuisine: Optional[str] = None,
    res_date: Optional[date] = None,
    res_time: Optional[time] = None,
    party_size: Optional[int] = None
):
    """
    Flexible availability search:
    - Can filter by restaurant_id, name, cuisine
    - Can filter by date, time
    - Returns all available slots if no filters are provided
    """

    # Base query
    query = """
        SELECT a.restaurant_id, r.restaurant, r.cuisine, a.date, a.time
        FROM public.availability a
        JOIN public.restaurants r ON a.restaurant_id = r.restaurant_id
        WHERE a.is_available = TRUE
    """
    params = []

    # Add optional filters
    if restaurant_id:
        query += " AND a.restaurant_id = %s"
        params.append(restaurant_id)
    if restaurant_name:
        query += " AND r.restaurant = %s"
        params.append(restaurant_name)
    if cuisine:
        query += " AND r.cuisine = %s"
        params.append(cuisine)
    if res_date:
        query += " AND a.date = %s"
        params.append(res_date)
    if res_time:
        query += " AND a.time = %s"
        params.append(res_time)

    # You could filter party_size here if you have a capacity column in restaurants

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    # Return structured response
    return [
        {
            "restaurant_id": r[0],
            "restaurant": r[1],
            "cuisine": r[2],
            "date": r[3],
            "time": r[4]
        }
        for r in rows
    ]

@app.post("/book")
def book_reservation(booking: Booking):
    # Check availability first
    cur.execute(
        """
        SELECT is_available FROM public.availability
        WHERE restaurant_id = %s AND date = %s AND time = %s;
        """,
        (booking.restaurant_id, booking.reservation_date, booking.reservation_time)
    )
    result = cur.fetchone()
    if not result or result[0] is False:
        raise HTTPException(status_code=400, detail="Slot not available")

    # Insert reservation
    cur.execute(
        """
        INSERT INTO public.reservations (restaurant_id, user_name, reservation_date, reservation_time)
        VALUES (%s, %s, %s, %s)
        RETURNING reservation_id;
        """,
        (booking.restaurant_id, booking.user_name, booking.reservation_date, booking.reservation_time)
    )
    reservation_id = cur.fetchone()[0]

    # Update availability
    cur.execute(
        """
        UPDATE public.availability
        SET is_available = FALSE
        WHERE restaurant_id = %s AND date = %s AND time = %s;
        """,
        (booking.restaurant_id, booking.reservation_date, booking.reservation_time)
    )

    conn.commit()
    return {"message": "Reservation booked", "reservation_id": reservation_id}

@app.post("/cancel")
def cancel_reservation(cancel: CancelReservation):
    # Get reservation info
    cur.execute(
        "SELECT restaurant_id, reservation_date, reservation_time FROM public.reservations WHERE reservation_id = %s;",
        (cancel.reservation_id,)
    )
    res = cur.fetchone()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")

    restaurant_id, res_date, res_time = res

    # Delete reservation
    cur.execute(
        "DELETE FROM public.reservations WHERE reservation_id = %s;",
        (cancel.reservation_id,)
    )

    # Make slot available again
    cur.execute(
        "UPDATE public.availability SET is_available = TRUE WHERE restaurant_id = %s AND date = %s AND time = %s;",
        (restaurant_id, res_date, res_time)
    )

    conn.commit()
    return {"message": "Reservation canceled successfully"}


# Last Minute Restaurant Booking Assistant

An AI-powered voice assistant that helps you find and book **last-minute restaurant reservations** over the phone.  
Built with **FastAPI** + **Telnyx Voice AI** + **Model Context Protocol (MCP)** + **Render** + **PostgreSQL**

This project demonstrates how to integrate conversational AI with real-time APIs and external services to solve a real-world problem:  
> “I need an Italian restaurant in Boston for 6 people at 6 PM, can you tell me where I can make a reservation?”

---

## Features
- **Check Availability**: Query restaurants by city, cuisine type, party size, time, and price range.  
- **Book Reservations**: Reserve a table and receive a confirmation ID.  
- **Cancel Reservations**: Cancel by reservation ID and free up the slot.  
- **Price Filtering**: Support for `$` = cheap, `$$` = moderate, `$$$` = expensive, `$$$$` = very expensive.  
- **Voice-First Experience**: Integrated with **Telnyx AI Assistant** so users can call a phone number and interact naturally.  
- **Dynamic Webhooks**: Personalize responses and track reservations with user context.

---

## Architecture Overview

*Database: PostgreSQL on Render with three core tables:

  1.restaurants – restaurant info
  2. availability – date/time slots
  3. reservations – customer bookings

*Backend (FastAPI):

  *Exposes REST APIs for availability, booking, and cancellation
  *Implements an MCP server for Telnyx Assistant integration

*Telnyx Assistant:

  *Connected to MCP server via webhook
  *Configured with dynamic variables, instructions, and a chosen voice
  *Linked to a purchased phone number for real world calling

## Setup Instructions (Try it Yourself)

### Database Setup

1. Create a PostgreSQL instance on Render (or any Postgres host).

2. Connect the DB to pgAdmin (or your preferred SQL client).

3. Create the following tables:

```
  CREATE TABLE restaurants (
  restaurant_id SERIAL PRIMARY KEY,
  restaurant VARCHAR(255),
  city VARCHAR(100),
  cuisine VARCHAR(100),
  description TEXT,
  price VARCHAR(10),
  cancellation_fee NUMERIC
);
```

```
CREATE TABLE availability (
  availability_id SERIAL PRIMARY KEY,
  restaurant_id INT REFERENCES restaurants(restaurant_id),
  date DATE,
  time TIME,
  is_available BOOLEAN,
  available_seats INT
);
```

```
CREATE TABLE reservations (
  reservation_id SERIAL PRIMARY KEY,
  restaurant_id INT REFERENCES restaurants(restaurant_id),
  user_name VARCHAR(255),
  reservation_date DATE,
  reservation_time TIME,
  party_size INT
);
```

4. Import the restaurants.csv and availability.csv to their respective tables

### Backend (FastAPI + MCP)

1. Clone this repo:

```
git clone https://github.com/ssokolovskaya98/telnyx-reservation-assistant.git
cd telnyx-reservation-assistant
```

2. Create and activate a virtual environment:
   
```
python -m venv venv
source venv/bin/activate #(Mac)
```

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Add a .env file with the following details: (Make sure to add this to your .gitignore file)

```
DB_NAME=xxx
DB_USER=xxx
DB_PASSWORD=xxx
DB_HOST=xxx
DB_PORT=xxx
X-API-KEY=xxx
```

5. Run the FastAPI app locally:

```
uvicorn main:app --reload
```

### Deployment on Render

1. Push code to GitHub.

2. Create a Web Service on Render, connect it to your repo.

3. Set environment variables (DB_NAME, DB_USER, etc) in the Render dashboard.

4. Deploy and confirm your app is live at https://<your-service>.onrender.com/mcp.

### Telnyx AI Assistant Setup

1. Create an AI Assistant in the Telnyx Portal.

   - Choose an LLM for your assistant
   - Add in instructions to guide your model in conversations
   - connect your MCP Server URL and dynamic webhook URL
   - Customize your voice
   
2. Purchase a Telnyx phone number and link it to your Assistant.

3. Call the number and test booking, checking availability, and cancellations.

## Demo Flow

1. User calls the Assistant’s number.
2. AI asks: “Hi, I can help you with last minute reservations, would you like to see availability and book a reservation?”
3. User provides details (i.e. cuisine type, preferred time, party size)
4. If available, reservation is created; if not, alternatives are offered.
5. User can also cancel a reservation by providing their name and time.

## End to End Development Flow

1. PostgreSQL DB created on Render and connected via pgAdmin.
2. Tables created for restaurants, availability, reservations.
3. Populated with real + mock data.
4. FastAPI backend built with endpoints + MCP integration.
5. App deployed on Render.
6. Telnyx Assistant created, connected to MCP server, configured with dynamic variables and voice.
7. Phone number purchased + linked to the assistant.
8. Testing

---

## Backend Architecture

WILL ADD IN

## Future Improvements

- Integrate with real restaurant APIs (e.g., Yelp, OpenTable).
- Expand to more cities and cuisines.
- Add SMS confirmations with Telnyx Messaging API.
- Consider other user wants/needs: Parking? Closet public transportation stop? Cancellation fees? Location/Neighborhood of restaurant?

## Developer

Sharon Sokolovskaya 

Built for Telnyx Code Challenge 2025


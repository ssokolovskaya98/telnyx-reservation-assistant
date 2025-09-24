# Last Minute Restaurant Booking Assistant

An AI-powered voice assistant that helps you find and book **last-minute restaurant reservations** over the phone.  
Built with **FastAPI** + **Telnyx Voice AI** + **Model Context Protocol (MCP)** + **Render**

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

## Technology Stack

- FASTAPI
- Telnyx
- Render
- PostgreSQL
- PgAdmin

---

## Set Up Instructions

WILL ADD IN

## Telnyx AI Assistant Set Up

WILL ADD IN

## Future Improvements

- Replace mock database with Postgres (or other DB).
- Add authentication for Telnyx webhooks.
- Integrate with real restaurant APIs (e.g., Yelp, OpenTable).
- Expand to more cities and cuisines.
- Add SMS confirmations with Telnyx Messaging API.

## Developer

Sharon Sokolovskaya 

Built for Telnyx Code Challenge 2025


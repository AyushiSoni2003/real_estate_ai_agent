# Postman Test Collection

Import the file [realtyiq-api.postman_collection.json](realtyiq-api.postman_collection.json) into Postman.

## Setup

1. Start the backend server:
   - `cd backend`
   - `python -m uvicorn app.main:app --reload`
2. In Postman, import the collection.
3. Update the `baseUrl` variable if needed.
4. Run the **Signup** request first to create the first user account.
5. Then run **Login** to get a JWT token.
6. Copy the token into the `accessToken` variable.
7. Create a lead, then use the returned `leadId` in the message and follow-up requests.

## Notes

- The WhatsApp test uses the endpoint under `/api/v1/messages/`.
- The follow-up endpoints are under `/api/v1/follow-ups/`.
- If your auth login payload differs, update the request body accordingly.

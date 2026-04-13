# Auth Service

Central Authentication Service for AI Evaluation Tool.

## Features

- User authentication with JWT tokens
- Refresh token support
- Role-based access control
- HTTP-only cookie support (configurable)

## API Endpoints

### POST /login
Authenticate user and return JWT tokens.

**Request Body:**
```json
{
  "user_name": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user_name": "string",
  "role": "string"
}
```

### POST /refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

### POST /logout
Revoke refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

## Environment Variables

- `AUTH_SECRET_KEY`: Secret key for JWT access tokens
- `AUTH_REFRESH_SECRET_KEY`: Secret key for JWT refresh tokens
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name

## Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AUTH_SECRET_KEY="your-secret-key"
export DB_HOST="localhost"
export DB_USER="root"
export DB_PASSWORD="your-password"

# Run the service
./run.sh
```

The service runs on port 8001 by default.
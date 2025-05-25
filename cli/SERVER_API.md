# PyBitcask Server API

A REST API server for PyBitcask key-value store providing CRUD operations via HTTP endpoints.

## Overview

The PyBitcask server provides a **data-only REST API** for performing CRUD operations. Administrative functions like mode switching, configuration management, and server lifecycle are handled exclusively through the CLI.

### 🌐 **Server Capabilities**
- ✅ **Create**: Store key-value pairs
- ✅ **Read**: Retrieve values by key
- ✅ **Update**: Modify existing values
- ✅ **Delete**: Remove key-value pairs
- ✅ **List**: Get all keys
- ✅ **Clear**: Remove all data
- ✅ **Batch**: Multiple operations in one request

### 🚫 **CLI-Only Operations**
- ❌ **Mode Switching**: Change between debug/normal modes
- ❌ **Configuration**: Modify settings
- ❌ **Server Management**: Start/stop server

## Starting the Server

The server must be started using the CLI:

```bash
# Start with default settings
pbc server start

# Start on custom port
pbc server start --port 9000

# Start with custom data directory
pbc --data-dir /path/to/data server start

# Start in debug mode
pbc --debug server start
```

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Authentication
The server currently provides **no authentication**. Consider using a reverse proxy for production deployments.

---

## Data Operations

### 1. Server Status
Get server information and current status.

**Endpoint:** `GET /`

**Response:**
```json
{
  "status": "running",
  "mode": "normal",
  "data_dir": "/Users/user/Library/Application Support/pybitcask",
  "keys_count": 42
}
```

---

### 2. Store Key-Value Pair
Store a single key-value pair.

**Endpoint:** `POST /put`

**Request Body:**
```json
{
  "key": "string",
  "value": "any type"
}
```

**Response:**
```json
{
  "status": "success",
  "key": "your_key"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/put" \
     -H "Content-Type: application/json" \
     -d '{"key": "user_name", "value": "Alice"}'
```

---

### 3. Retrieve Value
Get a value by its key.

**Endpoint:** `GET /get/{key}`

**Response:**
```json
{
  "key": "user_name",
  "value": "Alice",
  "found": true
}
```

**Example:**
```bash
curl "http://localhost:8000/get/user_name"
```

**Not Found Response:**
```json
{
  "key": "nonexistent",
  "value": null,
  "found": false
}
```

---

### 4. Delete Key
Remove a key-value pair.

**Endpoint:** `DELETE /delete/{key}`

**Response:**
```json
{
  "key": "user_name",
  "deleted": true
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/delete/user_name"
```

---

### 5. List All Keys
Get all keys in the database.

**Endpoint:** `GET /keys`

**Response:**
```json
{
  "keys": ["user_name", "user_age", "user_city"],
  "count": 3
}
```

**Example:**
```bash
curl "http://localhost:8000/keys"
```

---

### 6. Clear Database
Remove all data from the database.

**Endpoint:** `POST /clear`

**Response:**
```json
{
  "status": "success",
  "message": "Database cleared"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/clear"
```

---

### 7. Batch Operations
Store multiple key-value pairs in a single request.

**Endpoint:** `POST /batch`

**Request Body:**
```json
{
  "data": {
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "count": 3
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "data": {
         "name": "Alice",
         "age": 30,
         "city": "San Francisco"
       }
     }'
```

---

### 8. Health Check
Simple health check endpoint.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "pybitcask-server"
}
```

**Example:**
```bash
curl "http://localhost:8000/health"
```

---

## Error Handling

### HTTP Status Codes
- `200`: Success
- `404`: Key not found (for GET operations)
- `500`: Internal server error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors
- **Database not initialized**: Server started without proper database setup
- **Key not found**: Attempting to retrieve a non-existent key
- **Invalid JSON**: Malformed request body
- **Server error**: Internal database or server issues

---

## Data Types

The server supports storing any JSON-serializable data types:

- **Strings**: `"hello world"`
- **Numbers**: `42`, `3.14`
- **Booleans**: `true`, `false`
- **Arrays**: `[1, 2, 3]`
- **Objects**: `{"nested": "data"}`
- **Null**: `null`

**Example with complex data:**
```bash
curl -X POST "http://localhost:8000/put" \
     -H "Content-Type: application/json" \
     -d '{
       "key": "user_profile",
       "value": {
         "name": "Alice",
         "age": 30,
         "preferences": ["coding", "reading"],
         "active": true
       }
     }'
```

---

## Complete Example Workflow

```bash
# 1. Start the server (CLI required)
pbc server start --port 8000

# 2. Check server status
curl "http://localhost:8000/"

# 3. Store some data
curl -X POST "http://localhost:8000/put" \
     -H "Content-Type: application/json" \
     -d '{"key": "greeting", "value": "Hello, World!"}'

# 4. Retrieve the data
curl "http://localhost:8000/get/greeting"

# 5. Store multiple items
curl -X POST "http://localhost:8000/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "data": {
         "name": "Alice",
         "age": 30,
         "city": "San Francisco"
       }
     }'

# 6. List all keys
curl "http://localhost:8000/keys"

# 7. Delete a key
curl -X DELETE "http://localhost:8000/delete/age"

# 8. Verify deletion
curl "http://localhost:8000/keys"

# 9. Clear all data
curl -X POST "http://localhost:8000/clear"

# 10. Stop the server (CLI required)
pbc server stop
```

---

## Integration Examples

### Python
```python
import requests

# Store data
response = requests.post('http://localhost:8000/put',
                        json={'key': 'python_key', 'value': 'python_value'})
print(response.json())

# Retrieve data
response = requests.get('http://localhost:8000/get/python_key')
data = response.json()
if data['found']:
    print(f"Value: {data['value']}")
```

### JavaScript/Node.js
```javascript
// Store data
const response = await fetch('http://localhost:8000/put', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ key: 'js_key', value: 'js_value' })
});
const result = await response.json();
console.log(result);

// Retrieve data
const getResponse = await fetch('http://localhost:8000/get/js_key');
const data = await getResponse.json();
if (data.found) {
  console.log(`Value: ${data.value}`);
}
```

### Go
```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

func main() {
    // Store data
    payload := map[string]interface{}{
        "key":   "go_key",
        "value": "go_value",
    }
    jsonData, _ := json.Marshal(payload)

    resp, err := http.Post("http://localhost:8000/put",
                          "application/json",
                          bytes.NewBuffer(jsonData))
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    fmt.Println("Data stored successfully")
}
```

---

## Production Considerations

### Security
- **No Authentication**: The server provides no built-in authentication
- **Network Security**: Consider running behind a reverse proxy
- **Access Control**: Restrict network access to authorized clients

### Performance
- **Connection Pooling**: Use HTTP connection pooling for high-throughput applications
- **Batch Operations**: Use `/batch` endpoint for multiple operations
- **Monitoring**: Monitor the `/health` endpoint for service availability

### Deployment
```bash
# Production deployment example
pbc --data-dir /var/lib/pybitcask server start --port 8000
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Limitations

1. **No Authentication**: Built-in authentication not provided
2. **No Authorization**: All clients have full access to all operations
3. **No Transactions**: Operations are not transactional
4. **No Bulk Delete**: Must delete keys individually
5. **No Pattern Matching**: Cannot search keys by pattern
6. **CLI Dependency**: Server lifecycle requires CLI access

For advanced features like mode switching, configuration changes, or server management, use the PyBitcask CLI.

---

## Support

For issues related to:
- **API Operations**: Check this documentation and error responses
- **Server Management**: Use `pbc server --help`
- **Configuration**: Use `pbc config --help`
- **Mode Switching**: Use `pbc mode --help`

# PyBitcask CLI (pbc)

A command-line interface for the PyBitcask key-value store, providing comprehensive management capabilities including data operations, mode switching, and configuration management.

## Overview

PyBitcask provides two interfaces for interacting with your data:

### 🖥️ **CLI Mode (Full Features)**
- ✅ **CRUD Operations**: Put, Get, Delete, List, Clear
- ✅ **Mode Management**: Switch between debug/normal modes
- ✅ **Configuration**: View and manage settings
- ✅ **Server Control**: Start/stop the REST API server

### 🌐 **Server Mode (CRUD Only)**
- ✅ **CRUD Operations**: REST API for data operations
- ❌ **Mode Management**: Use CLI for mode switching
- ❌ **Configuration**: Use CLI for configuration changes
- ❌ **Server Control**: Use CLI to manage server lifecycle

> **Note**: Mode management, configuration changes, and server lifecycle management are **CLI-exclusive features**. The server provides only data operations via REST API.

## Installation

```bash
# Install the CLI package
pip install -e cli
```

## CLI Usage

The CLI provides full control over your PyBitcask instance. The basic syntax is:

```bash
pbc [OPTIONS] COMMAND [ARGS]...
```

### Global Options

- `--data-dir PATH`: Specify the data directory (overrides configuration)
- `--debug`: Run in debug mode (human-readable format)

### Configuration

PyBitcask uses a configuration system that follows platform-specific conventions:

#### Data Directory Locations
- macOS: `~/Library/Application Support/pybitcask`
- Linux: `/var/lib/pybitcask`
- Windows: `C:\ProgramData\pybitcask`
- Fallback: `~/.pybitcask`

#### Configuration File Locations
- macOS: `~/Library/Preferences/pybitcask/config.json`
- Linux: `~/.config/pybitcask/config.json`
- Windows: `%APPDATA%\pybitcask\config.json`
- Fallback: `~/.pybitcask/config.json`

### CLI Commands

#### Data Operations (Available in both CLI and Server)

1. **Store a value**
   ```bash
   pbc put KEY VALUE
   ```
   Example:
   ```bash
   pbc put name "John Doe"
   ```

2. **Retrieve a value**
   ```bash
   pbc get KEY
   ```
   Example:
   ```bash
   pbc get name
   ```

3. **Delete a value**
   ```bash
   pbc delete KEY
   ```
   Example:
   ```bash
   pbc delete name
   ```

4. **List all keys**
   ```bash
   pbc list
   ```

5. **Clear all data**
   ```bash
   pbc clear
   ```

#### Mode Management (CLI Only)

The CLI supports two storage modes:
- **Normal mode**: Uses protobuf format for efficient storage
- **Debug mode**: Uses human-readable JSON format

> ⚠️ **Important**: Mode switching is only available through the CLI. The server inherits the current mode but cannot change it.

1. **Switch to debug mode**
   ```bash
   pbc mode debug
   ```
   This will:
   - Show a warning about data deletion
   - Ask for confirmation
   - Delete all existing data
   - Switch to debug mode
   - Create a new empty database

2. **Switch to normal mode**
   ```bash
   pbc mode normal
   ```
   This will:
   - Show a warning about data deletion
   - Ask for confirmation
   - Delete all existing data
   - Switch to normal mode
   - Create a new empty database

3. **Show current mode**
   ```bash
   pbc mode show
   ```

#### Server Operations (CLI Only)

> 📡 **Server Management**: Starting, stopping, and managing the server is only available through the CLI.

1. **Start the server**
   ```bash
   pbc server start [--port PORT]
   ```
   Example:
   ```bash
   pbc server start --port 8000
   ```
   The server will:
   - Use the configured data directory
   - Inherit current debug mode settings
   - Start on the specified port (default: 8000)
   - Provide REST API for CRUD operations only

2. **Stop the server**
   ```bash
   pbc server stop
   ```
   This will:
   - Attempt graceful shutdown
   - Force stop if graceful shutdown fails
   - Clean up server resources

#### Configuration Management (CLI Only)

> ⚙️ **Configuration**: Viewing and modifying configuration is only available through the CLI.

1. **View current configuration**
   ```bash
   pbc config view
   ```
   Shows:
   - Current data directory
   - Debug mode status
   - Other configuration settings

2. **Reset configuration**
   ```bash
   pbc config reset
   ```
   This will:
   - Reset all settings to defaults
   - Use platform-specific default paths
   - Clear custom configurations

## Server API

When the server is running, it provides a REST API for data operations only:

### Available Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `GET` | `/` | Server status | - |
| `POST` | `/put` | Store key-value pair | `{"key": "string", "value": "any"}` |
| `GET` | `/get/{key}` | Retrieve value | - |
| `DELETE` | `/delete/{key}` | Delete key | - |
| `GET` | `/keys` | List all keys | - |
| `POST` | `/clear` | Clear all data | - |
| `POST` | `/batch` | Batch operations | `{"data": {"key1": "value1", ...}}` |
| `GET` | `/health` | Health check | - |

### Server API Examples

```bash
# Start the server (CLI only)
pbc server start --port 8000

# Use the REST API
curl -X POST "http://localhost:8000/put" \
     -H "Content-Type: application/json" \
     -d '{"key": "name", "value": "John Doe"}'

curl "http://localhost:8000/get/name"

curl -X DELETE "http://localhost:8000/delete/name"

curl "http://localhost:8000/keys"
```

> **Note**: Mode switching, configuration changes, and server management are not available through the REST API. Use the CLI for these operations.

## Examples

### CLI Examples

```bash
# Store some data
pbc put name "John Doe"
pbc put age 30
pbc put city "New York"

# Retrieve data
pbc get name
pbc get age

# List all keys
pbc list

# Delete a key
pbc delete age

# Switch to debug mode (CLI only)
pbc mode debug

# Start server (CLI only)
pbc server start --port 8000
```

### Server API Examples

```bash
# First, start the server using CLI
pbc server start --port 8000

# Then use REST API for data operations
curl -X POST "http://localhost:8000/put" \
     -H "Content-Type: application/json" \
     -d '{"key": "user", "value": "Alice"}'

curl "http://localhost:8000/get/user"

curl "http://localhost:8000/keys"
```

### Configuration Examples (CLI Only)

```bash
# Use custom data directory
pbc --data-dir /path/to/data put key "value"

# Run in debug mode
pbc --debug put key "value"

# View current configuration
pbc config view

# Reset to defaults
pbc config reset
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   CLI Client    │    │  REST Client    │
│                 │    │                 │
│ • CRUD Ops      │    │ • CRUD Ops      │
│ • Mode Mgmt     │    │   (API only)    │
│ • Config Mgmt   │    │                 │
│ • Server Ctrl   │    │                 │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │                      │ HTTP
          │ Direct               │
          │                      │
          └──────┬───────────────┘
                 │
         ┌───────▼────────┐
         │  PyBitcask     │
         │  Database      │
         │                │
         │ • Data Storage │
         │ • Indexing     │
         │ • Persistence  │
         └────────────────┘
```

## Notes

- **CLI**: Full-featured interface with all capabilities
- **Server**: REST API for data operations only
- **Mode Management**: CLI exclusive - server inherits current mode
- **Configuration**: CLI exclusive - server uses current configuration
- **Server Control**: CLI exclusive - start/stop server via CLI commands
- **Data Operations**: Available in both CLI and server modes
- **Debug Mode**: Useful for development and debugging (JSON format)
- **Normal Mode**: Recommended for production use (protobuf format)

## Security Considerations

- The server provides no authentication by default
- Mode switching and configuration changes require CLI access
- Consider running the server behind a reverse proxy in production
- Restrict CLI access to authorized users for configuration management

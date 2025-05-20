# PyBitcask CLI (pbc)

A command-line interface for the PyBitcask key-value store, providing an easy way to interact with your data.

## Installation

```bash
# Install the CLI package
pip install -e cli
```

## Usage

The CLI provides several commands for managing your key-value store. The basic syntax is:

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

### Commands

#### Data Operations

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

#### Mode Management

The CLI supports two modes:
- **Normal mode**: Uses proto format for efficient storage
- **Debug mode**: Uses human-readable JSON format

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

#### Server Operations

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
   - Inherit debug mode settings
   - Start on the specified port (default: 8000)
   - Show the server URL when started

2. **Stop the server**
   ```bash
   pbc server stop
   ```
   This will:
   - Attempt graceful shutdown
   - Force stop if graceful shutdown fails
   - Clean up server resources

#### Configuration Management

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

## Examples

### Basic Usage

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
```

### Using Server

```bash
# Start server on default port
pbc server start

# Start server on custom port
pbc server start --port 9000

# Stop server
pbc server stop
```

### Configuration Examples

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

## Notes

- Configuration is persisted between sessions
- Server uses the same configuration as CLI
- Debug mode is useful for development and debugging
- Normal mode is recommended for production use
- Data is stored in the configured data directory
- Server supports graceful shutdown
- Configuration follows platform-specific conventions

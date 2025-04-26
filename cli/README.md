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

- `--data-dir PATH`: Specify the data directory (default: "./data")
- `--debug`: Run in debug mode (human-readable format)

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
- **Normal mode**: Uses binary format for efficient storage
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

2. **Stop the server**
   ```bash
   pbc server stop
   ```

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

### Switching Modes

```bash
# Start in normal mode (default)
pbc put key1 "value1"

# Switch to debug mode
pbc mode debug

# Store data in debug mode (human-readable)
pbc put key2 "value2"

# Check current mode
pbc mode show

# Switch back to normal mode
pbc mode normal
```

### Using Different Data Directory

```bash
# Use a custom data directory
pbc --data-dir /path/to/data put key "value"
```

## Notes

- Switching modes will delete all existing data
- The mode setting is persisted between sessions
- Data is stored in the specified data directory
- Debug mode is useful for development and debugging
- Normal mode is recommended for production use

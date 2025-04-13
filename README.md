# Python MeshCore

Python library for interacting with [MeshCore](https://meshcore.co.uk) companion radio nodes.

## Installation

```bash
pip install meshcore
```

## Quick Start

Connect to your device and send a message:

```python
import asyncio
from meshcore import MeshCore, EventType

async def main():
    # Connect to your device
    meshcore = await MeshCore.create_serial("/dev/ttyUSB0")
    
    # Get your contacts
    contacts = await meshcore.commands.get_contacts()
    print(f"Found {len(contacts)} contacts")
    
    # Send a message to the first contact
    if contacts:
        contact_key = next(iter(contacts.items()))[1]['public_key']
        await meshcore.commands.send_msg(bytes.fromhex(contact_key), "Hello from Python!")
    
    await meshcore.disconnect()

asyncio.run(main())
```

## Development Setup

To set up for development:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run examples
python examples/pubsub_example.py -p /dev/ttyUSB0
```

## Usage Guide

### Connecting to Your Device

Connect via Serial, BLE, or TCP:

```python
# Serial connection
meshcore = await MeshCore.create_serial("/dev/ttyUSB0", 115200, debug=True)

# BLE connection (scans for devices if address not provided)
meshcore = await MeshCore.create_ble("12:34:56:78:90:AB")

# TCP connection
meshcore = await MeshCore.create_tcp("192.168.1.100", 4000)
```

### Using Commands (Synchronous Style)

Send commands and wait for responses:

```python
# Get device information
device_info = await meshcore.commands.send_device_query()
print(f"Device model: {device_info['model']}")

# Get list of contacts
contacts = await meshcore.commands.get_contacts()
for contact_id, contact in contacts.items():
    print(f"Contact: {contact['adv_name']} ({contact_id})")

# Send a message (destination key in bytes)
await meshcore.commands.send_msg(dst_key, "Hello!")

# Setting device parameters
await meshcore.commands.set_name("My Device")
await meshcore.commands.set_tx_power(20)  # Set transmit power
```

### Finding Contacts

Easily find contacts by name or key:

```python
# Find a contact by name
contact = meshcore.get_contact_by_name("Bob's Radio")
if contact:
    print(f"Found Bob at: {contact['adv_lat']}, {contact['adv_lon']}")
    
# Find by partial key prefix
contact = meshcore.get_contact_by_key_prefix("a1b2c3")
```

### Event-Based Programming (Asynchronous Style)

Subscribe to events to handle them asynchronously:

```python
# Subscribe to incoming messages
async def handle_message(event):
    data = event.payload
    print(f"Message from {data['pubkey_prefix']}: {data['text']}")
    
subscription = meshcore.subscribe(EventType.CONTACT_MSG_RECV, handle_message)

# Subscribe to advertisements
async def handle_advert(event):
    print("Advertisement detected!")
    
meshcore.subscribe(EventType.ADVERTISEMENT, handle_advert)

# When done, unsubscribe
meshcore.unsubscribe(subscription)
```

#### Filtering Events by Attributes

Filter events based on their attributes to handle only specific ones:

```python
# Subscribe only to messages from a specific contact
async def handle_specific_contact_messages(event):
    print(f"Message from Alice: {event.payload['text']}")
    
contact = meshcore.get_contact_by_name("Alice")
if contact:
    alice_subscription = meshcore.subscribe(
        EventType.CONTACT_MSG_RECV,
        handle_specific_contact_messages,
        attribute_filters={"pubkey_prefix": contact["public_key"][:12]}
    )

# Send a message and wait for its specific acknowledgment
async def send_and_confirm_message(meshcore, dst_key, message):
    # Send the message and get information about the sent message
    sent_result = await meshcore.commands.send_msg(dst_key, message)
    
    # Extract the expected acknowledgment code from the message sent event
    expected_ack = sent_result["expected_ack"].hex()
    print(f"Message sent, waiting for ack with code: {expected_ack}")
    
    # Wait specifically for this acknowledgment
    result = await meshcore.wait_for_event(
        EventType.ACK,
        attribute_filters={"code": expected_ack},
        timeout=10.0
    )
    
    if result:
        print("Message confirmed delivered!")
        return True
    else:
        print("Message delivery confirmation timed out")
        return False
```

### Hybrid Approach (Commands + Events)

Combine command-based and event-based styles:

```python
import asyncio

async def main():
    # Connect to device
    meshcore = await MeshCore.create_serial("/dev/ttyUSB0")
    
    # Set up event handlers
    async def handle_ack(event):
        print("Message acknowledged!")
    
    async def handle_battery(event):
        print(f"Battery level: {event.payload}%")
    
    # Subscribe to events
    meshcore.subscribe(EventType.ACK, handle_ack)
    meshcore.subscribe(EventType.BATTERY, handle_battery)
    
    # Create background task for battery checking
    async def check_battery_periodically():
        while True:
            # Send command (returns battery level)
            result = await meshcore.commands.get_bat()
            print(f"Battery check initiated, response: {result}")
            await asyncio.sleep(60)  # Wait 60 seconds between checks
    
    # Start the background task
    battery_task = asyncio.create_task(check_battery_periodically())
    
    # Send manual command and wait for response
    await meshcore.commands.send_advert(flood=True)
    
    try:
        # Keep the main program running
        await asyncio.sleep(float('inf'))
    except asyncio.CancelledError:
        # Clean up when program ends
        battery_task.cancel()
        await meshcore.disconnect()

# Run the program
asyncio.run(main())
```

### Auto-Fetching Messages

Let the library automatically fetch incoming messages:

```python
# Start auto-fetching messages
await meshcore.start_auto_message_fetching()

# Just subscribe to message events - the library handles fetching
async def on_message(event):
    print(f"New message: {event.payload['text']}")
    
meshcore.subscribe(EventType.CONTACT_MSG_RECV, on_message)

# When done
await meshcore.stop_auto_message_fetching()
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
# Enable debug mode when creating the connection
meshcore = await MeshCore.create_serial("/dev/ttyUSB0", debug=True)
```

This logs detailed information about commands sent and events received.

## Common Examples

### Sending Messages to Contacts

```python
# Get contacts and send to a specific one
contacts = await meshcore.commands.get_contacts()
for key, contact in contacts.items():
    if contact["adv_name"] == "Alice":
        # Convert the hex key to bytes
        dst_key = bytes.fromhex(contact["public_key"])
        await meshcore.commands.send_msg(dst_key, "Hello Alice!")
        break
```

### Monitoring Channel Messages

```python
# Subscribe to channel messages
async def channel_handler(event):
    msg = event.payload
    print(f"Channel {msg['channel_idx']}: {msg['text']}")
    
meshcore.subscribe(EventType.CHANNEL_MSG_RECV, channel_handler)
```

## Examples in the Repo

Check the `examples/` directory for more:

- `pubsub_example.py`: Event subscription system with auto-fetching
- `serial_infos.py`: Quick device info retrieval
- `serial_msg.py`: Message sending and receiving
- `ble_t1000_infos.py`: BLE connections


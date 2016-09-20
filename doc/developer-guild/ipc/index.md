# IPC Module for ProcsZoo

## Package Name

`procszoo.ipc`

## Introduction

This module is used for interprocess communication (IPC) for processes
in difference namespaces. I designed and wrote this module because
existing IPC libraries are not suitable for inter-namespaces
communication.

Currently, we have implemented a JSON-RPC interface.

## Design

Messages are delivered over [Netlink][](7).
Before reading this document, you should read the above link first.

We use the following message format:

``` 
+-----------------------+
| nlmsghdr              |
+-----------------------+
| procslinkhdr          |
+-----------------------+
| JSON-RPC message      |
+-----------------------+
```

Where
- `nlmsghdr` is the raw Netlink header.
- `procslinkhdr` is our own defined header for extension
(because we may run different protocolsother than JSON-RPC in the future),
- `JSON-RPC message` is the JSON-RPC request/response body encoded
in **UTF-8**. [JSON-RPC 2.0] is used.

Following is the defination of `struct procslinkhdr`:

``` C
/* connectorhdr (8 bytes) */
struct procslinkhdr {
    uint16_t version; /* version number, default: 1 */
    uint16_t flag; /* reserved */
    uint32_t length; /* message length including this header */
    uint16_t payload_type; /* payload_type message type ID */
    uint16_t reserved; /* reserved */
    uint32_t seq; /* sequence number */
    uint64_t timestamp; /* when this message is sent */
};
```

## Dependencies

This module is an independent module, which doesn't depend on any other
parts of ProcsZoo.

Third-party dependencies:

- [python-future][]: to be compatible with both Python 2 and 3

## Directory Structure

```
+ procszoo/procszoo/ipc
  - __init__.py
  - common.py
  - jsonrpc.py
  - netlink.py
  - procslink.py
```

Where
- `__init__.py` defines the JSON-RPC server/client: `RPCPeer`. 
- `common.py` defines the base class for message headers and messages.
- `netlink.py` defines `NetlinkMessageHeader` and `NetlinkMessage`,
which are abstraction for Netlink header and whole netlink meesages.
- `procslink.py` defines message data structures for the
Procslink message layer.
-  `jsonrpc.py` defines models for JSON-RPC 2.0 request object, response
object, and error object, etc.

## API Usage Demo

### parse bytes to message objects

``` python
# suppose data is a raw Netlink message bytes
netlink_message = NetlinkMessage.from_bytes(data)
procslink_message = ProcslinkMessage.from_bytes(netlink_message.payload)
jsonrpc_request = JSONRPCRequest.from_bytes(procslink_message.payload)
```

### Convert message objects to raw bytes

``` python
jsonrpc_response = JSONRPCResponse(id=123, result=True)
procslink_header = ProcslinkMessageHeader(
    payload_type=ProcslinkMessageHeader.PAYLOAD_TYPE_JSONRPC2_RESPONSE)
procslink_message = ProcslinkMessage(procslink_header,
    jsonrpc_response.to_bytes()))
netlink_header = NetlinkMessageHeader(nlmsg_pid=sender_nl_pid)
netlink_message = NetlinkMessage(netlink_header,
    procslink_message.to_bytes())
data = netlink_message.to_bytes()
```

### Run JSON-RPC server

``` python
import os
from procszoo.ipc import RPCPeer

class MyAPI(object):
    def hello(self, name):
        s = "Hello, %s!" % name
        print(s)
        return s

rpc_server = RPCPeer()
print("server's nl_pid is %s", rpc_server.nl_pid)
rpc_server.register_functions_in_object(MyAPI())
rpc_server.run_server_forever()
```

### Run JSON-RPC client

``` python
from procszoo.ipc import RPCPeer

# server_nl_pid is server's nl_pid
rpc_client = RPCPeer()
rpc_client.talk_to(server_nl_pid).hello("Rayson Zhu")
```


[Netlink]: http://man7.org/linux/man-pages/man7/netlink.7.html
[JSON-RPC 2.0]: http://www.jsonrpc.org/specification
[python-future]: http://python-future.org/

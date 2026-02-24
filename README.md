# Distributed Mesh Network Communication Spec

This document defines the DistNet protocol model used by MeshArranger and the host-facing command surface exposed through the DistNet gateway.

## Scope

The specification covers two operating domains:

1. Intra-robot mesh: sensors, actuators, and compute nodes auto-discover each other and bind to capabilities.
2. Field mesh: robot gateway nodes expose selected capabilities to other robots and fixed field infrastructure.

### Robot auto-discovering components through the mesh

<img src="./design/RobotWithSensors2.png" alt="Robot auto discovering its own components" width="400">

### Robot and field-level discovery in shared space

<img src="./design/RobotField.png" alt="Robot discovering field components" width="400">

## DistNet Gateway Alignment

The host-accessible command surface in this repository is the DistNet gateway REST API (see `DistNetGtwy/spec/api.md` and `DistNetGtwy/README.md`).

- Base URL: `http://mesh-gateway.local:8080`
- Device static IP: `192.168.137.2/24`
- Host static IP: `192.168.137.1/24`
- mDNS hostname: `mesh-gateway.local`
- Supported endpoints:
  - `GET /health`
  - `POST /echo`
  - `POST /command`
- Supported `cmd` values in `POST /command`:
  - `status`
  - `echo`

## Quick Commands (Spec-Accurate)

### 1) Health check

```bash
curl -s http://mesh-gateway.local:8080/health
```

Expected shape:

```json
{
  "ok": true,
  "service": "mesh-gateway",
  "version": "1.0.0"
}
```

### 2) Status command via `/command`

```bash
curl -s -X POST http://mesh-gateway.local:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"cmd":"status","args":{}}'
```

Expected shape:

```json
{
  "ok": true,
  "result": {
    "uptime_ms": 12345,
    "ip": "192.168.137.2",
    "hostname": "mesh-gateway.local"
  }
}
```

### 3) Echo command via `/echo`

```bash
curl -s -X POST http://mesh-gateway.local:8080/echo \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello"}'
```

### 4) Echo command via `/command`

```bash
curl -s -X POST http://mesh-gateway.local:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"cmd":"echo","args":{"message":"hello"}}'
```

### 5) Unknown command handling

```bash
curl -s -X POST http://mesh-gateway.local:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"cmd":"not_real","args":{}}'
```

Expected shape:

```json
{
  "ok": false,
  "error": "unknown_command",
  "cmd": "not_real"
}
```

### 6) CLI helper commands

`DistNetGtwy/tools/gatewayctl.py` wraps the same contract:

```bash
python3 DistNetGtwy/tools/gatewayctl.py health
python3 DistNetGtwy/tools/gatewayctl.py status
python3 DistNetGtwy/tools/gatewayctl.py echo "hello"
python3 DistNetGtwy/tools/gatewayctl.py call echo --args '{"message":"hello"}'
```

## Goals

- Zero manual wiring of component relationships at startup.
- Fast discovery and re-discovery after reset, disconnect, or brownout.
- Stable capability naming (bind by service, not by address).
- Consistent behavior from robot-internal to field-wide deployments.
- Compact message envelopes for constrained wireless links.

## Terms

- Node: any participant in the mesh (sensor, actuator, controller, compute unit, robot gateway, or field beacon).
- Service: a capability provided by a node (for example `imu.attitude`, `motor.set_rpm`, `field.zone_state`).
- Service key: compact identifier derived from canonical service name and major version.
- Robot mesh: all nodes physically belonging to one robot.
- Field mesh: robot gateways plus other robots and field infrastructure.

## Network Model

- Topology: peer mesh with no mandatory always-on coordinator.
- Addressing:
  - `node_id`: globally unique node identifier.
  - `robot_id`: identifier shared by components from one robot.
  - `field_id`: identifier for the current match/field context.
- Discovery domains:
  - Local domain: robot-internal traffic and bindings.
  - Field domain: robot gateway plus external robots/field nodes.

## Service Identity

Canonical service naming:

- `<domain>/<service_name>:<major_version>`

Examples:

- `core/attitude:1`
- `act/motor.set_rpm:1`
- `field/zone_occupancy:1`

Each service name maps to a deterministic 16-bit `service_key` used for compact advertisements and lookups.

## Protocol Envelope

All mesh messages use a fixed-size header and typed payload body (TLV or equivalent compact encoding).

Required header fields:

- `proto_ver`
- `msg_type`
- `src_node_id`
- `dst_node_id` (or broadcast address)
- `seq`
- `timestamp_ms`

## Core Message Families

- `HELLO`: periodic node presence and compact capability summary.
- `WHO_HAS`: request providers for one or more service keys.
- `I_HAVE`: response listing matching providers.
- `DESCRIBE_NODE`: request full node profile.
- `NODE_PROFILE`: full profile response.
- `DESCRIBE_SERVICE`: request a service schema/contract.
- `SERVICE_DESC`: service schema response.
- `PUBLISH`: telemetry/event publication.
- `CALL`: request/command invocation.
- `RESULT`: response to `CALL`.
- `PING` / `PONG`: liveness verification.
- `BYE`: graceful leave/disconnect.

## Capability Advertisement Contract

`HELLO` must remain compact and cacheable. It includes:

- `node_id`, `robot_id`, `role`, `health`
- `provides[]`, each entry containing:
  - `service_key`
  - `service_class` (`sensor`, `actuator`, `compute`, `field`)
  - `confidence` (`0-100`)
  - `qos_flags`
- `profile_hash` for validating cached `NODE_PROFILE` data

Design intent:

- Keep recurring network cost low.
- Support fast matching for dependencies.
- Defer large metadata transfer until explicitly requested.

## Full Node Profile (On Demand)

Retrieved via `DESCRIBE_NODE` and returned as `NODE_PROFILE`.

Expected profile content:

- hardware identity (model, serial, firmware)
- mount/frame metadata for spatial devices
- units, scaling, and normalization rules
- accuracy, covariance, and calibration state
- supported commands and operational limits
- rate/timing guarantees
- safety state model and fault semantics

## Discovery and Binding Flow (Single Robot)

1. Node boots and enters `DISCOVERING`.
2. Node broadcasts `HELLO`.
3. Peers cache summary and check dependency set.
4. Missing dependency triggers `WHO_HAS(service_key...)`.
5. Providers answer with `I_HAVE`.
6. Requestor ranks candidates by trust, health, confidence, freshness, then latency.
7. If necessary, requestor fetches `NODE_PROFILE` for compatibility checks.
8. Node transitions to `OPERATIONAL` when required dependencies are bound.

Failure path:

- Missed `HELLO` window triggers `PING` retries.
- Dependency timeout removes binding.
- Node re-enters discovery and issues fresh `WHO_HAS`.
- If required minimum is not satisfied, node emits a minimum-dependency failure event and enters `DEGRADED`.

## Multi-Robot + Field Flow

1. Each robot forms an internal mesh using the same process above.
2. Robot gateway exports selected services to the field domain.
3. Field infrastructure advertises official services (time, localization beacons, zone/game state, etc.).
4. Robots discover peer robot services and field services.
5. Export policy enforces visibility boundaries.

Domain split:

- Robot-internal domain: high-rate telemetry and actuator paths.
- Field domain: bounded, policy-filtered, match-relevant data only.

## Node Lifecycle State Machine

States:

- `BOOT`
- `UNPROVISIONED` (optional)
- `DISCOVERING`
- `BINDING`
- `OPERATIONAL`
- `DEGRADED`
- `FAULT`

Required transitions:

- `BOOT -> DISCOVERING`
- `DISCOVERING -> BINDING` when candidates are available
- `BINDING -> OPERATIONAL` when required dependencies are satisfied
- `OPERATIONAL -> DEGRADED` when a critical dependency is lost
- `DEGRADED -> OPERATIONAL` when rebind succeeds

## Reliability and Timing

- `HELLO` interval: `250-1000 ms` depending on profile.
- Dependency timeout: `3x` expected `HELLO` interval.
- `CALL`/`RESULT` retry policy is service-class specific.
- Sequence numbers reject stale and duplicate payloads.

## Security and Safety

- Trust check (signed identity or trusted allow-list) required before binding critical control paths.
- Authorization policy:
  - Internal actuator control requires trusted role.
  - Field-domain feeds default to read-only unless explicitly enabled.
- Safety interlocks:
  - reject out-of-range commands
  - enter safe mode on repeated auth failures or malformed command envelopes

## Data Model Requirements

Each service descriptor must define:

- `service_key`
- canonical name + major version
- direction (`publish`, `callable`, or both)
- payload schema reference
- units and valid ranges
- min/max update rates
- fault code set

## Acceptance Criteria

- A new robot node joins without manual address configuration.
- Removing and restoring a non-critical node does not prevent operation.
- Multiple robots coexist without service-key collision ambiguity.
- Field services are discovered and consumed within bounded latency.
- Internal-only services are not exposed to unauthorized field peers.

## Implementation Notes

- Keep periodic advertisements compact and deterministic.
- Pull profile/service detail only when the cache hash changes.
- Cache profile by `node_id + profile_hash`.
- Increase major version on incompatible payload or behavior changes.
- Gateway REST API is currently a minimal command bridge; extend `/command` with new `cmd` values as DistNet features are promoted to host-facing operations.

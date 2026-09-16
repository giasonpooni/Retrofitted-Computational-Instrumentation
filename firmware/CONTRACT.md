# Firmware contract (not a board sketch)

The first C increment must emit the same observation object the host tests
already refuse to corrupt. Do not start with device-specific Arduino sketches
and later invent a platform.

Pinned target for the first board: LILYGO T-Display-S3, ESP-IDF.
Citation: https://wiki.lilygo.cc/products/t-display-series/t-display-s3/

GPIO15 is peripheral power enable. It must be driven high before the panel
and some peripherals work. That is board profile, not instrument identity.

## Acquisition path

```
Trigger / data-ready / approved schedule
        |
        v
Acquire and timestamp
        |
        v
Bounded queue
   /    |    \
log  display  transport
```

Display, Wi-Fi, and agents are consumers. They do not own the sample.

## Record the firmware must emit

- observation_id = session_id + sequence (assigned at acquire, not at publish)
- session_id distinct after reboot
- device_ticks and what that timestamp means
- assembly_id, assembly_version, calibration_id
- raw and raw_unit, or unavailable
- indicated only from the declared calibration
- four quality dimensions, not one GOOD flag

## Timing

A microsecond timer callback is not a microsecond sample instant.
Retain boot/session id, sequence, device clock, and the meaning of that clock.
UTC conversion is a separate mapping with its own basis. Do not rewrite
device history when network time jumps.

## Transport

Application-level observation identity is independent of MQTT packet ids.
A retry is another delivery of the same observation.
Broker ACK is not durable admission.

## Updates (plan now, activate later)

Version independently: hardware assembly, firmware build, device
configuration, sensor/installation binding, calibration, observer model.

First bench prototype may use wired updates. Storage layout, recovery
access, and firmware identity still belong in the first C project so a
later OTA path has somewhere to land.

Agents expose retained observations, health, and proposed configuration
changes. They do not get arbitrary GPIO, bus, or flash authority.

## First C increment (when a board is on the bench)

One documented interface chain. Local acquire + bounded log.
USB or UART to the laptop receiver in this repo.
No observer on the device.
No silent last-value hold.

This directory holds the contract. It does not yet hold a flashing image.
That is deliberate: host tests establish the record before the first hex file.

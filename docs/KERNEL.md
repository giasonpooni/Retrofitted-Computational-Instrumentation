# Ownership. Write this down and stop renegotiating it.

Industrial-grade integrity here means: the measurement chain is reconstructible,
the raw observation is never replaced by an estimate, and a retry is not a new
sample. It does not mean a certificate, a SIL rating, or a universal device
platform.

## Language

| Layer | Language | Why |
| --- | --- | --- |
| Board / acquisition | C (ESP-IDF) | Timing, persistence, electrical interface. Julia does not run here. |
| Measurement contract, manifests, quality flags, replay | Python | Same declaration style as FSRT / torus. Host tests must fail without hardware. |
| A2-A5, charts, J Sigma J^T | Python (JSPT) | Already pinned. A Julia rewrite is a forbidden fork of the law. |
| Exact torus lengths, SL(2,Z) fold | Python | The object is small; exactness is algebraic, not throughput. |
| Optional later kernel: geodesic ODE / Jacobi vs s, sin s, sinh s | Julia or Python | Only if the Python integrator is the bottleneck and the report contract stays Python. |

Consumption is one way. This repo does not import JSPT. JSPT does not import this repo.
Observers run on the laptop after the record exists.

SP1 does not run here. An observation digest is SHA-256 of the canonical
record and may later appear in a GAT evidence_commitments list. It does
not prove the sensor, the calibration, or the building.

## Components that must change independently

| Component | What it describes | What should change independently |
| --- | --- | --- |
| Board profile | Exact LILYGO model/revision, pins, peripherals, storage, display, power. | Replacing the computing board. |
| Measurement-interface driver | How raw information is acquired. | Replacing the electrical or optical interface. |
| Instrument profile | Physical sensor, quantity, range, uncertainty model. | Replacing or recalibrating the instrument. |
| Installation binding | Asset or region observed, mount, applicable configuration. | Moving the instrument. |
| Calibration | y = g(r; theta), range, units, citation. | A new conversion. History is not rewritten. |

Electrical compatibility is declared. A pin name does not make an unknown probe safe.

## Quality is four questions

| Status dimension | Example |
| --- | --- |
| Acquisition | Sample received, disconnected channel, overrange, corrupt response. |
| Timing | Device clock at readout, readout time only, clock mapping unknown. |
| Calibration | Applicable, unsupported range, changed installation. |
| Inference | Not run, observer updated, prediction only, model outside support. |

One GOOD flag is forbidden. Unknown uncertainty must not become zero.

## What belongs in the declaration

Add a user-set parameter only if it changes the object or the evidence.

- geometry of the instrument and installation
- calibration theta, range, units, citation
- measurement sigma when the source is silent
- chart scales when they are a change of representation
- sample schedule only when it changes what the record means

A tank id or a display preference in the conversion is drift.

## What not to do

- Julia as a second law or a second finite_difference.
- Firmware sketches that bury `reading = raw * 0.037`.
- Filling a gap with the last value.
- Treating MQTT ACK as admission of a physical observation.
- Pulling Kalman / JSPT into this repo.
- Proving samples with SP1.
- Claiming the dial-reader measures process pressure.

## Review question

Does this helper exist if we delete the domain names (LILYGO, displacement, bench)?

If yes, and it is a chart or Jacobian law, it belongs in JSPT or it is a fork.
If no, it stays in this kernel.

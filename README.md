# Rugged Monitor EP-0084

A rugged, 3D-printed enclosure for the
[52Pi EP-0084](https://wiki.52pi.com/index.php/EP-0084) 7" capacitive touch display
(1024×600, HDMI, touch over USB).

![Front with the sun hood](out/11-sun-hood.png)
![Rear](out/2-rear.png)

- Outer dimensions: 192.9 × 148.9 × 40.5 mm
- VESA 75 mount
- Protection against shock, dust and splashes (gasket between bezel and cover, caps on the ports)
- HDMI and power on the top edge, touch micro-USB on the side
- Menu buttons reachable from outside, through TPU keys
- Detachable sun hood, for use on a car dashboard
- Tilting desk stand, 0° to 60° back from vertical (see [Desk stand](#desk-stand))

## Parts

The files in `out/` open in print orientation and need no supports.

| File | Material | Volume |
|---|---|---|
| `front-bezel.stl` | Rigid | 90 cm³ |
| `chassis.stl` | Rigid | 46 cm³ |
| `rear-cover.stl` | Rigid | 184 cm³ |
| `keypad-frame.stl` | Rigid | 7 cm³ |
| `sun-hood.stl` | Rigid | 42 cm³ |
| `keypad-strip-tpu.stl` | TPU 95A | 2 cm³ |
| `port-cap-hdmi-dc-tpu.stl` | TPU 95A | 4 cm³ |
| `port-cap-usb-tpu.stl` | TPU 95A | 1 cm³ |

Rigid material: ASA for use in a car (PETG softens near 80 °C and PLA is not
suitable); PETG is enough for indoor use.

Fit tests, to validate clearances before printing the large parts:
`test-lcd-pocket.stl` (LCD pocket), `test-hardware.stl` (nut slots and holes) and
`test-port-walls.stl` (the port walls of the cover).

`rugged-monitor.step` holds the full assembly, including the kit components as
reference.

## Hardware

| Qty | Part | Where |
|---|---|---|
| 6 | M3×20 screw, socket cap head (DIN 912) | Closing the cover against the bezel |
| 5 | M3×16 screw, button head (ISO 7380) | Key pins |
| 31 | M3×10 screw, button head (ISO 7380) | Chassis (9), boards (6), keypad frame (6), sun hood (6), OSD keypad (2), port cap tethers (2) |
| 29 | M3 hex nut, standard (DIN 934) | Closure (6), chassis (9), boards (6), sun hood (8) |
| 10 | M3 heat-set threaded insert | Keypad frame (6), OSD keypad (2), port cap tethers (2) |
| 4 | M4 heat-set threaded insert | VESA mount |
| 4 | M4×8 screw | VESA mount |
| — | Neutral-cure silicone sealant | Gasket between bezel and cover |
| — | 1 mm adhesive foam tape | Between the front lip and the glass; between the LCD and the chassis |

No screw threads directly into plastic: nuts are held captive in slots where there
is access, and brass inserts are used in the blind holes that must not go through
the wall.

## Assembly, in short

1. Slide the 9 chassis nuts into the slots in the wall of the LCD pocket.
2. Stick the foam on the lip and lay the LCD + glass assembly in, with the flex cables on the side of the stops.
3. Fit the 6 nuts under the chassis, pass the flex cables through its slots and screw the chassis down.
4. Mount the video board and the touch board on the chassis and connect the flex cables.
5. On the cover: set the inserts, drop in the key pins, mount the OSD keypad, the keypad strip and the frame.
6. Close the cover with the 6 M3×20 screws.

The gasket is formed in place: silicone in the bezel groove, release agent on the
cover tongue, cured with the case closed and empty.

## Desk stand

A printed stand to use the monitor on a table. It bolts to the VESA 75 pattern of the
cover, so the enclosure itself is not modified, and the screen tilts from upright to
60° back.

![Desk stand, tilted 30°](out/12-stand-front.png)
![Stand from behind](out/14-stand-rear-detail.png)

- Footprint 150 × 160 mm; the lowest edge of the enclosure is 11 mm above the table
  when upright
- Two printed parts, no supports: a base with two arms, and a bracket (VESA plate with
  two side walls) that turns between the arms
- One M4 bolt per side is the pivot. A second one runs in an arc slot of the arm; a
  wing nut clamps the wall against the arm to hold the angle, so the tilt is
  continuous
- The sun hood fits at every angle; the stand does not cover the ports, the closure
  screws or the keys
- Self-adhesive rubber feet go in the four recesses under the base

| File | Material | Volume |
|---|---|---|
| `stand-base.stl` | Rigid | 153 cm³ |
| `stand-bracket.stl` | Rigid | 62 cm³ |
| `test-stand-hinge.stl` | Rigid | 28 cm³ |

`test-stand-hinge.stl` is a fit test: one arm with its slot and one wall with the
hex pockets and the counterbored VESA hole. Print it before the two large parts.
`desk-stand.step` holds the assembly, with the enclosure tilted 30° as reference.

| Qty | Part | Where |
|---|---|---|
| 4 | M4×8 screw, button head (ISO 7380) | Bracket to the VESA inserts of the cover |
| 4 | M4×20 bolt, hex head (DIN 933) | Pivot (2) and tilt lock (2); the head sits in a hex pocket of the wall |
| 2 | M4 nylon lock nut (DIN 985) | Pivot |
| 2 | M4 wing nut (DIN 315) | Tilt lock |
| 4 | M4 washer, 9 mm outside diameter | Under the nuts |
| 4 | Self-adhesive rubber foot, Ø10 mm | Underside of the base |

Assembly, in short:

1. Screw the bracket to the four VESA inserts of the cover; the screw heads sit in the counterbores.
2. Stand the base up and lower the bracket between its two arms.
3. On each side, push a bolt from inside the bracket through the wall and the arm, with the head in the hex pocket.
4. Pivot: washer and lock nut, tightened until the bracket turns freely without play.
5. Lock: washer and wing nut. Loosen to tilt, tighten to hold.

The two walls sit inside the arms, with 0.6 mm between wall and arm until the wing nut
is tightened.

## Regenerating the model

The model is generated by the `fusion/RuggedMonitor/RuggedMonitor.py` script, for
Autodesk Fusion. Every dimension lives in the `P` dictionary at the top of the file.

1. Copy (or link) the `fusion/RuggedMonitor` folder into Fusion's scripts folder.
2. In Fusion: Utilities → Scripts and Add-Ins → RuggedMonitor → Run.

The script rebuilds the "Rugged Monitor" document if it is open (otherwise it creates
a new one) and writes the STL files, the STEP file and the images to `out/`.

The stand is generated the same way by `fusion/RuggedMonitorStand/RuggedMonitorStand.py`
(link the `fusion/RuggedMonitorStand` folder too). It takes the enclosure from
`RuggedMonitor.py`, so both folders must be in the repository layout. Besides the parts
it moves the enclosure through the whole tilt range and logs any overlap and the
closest approach to the base in `out/build-stand.log`.

## Status

The bezel, chassis and cover have been printed and validated against the real
hardware. The keys (TPU strip, pins and frame), the port caps and the silicone gasket
have not been tested yet.

The desk stand has been checked in the model only (no overlaps from 0° to 60°, hardware
included). It has not been printed yet.

## License

- **The Fusion scripts** (`fusion/RuggedMonitor`, `fusion/RuggedMonitorStand`) — [MIT](LICENSE)
- **The design** (`out/*.step`, `out/*.stl`, renders) — [CC BY-SA 4.0](LICENSE-DESIGN.md)

You may print and sell this enclosure and its stand; credit José Macário (@zmacario), link back here,
and share modifications of the design under the same license. See
[LICENSE-DESIGN.md](LICENSE-DESIGN.md).

Not affiliated with 52Pi.

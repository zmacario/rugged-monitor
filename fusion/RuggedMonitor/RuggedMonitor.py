# Rugged enclosure for the 52Pi EP-0084 display (7" 1024x600, capacitive touch).
#
# Fusion script: Utilities > Scripts and Add-Ins > RuggedMonitor > Run.
# Rebuilds the "Rugged Monitor" document if it is active (otherwise creates a new
# one) with the printed parts (bezel, chassis, cover, keypad parts, TPU caps,
# sun hood) and the kit components as reference.
#
# All dimensions are in mm in the P dictionary. To adjust the design, change the
# values and run the script again.
#
# Axes (REAR view of the monitor): X to the right, Y up,
# Z = 0 at the front face of the bezel, increasing towards the back.

import math
import os
import traceback

import adsk.core
import adsk.fusion

P = dict(
    # --- LCD (TP_Dimension drawing on the wiki) ---
    lcd_w=164.86, lcd_h=99.96,  # confirmed with the printed fit test
    stack_t=4.55,           # measured: LCD + touch glass, bonded
    lcd_fpc_left=68.23,     # from the left edge (front view) to the flex cable
    lcd_fpc_w=25.5,
    # --- touch glass (Tp-mechanical) ---
    tp_w=164.4, tp_h=99.3,
    va_w=155.0, va_h=89.0,  # visible area
    va_left=2.9, va_top=2.9,  # confirmed: margins seen from the front (right 6.5, bottom 7.4)
    tp_tail_right=13.3,     # from the right edge (front view) to the flex cable
    tp_tail_w=15.5,
    # --- video board (Outlinedrawing) ---
    vb_w=90.6, vb_h=65.6,
    vb_con1_x=34.75,        # flex connector centre, from the left
    lcd_fpc_len=42.9,       # measured: LCD flex folded and pulled flat behind the LCD
    vb_holes=((2.4, 2.3), (2.4, 62.1), (79.6, 1.6), (88.75, 61.9)),   # confirmed on the printed chassis
    vb_hdmi_x=60.6, vb_dc_x=82.1, vb_vga_x=33.3, vb_rca_x=10.5,
    hdmi_zc=3.1,            # HDMI centre above the board face
    dc_zc=6.5,              # confirmed: DC jack centre above the board face
    # --- CTP-5710 touch board ---
    ctp_l=56.9, ctp_w=28.07,
    tp_tail_len=34.5,       # measured: touch flex folded and pulled flat behind the LCD
    ctp_hole=3.56,
    ctp_usb=13.46,          # micro-USB centre from the end opposite the flex
    usb_zc=1.4,
    # --- flex cables: each board sits where its flex reaches with slack ---
    fpc_contact=5.0,        # flex tip that goes into the connector
    fpc_slack=5.5,          # slack so the flex is not pulled tight
    fpc_conn_h=1.0,         # connector mouth above the board face
    fpc_slot=12.0,          # height of the chassis slots above the LCD bottom edge
    # --- OSD keypad ---
    kp_l=76.0, kp_w=16.0,
    kp_x=73.0,              # keypad centre in X (rear view)
    kp_btn=(5.90, 23.75, 36.325, 52.025, 69.90),  # from the LED end
    kp_holes=(15.15, 60.68),
    kp_row=4.0,             # measured: button row from the board edge
    kp_sw_h=4.6,            # measured: button height above the board
    # --- Z stack-up ---
    lip_t=2.5,              # front lip that protects the glass
    seal_t=0.8,             # sealing foam between lip and glass (1 mm, compressed)
    pad_t=1.0,              # foam between LCD and chassis
    mid_t=2.0,              # chassis
    so_h=8.0,               # board standoffs (8 mm to suit an M3x10 screw)
    pcb_t=1.6,
    comp_h=13.0,            # tallest component (VGA) above the board
    clr=3.0,
    back_t=4.0,
    # --- enclosure ---
    fit=0.3,                # LCD clearance in its pocket
    test_wall=3.0, test_depth=4.0,   # LCD pocket fit test
    center_window=True,     # widen the case so the window is centred on the front
    fpc_gap=2.5,            # room for the flex cables to fold under the LCD
    ledge=7.0,              # chassis ledge around the pocket
    mid_clr=0.25,
    wall_gap=0.5,
    wall=4.4,
    r_out=10.0,
    groove_w=2.4, groove_d=1.5,   # gasket groove in the bezel
    # tongue on the cover that enters the groove; the gap around it (0.5 mm on each
    # side and at the bottom) is for the silicone sealant gasket
    tongue_w=1.4, tongue_h=1.0,
    lug_d=10.0, lug_out=2.5, lug_x=75.0,
    lug_fillet=6.0,         # fillet radius between each screw column and the wall
    # no screw threads into plastic: M3 nuts captive in slots or pockets where there
    # is access, brass inserts in the blind holes that must not go through
    nut_af=5.7, nut_h=2.6,        # slot for an M3 nut (5.5 across flats, 2.4 thick); confirmed on the test print
    nut_roof=2.25,                # plastic between the nut and the chassis seat
    lug_nut_z=2.0,                # height of the nut slot in the columns, from the front
    ins_d=4.0,                    # hole for an M3 threaded insert
    # lengths chosen to suit the screws already in stock: M3x20 cap head for the
    # closure, M3x16 button head for the pins, M3x10 button head everywhere else
    m3_clear=3.4, m3_head=6.5, m3_grip=11.0,
    chassis_collar=2.0,           # collar under the chassis screw heads
    vesa=75.0, vesa_ins_d=5.6, vesa_ins_depth=6.0, vesa_boss_d=11.0,
    # keys: one M3 button-head screw per button acts as a pin; its head floats
    # outside the cover, under a TPU strip held down by a frame
    pin_len=16.0, pin_d=3.0, pin_head_d=5.7, pin_head_h=1.65,
    pin_hole_d=3.4,
    key_float=0.6,          # gap of the pin head above the cover (travel + margin)
    key_cav_d=11.0,         # TPU chamber around the pin head
    key_roof=0.6,           # membrane the finger presses
    key_flange=0.6, key_bead_w=0.8, key_bead_h=0.5,
    key_nub_d=4.0, key_nub_h=0.5,   # raised marker on each button axis
    frame_t=4.0, frame_pocket=1.0, frame_half_w=16.5, frame_screw_dx=12.5,
    frame_boss_h=6.0,
    hdmi_open=(24.0, 14.0), dc_open=13.0, usb_open=(12.5, 9.0),
    cap_t=2.0, cap_plug=4.0,
    tether_len=10.0, tether_w=8.0, tether_t=1.0, eye_d=9.0,   # port cap tether and eyelet
    tether_rib=6.0, tether_hole=9.0,
    tether_top_len=30.0, tether_top_w=6.0, eye_top_d=8.0,     # L-shaped tether of the top cap
    chamfer=1.2, win_chamfer=1.5,
    # detachable sun hood, held by M3x10 thumb screws that thread into nuts sitting
    # in slots open on the bezel edges. The pattern is symmetric about the window
    # centre, so the hood fits in both orientations.
    hood_side_dx=89.5, hood_side_dy=22.0, hood_top_dx=55.0, hood_top_dy=60.95,
    hood_nut_z=3.0, hood_hole_z=7.8,
    hood_inset=1.9,         # flange inset from the bezel outline
    hood_corner_r=6.0,      # inner radius of the hood top corners
    hood_margin=6.0, hood_depth=50.0, hood_depth_bottom=15.0, hood_wall=2.0, hood_flange_t=3.0,
)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'out')

tbm = None
log_lines = []


def log(msg):
    log_lines.append(str(msg))


def pt(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def box(x0, x1, y0, y1, z0, z1):
    obb = adsk.core.OrientedBoundingBox3D.create(
        pt((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
        adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
        (x1 - x0) / 10.0, (y1 - y0) / 10.0, (z1 - z0) / 10.0)
    return tbm.createBox(obb)


def cyl(p0, p1, d):
    return tbm.createCylinderOrCone(pt(*p0), d / 20.0, pt(*p1), d / 20.0)


def cyl_z(x, y, z0, z1, d):
    return cyl((x, y, z0), (x, y, z1), d)


def add(target, tool):
    tbm.booleanOperation(target, tool, adsk.fusion.BooleanTypes.UnionBooleanType)


def cut(target, tool):
    tbm.booleanOperation(target, tool, adsk.fusion.BooleanTypes.DifferenceBooleanType)


def hexprism(x, y, z0, z1, af):
    b = None
    for ang in (0.0, 60.0, 120.0):
        a = math.radians(ang)
        obb = adsk.core.OrientedBoundingBox3D.create(
            pt(x, y, (z0 + z1) / 2),
            adsk.core.Vector3D.create(math.cos(a), math.sin(a), 0),
            adsk.core.Vector3D.create(-math.sin(a), math.cos(a), 0),
            2 * af / 10.0, af / 10.0, (z1 - z0) / 10.0)
        side = tbm.createBox(obb)
        if b is None:
            b = side
        else:
            tbm.booleanOperation(b, side, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return b


def rrect(x0, x1, y0, y1, z0, z1, r):
    b = box(x0 + r, x1 - r, y0, y1, z0, z1)
    add(b, box(x0, x1, y0 + r, y1 - r, z0, z1))
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r):
            add(b, cyl_z(cx, cy, z0, z1, 2 * r))
    return b


def build():
    p = P
    g = {}

    # pocket for LCD + glass
    px1 = p['lcd_w'] / 2 + p['fit']
    px0 = -px1
    py1 = p['lcd_h'] / 2 + p['fit']
    py0 = -(p['lcd_h'] / 2 + p['fit'] + p['fpc_gap'])
    lcd_bot = -p['lcd_h'] / 2

    # window (X mirrored: the model is in rear view)
    va_right = p['tp_w'] - p['va_w'] - p['va_left']
    wx0 = -p['tp_w'] / 2 + va_right
    wx1 = p['tp_w'] / 2 - p['va_left']
    wy1 = p['tp_h'] / 2 - p['va_top']
    wy0 = wy1 - p['va_h']

    # base outline of the case: the pocket, widened on the side the window is
    # offset towards, so that the window ends up centred on the front
    ex = (wx0 + wx1) - (px0 + px1) if p['center_window'] else 0.0
    ey = (wy0 + wy1) - (py0 + py1) if p['center_window'] else 0.0
    ax0, ax1 = px0 + min(ex, 0.0), px1 + max(ex, 0.0)
    ay0, ay1 = py0 + min(ey, 0.0), py1 + max(ey, 0.0)
    cx = (ax0 + ax1) / 2
    cy = (ay0 + ay1) / 2

    # offsets from the base outline
    d_mid = p['ledge']
    d_rec = d_mid + p['mid_clr']
    d_in = d_mid + p['wall_gap']
    d_out = d_in + p['wall']
    d_lug = d_out + p['lug_out']
    d_gc = d_in + p['wall'] / 2
    r_corner = d_out - p['r_out']

    def ring(d, z0, z1):
        return rrect(ax0 - d, ax1 + d, ay0 - d, ay1 + d, z0, z1, d - r_corner)

    # Z levels
    stack = p['stack_t']
    z_glass = p['lip_t'] + p['seal_t']
    z_ledge = z_glass + stack + p['pad_t']
    z_split = z_ledge + p['mid_t']
    z_pcb = z_split + p['so_h'] + p['pcb_t']
    z_in = z_pcb + p['comp_h'] + p['clr']
    T = z_in + p['back_t']

    lug_defs = [(x, yw, sgn) for yw, sgn in ((ay1 + d_out, 1), (ay0 - d_out, -1))
                for x in (cx - p['lug_x'], cx, cx + p['lug_x'])]
    lugs = [(x, yw + sgn * p['lug_out']) for x, yw, sgn in lug_defs]

    def lug_body(x, y_wall, sgn, z0, z1):
        # screw column blended into the wall by two concave fillets. The arcs
        # cross the wall and the column at a tiny angle instead of being exactly
        # tangent, to keep the boolean operation robust.
        r, f, lo = p['lug_d'] / 2, p['lug_fillet'], p['lug_out']
        fy = f - 0.02
        dx = ((r + f) ** 2 - (fy - lo) ** 2) ** 0.5 * 0.9995
        y_t = lo + (fy - lo) * r / (r + f)
        b = cyl_z(x, y_wall + sgn * lo, z0, z1, 2 * r)
        ya, yb = sorted((y_wall - sgn * 0.5, y_wall + sgn * y_t))
        web = box(x - dx, x + dx, ya, yb, z0, z1)
        for side in (-1, 1):
            cut(web, cyl_z(x + side * dx, y_wall + sgn * fy, z0 - 1, z1 + 1, 2 * f))
        add(b, web)
        return b

    # flex cables
    fpc_x1 = p['lcd_w'] / 2 - p['lcd_fpc_left']
    fpc_x0 = fpc_x1 - p['lcd_fpc_w']
    tail_x0 = -p['tp_w'] / 2 + p['tp_tail_right']
    tail_x1 = tail_x0 + p['tp_tail_w']

    # video board
    vb_x0 = (fpc_x0 + fpc_x1) / 2 - p['vb_con1_x']
    # the flex rises from the back of the LCD to the connector: the board sits as
    # far as the free length of the flex (minus contact tip and slack) can reach
    fpc_rise = p['pad_t'] + p['mid_t'] + p['so_h'] + p['pcb_t'] + p['fpc_conn_h']

    def fpc_reach(length):
        return ((length - p['fpc_contact'] - p['fpc_slack']) ** 2 - fpc_rise ** 2) ** 0.5

    vb_y0 = lcd_bot + fpc_reach(p['lcd_fpc_len'])
    vb_y1 = vb_y0 + p['vb_h']
    vb_holes = [(vb_x0 + u, vb_y0 + v) for u, v in p['vb_holes']]
    hdmi_x = vb_x0 + p['vb_hdmi_x']
    dc_x = vb_x0 + p['vb_dc_x']
    hdmi_z = z_pcb + p['hdmi_zc']
    dc_z = z_pcb + p['dc_zc']

    # touch board: flex pointing down, micro-USB facing -X
    ctp_x1 = (tail_x0 + tail_x1) / 2 + p['ctp_w'] / 2
    ctp_x0 = ctp_x1 - p['ctp_w']
    ctp_y0 = lcd_bot + fpc_reach(p['tp_tail_len'])
    ctp_y1 = ctp_y0 + p['ctp_l']
    h = p['ctp_hole']
    ctp_holes = [(ctp_x1 - h, ctp_y1 - h), (ctp_x0 + h, ctp_y0 + h)]
    usb_y = ctp_y1 - p['ctp_usb']
    usb_z = z_pcb + p['usb_zc']

    # OSD keypad on the cover, LED end down, buttons on the outer side
    kp_y0 = cy - p['kp_l'] / 2
    kp_bx = p['kp_x'] + p['kp_w'] / 2 - p['kp_row']
    kp_btn = [(kp_bx, kp_y0 + s) for s in p['kp_btn']]
    kp_holes = [(kp_bx, kp_y0 + s) for s in p['kp_holes']]
    # the keypad-to-cover distance follows from the pin length
    kp_off = p['pin_len'] - p['back_t'] + p['kp_sw_h'] - p['key_float']
    z_kp = z_in - kp_off                # component face of the keypad
    ky0, ky1 = kp_btn[0][1], kp_btn[-1][1]
    fdx = p['frame_screw_dx']
    frame_screws = [(kp_bx + sx * fdx, y) for sx in (-1, 1)
                    for y in (ky0 - 8.0, kp_y0 + 44.0, ky1 + 8.0)]

    def nut_slot(x, y, dx, dy, z0, reach):
        # slot through which the nut slides in sideways, from (x, y) towards (dx, dy)
        a = p['nut_af'] / 2
        xa, xb = sorted((x - dx * 3.3 - abs(dy) * a, x + dx * reach + abs(dy) * a))
        ya, yb = sorted((y - dy * 3.3 - abs(dx) * a, y + dy * reach + abs(dx) * a))
        return box(xa, xb, ya, yb, z0, z0 + p['nut_h'])

    # chassis screws: (x, y, direction towards the pocket wall). The nut slides in
    # through the pocket wall and is trapped once the LCD is fitted.
    d_s = p['ledge'] / 2
    mid_screws = ([(px0 - d_s, y, 1, 0) for y in (py1 - 10.0, py0 + 12.0)] +
                  [(px1 + d_s, y, -1, 0) for y in (py1 - 10.0, py0 + 12.0)] +
                  [(x, py1 + d_s, 0, -1) for x in (-62.0, 18.0, 66.0)] +
                  [(x, py0 - d_s, 0, 1) for x in (-19.0, 66.0)])
    z_mnut = z_ledge - p['nut_roof'] - p['nut_h']

    vesa = [(cx + sx * p['vesa'] / 2, cy + sy * p['vesa'] / 2) for sx in (-1, 1) for sy in (-1, 1)]

    # ---------------- front bezel ----------------
    front = ring(d_out, 0, z_split)
    for x, yw, sgn in lug_defs:
        add(front, lug_body(x, yw, sgn, 0, z_split))
    cut(front, box(wx0, wx1, wy0, wy1, -1, p['lip_t'] + 1))
    cut(front, box(px0, px1, py0, py1, p['lip_t'], z_split + 1))
    cut(front, ring(d_rec, z_ledge, z_split + 1))
    # stops for the LCD bottom edge, clear of the flex cable zones
    for bx0, bx1 in ((24.4, 44.4), (-43.6, -23.6)):
        add(front, box(bx0, bx1, py0 - 0.5, lcd_bot - p['fit'], p['lip_t'] - 0.5, z_glass + stack))
    groove = ring(d_gc + p['groove_w'] / 2, z_split - p['groove_d'], z_split + 1)
    cut(groove, ring(d_gc - p['groove_w'] / 2, z_split - p['groove_d'] - 1, z_split + 2))
    cut(front, groove)
    # closure: M3x20 screw through the cover, nut in a slot open at the tip of each column
    for x, yw, sgn in lug_defs:
        yc = yw + sgn * p['lug_out']
        cut(front, cyl_z(x, yc, p['lug_nut_z'] - 1.0, z_split + 1, p['m3_clear']))
        cut(front, nut_slot(x, yc, 0, sgn, p['lug_nut_z'], p['lug_d'] / 2 + 1.0))
    # chassis: M3x10 screw, nut in a slot open towards the LCD pocket
    for x, y, dx, dy in mid_screws:
        cut(front, cyl_z(x, y, z_mnut - 1.4, z_ledge + 1, p['m3_clear']))
        cut(front, nut_slot(x, y, dx, dy, z_mnut, d_s + 0.5))
    # sun hood: (x, y, direction towards the outer edge the nut slides in from)
    hood_side = [(cx + sx * p['hood_side_dx'], cy + sy * p['hood_side_dy'], sx, 0)
                 for sx in (-1, 1) for sy in (-1, 1)]
    hood_top = [(cx + sx * p['hood_top_dx'], cy + p['hood_top_dy'], 0, 1) for sx in (-1, 1)]
    hood_bot = [(x, 2 * cy - y, 0, -1) for x, y, _dx, _dy in hood_top]
    for x, y, dx, dy in hood_side + hood_top + hood_bot:
        cut(front, cyl_z(x, y, -1, p['hood_hole_z'], p['m3_clear']))
        edge = (ax1 + d_out - x) if dx > 0 else (x - (ax0 - d_out)) if dx < 0 else \
               (ay1 + d_out - y) if dy > 0 else (y - (ay0 - d_out))
        cut(front, nut_slot(x, y, dx, dy, p['hood_nut_z'], edge + 1.0))
    g['Front bezel'] = front

    # ---------------- chassis ----------------
    mid = ring(d_mid, z_ledge, z_split)
    z_so = z_split + p['so_h']
    # boards: M3x10 screw from above, nut in a hex pocket under the chassis,
    # recessed 1.6 mm so the screw tip cannot reach the LCD
    for x, y in vb_holes + ctp_holes:
        add(mid, cyl_z(x, y, z_split - 0.5, z_split + 2.5, 9.5))
        add(mid, cyl_z(x, y, z_split - 0.5, z_so, 7.0))
        cut(mid, cyl_z(x, y, z_ledge - 1, z_so + 1, p['m3_clear']))
        cut(mid, hexprism(x, y, z_ledge - 1, z_ledge + 4.0, p['nut_af']))
    for x, y, dx, dy in mid_screws:
        add(mid, cyl_z(x, y, z_split - 0.5, z_split + p['chassis_collar'], 7.0))
        cut(mid, cyl_z(x, y, z_ledge - 1, z_split + p['chassis_collar'] + 1, p['m3_clear']))
    for sx0, sx1 in ((fpc_x0 - 3, fpc_x1 + 3), (tail_x0 - 3, tail_x1 + 3)):
        cut(mid, box(sx0, sx1, py0, lcd_bot + p['fpc_slot'], z_ledge - 1, z_split + 1))
    g['Chassis'] = mid

    # ---------------- rear cover ----------------
    back = ring(d_out, z_split, T)
    for x, yw, sgn in lug_defs:
        add(back, lug_body(x, yw, sgn, z_split, T))
    cut(back, ring(d_in, z_split - 1, z_in))
    tongue = ring(d_gc + p['tongue_w'] / 2, z_split - p['tongue_h'], z_split + 0.5)
    cut(tongue, ring(d_gc - p['tongue_w'] / 2, z_split - p['tongue_h'] - 1, z_split + 1))
    add(back, tongue)
    for x, y in vesa:
        add(back, cyl_z(x, y, T - p['vesa_ins_depth'] - 1.0, z_in + 0.5, p['vesa_boss_d']))
        cut(back, cyl_z(x, y, T - p['vesa_ins_depth'], T + 1, p['vesa_ins_d']))
    for x, y in kp_holes:
        add(back, cyl_z(x, y, z_kp, z_in + 0.5, 8.0))
        cut(back, cyl_z(x, y, z_kp - 1, z_kp + 9.5, p['ins_d']))
    for x, y in kp_btn:
        cut(back, cyl_z(x, y, z_in - 1, T + 1, p['pin_hole_d']))
    for x, y in frame_screws:
        add(back, cyl_z(x, y, z_in - p['frame_boss_h'], z_in + 0.5, 8.0))
        cut(back, cyl_z(x, y, z_in - p['frame_boss_h'] + 1.0, T + 1, p['ins_d']))
    for x, y in lugs:
        cut(back, cyl_z(x, y, z_split - 1, T + 1, p['m3_clear']))
        cut(back, cyl_z(x, y, z_split + p['m3_grip'], T + 1, p['m3_head']))
    hw, hh = p['hdmi_open'][0] / 2, p['hdmi_open'][1] / 2
    uw, uh = p['usb_open'][0] / 2, p['usb_open'][1] / 2
    oy1 = ay1 + d_out
    ox0 = ax0 - d_out
    cut(back, box(hdmi_x - hw, hdmi_x + hw, ay1 + d_in - 1, oy1 + 1, hdmi_z - hh, hdmi_z + hh))
    cut(back, cyl((dc_x, ay1 + d_in - 1, dc_z), (dc_x, oy1 + 1, dc_z), p['dc_open']))
    cut(back, box(ox0 - 1, ax0 - d_in + 1, usb_y - uw, usb_y + uw, usb_z - uh, usb_z + uh))
    g['Rear cover'] = back

    # ---------------- TPU port caps ----------------
    # each cap is tethered to the case by a thin strap with an eyelet and an M3
    # screw, which threads into a blind hole reinforced on the inside of the wall
    m, ct, cp = 1.5, p['cap_t'], p['cap_plug']
    sl, sw, st, ed = p['tether_len'], p['tether_w'], p['tether_t'], p['eye_d']
    rib, hole = p['tether_rib'], p['tether_hole']
    dr = p['dc_open'] / 2

    z0c, z1c = min(hdmi_z - hh, dc_z - dr) - m, max(hdmi_z + hh, dc_z + dr) + m
    # top cap: L-shaped tether that drops to the edge of the front bezel and runs
    # under the cap to the eyelet, so it stays clear of the screw columns
    x_a, x_end = hdmi_x - hw - m, dc_x + dr + m
    tw, te = p['tether_top_w'], p['eye_top_d']
    xe, ze = x_a + p['tether_top_len'], z_split / 2
    y_s0, y_s1 = oy1 + ct - st, oy1 + ct
    cap = box(x_a, x_end, oy1, oy1 + ct, z0c, z1c)
    add(cap, box(hdmi_x - hw + 0.1, hdmi_x + hw - 0.1, oy1 - cp, oy1 + 0.5, hdmi_z - hh + 0.1, hdmi_z + hh - 0.1))
    add(cap, cyl((dc_x, oy1 - cp, dc_z), (dc_x, oy1 + 0.5, dc_z), p['dc_open'] - 0.2))
    add(cap, box(x_a, x_a + tw, y_s0, y_s1, ze - tw / 2, z0c + 0.5))
    add(cap, box(x_a, xe, y_s0, y_s1, ze - tw / 2, ze + tw / 2))
    add(cap, cyl((xe, oy1, ze), (xe, oy1 + ct, ze), te))
    cut(cap, cyl((xe, oy1 - 1, ze), (xe, oy1 + ct + 1, ze), p['m3_clear']))
    g['HDMI+DC port cap (TPU)'] = cap
    cut(front, cyl((xe, oy1 - hole, ze), (xe, oy1 + 1, ze), p['ins_d']))

    y_end = usb_y - uw - m
    ye = y_end - sl - ed / 2
    cap = box(ox0 - ct, ox0, y_end, usb_y + uw + m, usb_z - uh - m, usb_z + uh + m)
    add(cap, box(ox0 - 0.5, ox0 + cp, usb_y - uw + 0.1, usb_y + uw - 0.1, usb_z - uh + 0.1, usb_z + uh - 0.1))
    add(cap, box(ox0 - ct, ox0 - ct + st, ye, y_end + 0.5, usb_z - sw / 2, usb_z + sw / 2))
    add(cap, cyl((ox0 - ct, ye, usb_z), (ox0, ye, usb_z), ed))
    cut(cap, cyl((ox0 - ct - 1, ye, usb_z), (ox0 + 1, ye, usb_z), p['m3_clear']))
    g['USB port cap (TPU)'] = cap
    add(back, box(ax0 - d_in - 0.5, ax0 - d_in + rib, ye - 4.0, ye + 4.0, usb_z - 4.0, z_in + 0.5))
    cut(back, cyl((ox0 - 1, ye, usb_z), (ox0 + hole, ye, usb_z), p['ins_d']))

    # TPU keypad strip: thin flange with a sealing bead, body with one chamber per
    # button and a raised marker on each pin axis
    cav_h = p['key_float'] + p['pin_head_h'] + 0.1
    z_roof = T + cav_h + p['key_roof']
    keys = box(kp_bx - 9.0, kp_bx + 9.0, ky0 - 9.0, ky1 + 9.0, T, T + p['key_flange'])
    add(keys, box(kp_bx - 6.5, kp_bx + 6.5, ky0 - 6.5, ky1 + 6.5, T, z_roof))
    z_bead = T + p['key_flange'] + p['key_bead_h']
    bead = box(kp_bx - 8.5, kp_bx + 8.5, ky0 - 8.5, ky1 + 8.5, T + p['key_flange'] - 0.2, z_bead)
    bw = p['key_bead_w']
    cut(bead, box(kp_bx - 8.5 + bw, kp_bx + 8.5 - bw, ky0 - 8.5 + bw, ky1 + 8.5 - bw, T, z_bead + 1))
    add(keys, bead)
    for x, y in kp_btn:
        cut(keys, cyl_z(x, y, T - 1, T + cav_h, p['key_cav_d']))
        add(keys, cyl_z(x, y, z_roof - 0.2, z_roof + p['key_nub_h'], p['key_nub_d']))
    g['Keypad strip (TPU)'] = keys

    # frame that clamps the keypad strip against the cover
    fw = p['frame_half_w']
    z_fr = T + p['frame_t']
    frame = rrect(kp_bx - fw, kp_bx + fw, ky0 - 13.0, ky1 + 13.0, T, z_fr, 4.0)
    cut(frame, box(kp_bx - 9.2, kp_bx + 9.2, ky0 - 9.2, ky1 + 9.2, T - 1, T + p['frame_pocket']))
    cut(frame, box(kp_bx - 6.8, kp_bx + 6.8, ky0 - 6.8, ky1 + 6.8, T - 1, z_fr + 1))
    for x, y in frame_screws:
        cut(frame, cyl_z(x, y, T - 1, z_fr + 1, p['m3_clear']))
        cut(frame, cyl_z(x, y, T + 1.5, z_fr + 1, 6.2))
    g['Keypad frame'] = frame

    # ---------------- sun hood ----------------
    hm, hd, hwl, hft = p['hood_margin'], p['hood_depth'], p['hood_wall'], p['hood_flange_t']
    hx0, hx1, hy0, hy1 = wx0 - hm, wx1 + hm, wy0 - hm, wy1 + hm     # inner faces
    # the flange follows the bezel outline, inset evenly all round, so its corners
    # are concentric with those of the case
    ins, r_in = p['hood_inset'], p['hood_corner_r']
    hood = rrect(ax0 - d_out + ins, ax1 + d_out - ins, ay0 - d_out + ins, ay1 + d_out - ins,
                 -hft, 0, p['r_out'] - ins)
    cut(hood, rrect(hx0, hx1, hy0 - 40.0, hy1, -hft - 1, 1, r_in))
    # roof and side wings as a single shell, with rounded top corners
    shell = rrect(hx0 - hwl, hx1 + hwl, hy0 - 40.0, hy1 + hwl, -hd, 0, r_in + hwl)
    cut(shell, rrect(hx0, hx1, hy0 - 50.0, hy1, -hd - 1, 1, r_in))
    # wedge-shaped wings: deep at the top, short at the bottom. The cut starts at
    # the inner face of the roof so it does not touch it.
    z_top, z_bot = -hd, -p['hood_depth_bottom']
    ly, lz = hy0 - hy1, z_bot - z_top
    ll = math.hypot(ly, lz)
    uy, uz = ly / ll, lz / ll
    ny, nz = -uz, uy
    obb = adsk.core.OrientedBoundingBox3D.create(
        pt(cx, (hy1 + hy0) / 2 + ny * 50.0, (z_top + z_bot) / 2 + nz * 50.0),
        adsk.core.Vector3D.create(0, uy, uz), adsk.core.Vector3D.create(0, ny, nz),
        40.0, 10.0, 40.0)
    cut(shell, tbm.createBox(obb))
    add(hood, shell)
    cut(hood, box(ax0 - d_out - 1, ax1 + d_out + 1, hy0 - 60.0, hy0, -hd - 1, 1))
    for x, y, _dx, _dy in hood_side + hood_top:
        cut(hood, cyl_z(x, y, -hft - 1, 1, p['m3_clear']))
    g['Sun hood'] = hood

    # ---------------- reference: kit components ----------------
    ref = {}
    ref['LCD + touch glass'] = box(-p['lcd_w'] / 2, p['lcd_w'] / 2, lcd_bot, -lcd_bot, z_glass, z_glass + stack)
    vb = box(vb_x0, vb_x0 + p['vb_w'], vb_y0, vb_y1, z_so, z_pcb)
    add(vb, box(hdmi_x - 7.5, hdmi_x + 7.5, vb_y1 - 10.5, vb_y1 + 1.0, z_pcb, z_pcb + 6.2))
    add(vb, box(dc_x - 4.5, dc_x + 4.5, vb_y1 - 11.0, vb_y1 + 3.0, z_pcb, z_pcb + 11.0))
    vx = vb_x0 + p['vb_vga_x']
    add(vb, box(vx - 15.5, vx + 15.5, vb_y1 - 10.0, vb_y1 + 6.0, z_pcb, z_pcb + 12.5))
    rx = vb_x0 + p['vb_rca_x']
    add(vb, box(rx - 5.0, rx + 5.0, vb_y1 - 8.0, vb_y1 + 4.0, z_pcb, z_pcb + 13.0))
    ref['Video board'] = vb
    ctp = box(ctp_x0, ctp_x1, ctp_y0, ctp_y1, z_so, z_pcb)
    add(ctp, box(ctp_x0 - 0.5, ctp_x0 + 5.0, usb_y - 4.0, usb_y + 4.0, z_pcb, z_pcb + 2.8))
    ref['Touch board'] = ctp
    kp = box(p['kp_x'] - p['kp_w'] / 2, p['kp_x'] + p['kp_w'] / 2, kp_y0, kp_y0 + p['kp_l'], z_kp - p['pcb_t'], z_kp)
    for x, y in kp_btn:
        add(kp, box(x - 3, x + 3, y - 3, y + 3, z_kp, z_kp + p['kp_sw_h']))
    ref['OSD keypad'] = kp
    z_sw = z_kp + p['kp_sw_h']
    pins = None
    for x, y in kp_btn:
        pin = cyl_z(x, y, z_sw, z_sw + p['pin_len'], p['pin_d'])
        add(pin, cyl_z(x, y, z_sw + p['pin_len'], z_sw + p['pin_len'] + p['pin_head_h'], p['pin_head_d']))
        if pins is None:
            pins = pin
        else:
            add(pins, pin)
    ref['Key pins (5x M3x16)'] = pins

    # fit test: just the lip, the window and 4 mm of pocket, with a thin wall.
    # Confirms the LCD size and the window position with little material.
    tw_, th_ = p['test_wall'], p['lip_t'] + p['test_depth']
    test = box(px0 - tw_, px1 + tw_, py0 - tw_, py1 + tw_, 0, th_)
    cut(test, box(wx0, wx1, wy0, wy1, -1, p['lip_t'] + 1))
    cut(test, box(px0, px1, py0, py1, p['lip_t'], th_ + 1))
    for bx0, bx1 in ((24.4, 44.4), (-43.6, -23.6)):
        add(test, box(bx0, bx1, py0 - 0.5, lcd_bot - p['fit'], p['lip_t'] - 0.5, th_))
    # hardware test: a block as thick as the bezel with one of each hole or slot
    # used in the case, to tune clearances in the final material
    cw, cd = 40.0, 24.0
    coupon = box(0, cw, 0, cd, 0, z_split)
    cut(coupon, cyl_z(6.0, 6.0, p['lug_nut_z'] - 1.0, z_split + 1, p['m3_clear']))     # nut slot
    cut(coupon, nut_slot(6.0, 6.0, 0, -1, p['lug_nut_z'], 7.0))
    cut(coupon, cyl_z(16.0, 8.0, -1, z_split + 1, p['m3_clear']))                      # hex nut pocket
    cut(coupon, hexprism(16.0, 8.0, -1, 4.0, p['nut_af']))
    cut(coupon, cyl_z(25.0, 8.0, z_split - 7.0, z_split + 1, p['ins_d']))              # M3 insert
    cut(coupon, cyl_z(34.0, 8.0, -1, p['vesa_ins_depth'], p['vesa_ins_d']))            # M4 insert
    cut(coupon, box(-1, cw + 1, 17.8, 17.8 + p['groove_w'], z_split - p['groove_d'], z_split + 1))
    # port wall test: only the top wall of the cover (with its three columns, so it
    # bolts on in place) and the stretch of side wall with the micro-USB, no back
    region = box(ax0 - d_out - 20, ax1 + d_out + 20, ay1 + d_in, ay1 + d_out + 20, z_split - 3, z_in)
    add(region, box(ax0 - d_out - 20, ax0 - d_in, usb_y - 18.0, ay1 + d_out + 20, z_split - 3, z_in))
    ports = tbm.copy(back)
    tbm.booleanOperation(ports, region, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    extras = {'LCD pocket test': test, 'Hardware test': coupon, 'Port wall test': ports}

    info = dict(T=T, z_split=z_split, z_in=z_in, z_pcb=z_pcb, cy=cy,
                width=(ax1 - ax0) + 2 * d_out, height=(ay1 - ay0) + 2 * d_lug + p['lug_d'],
                bezel=dict(x_neg=wx0 - (ax0 - d_out), x_pos=(ax1 + d_out) - wx1,
                           bottom=wy0 - (ay0 - d_out), top=(ay1 + d_out) - wy1),
                hdmi=(hdmi_x, hdmi_z), dc=(dc_x, dc_z), usb=(usb_y, usb_z),
                vb_y0=vb_y0 - lcd_bot, ctp_y0=ctp_y0 - lcd_bot, fpc_rise=fpc_rise, kp_off=kp_off,
                hdmi_recess=(ay1 + d_out) - (vb_y1 + 1.0), usb_recess=ctp_x0 - (ax0 - d_out))
    return g, ref, info, extras


def planar_face_at(body, z_mm):
    best = None
    for f in body.faces:
        if f.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        bb = f.boundingBox
        if abs(bb.minPoint.z * 10 - z_mm) < 1e-3 and abs(bb.maxPoint.z * 10 - z_mm) < 1e-3:
            if best is None or f.area > best.area:
                best = f
    return best


def chamfer_loop(comp, z_mm, dist_mm, outer):
    face = planar_face_at(comp.bRepBodies.item(0), z_mm)
    for loop in face.loops:
        if loop.isOuter != outer:
            continue
        # of the inner loops only the window matters, not the holes
        if not outer and loop.edges.count != 4:
            continue
        edges = adsk.core.ObjectCollection.create()
        for e in loop.edges:
            edges.add(e)
        cf = comp.features.chamferFeatures
        inp = cf.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, adsk.core.ValueInput.createByReal(dist_mm / 10.0), True)
        cf.add(inp)
        return


def add_component(root, name, temp_body, parametric):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    if parametric:
        base = comp.features.baseFeatures.add()
        base.startEdit()
        comp.bRepBodies.add(temp_body, base)
        base.finishEdit()
    else:
        comp.bRepBodies.add(temp_body)
    comp.bRepBodies.item(0).name = name
    return occ


def snapshot(app, name, eye, up=(0, 1, 0), target=(0, 0, 2)):
    vp = app.activeViewport
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.target = adsk.core.Point3D.create(*target)
    cam.eye = adsk.core.Point3D.create(*eye)
    cam.upVector = adsk.core.Vector3D.create(*up)
    cam.isFitView = True
    vp.camera = cam
    vp.fit()
    adsk.doEvents()
    vp.refresh()
    adsk.doEvents()
    vp.saveAsImageFile(os.path.join(OUT, name), 1600, 1100)


# rotation (axis, degrees) that puts each part in its print orientation: the face
# that sits on the bed ends up at Z = 0, with no supports needed
PRINT_ROT = {
    'Rear cover': ((1, 0, 0), 180),          # back on the bed, opening up
    'Sun hood': ((1, 0, 0), 180),             # flange on the bed
    'Keypad frame': ((1, 0, 0), 180),          # outer face on the bed
    'HDMI+DC port cap (TPU)': ((1, 0, 0), -90),    # outer face on the bed, plugs up
    'USB port cap (TPU)': ((0, 1, 0), -90),
    'Port wall test': ((1, 0, 0), 180),
}


def print_oriented(name, body):
    b = tbm.copy(body)
    rot = PRINT_ROT.get(name)
    if rot:
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(rot[1]), adsk.core.Vector3D.create(*rot[0]), adsk.core.Point3D.create(0, 0, 0))
        tbm.transform(b, m)
    bb = b.boundingBox
    t = adsk.core.Matrix3D.create()
    t.translation = adsk.core.Vector3D.create(-(bb.minPoint.x + bb.maxPoint.x) / 2,
                                               -(bb.minPoint.y + bb.maxPoint.y) / 2, -bb.minPoint.z)
    tbm.transform(b, t)
    return b


def export_stls(app, jobs):
    # exports [(name, body, file)] in print orientation from a temporary document,
    # without touching the main document
    tdoc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    tdes = adsk.fusion.Design.cast(app.activeProduct)
    tdes.designType = adsk.fusion.DesignTypes.DirectDesignType
    em = tdes.exportManager
    out = []
    for name, body, fname in jobs:
        tbody = tdes.rootComponent.bRepBodies.add(print_oriented(name, body))
        opts = em.createSTLExportOptions(tbody, os.path.join(OUT, fname))
        opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(opts)
        bb = tbody.boundingBox
        out.append('%s: %.1f x %.1f x %.1f mm, %.1f cm3' % (
            fname, (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10, tbody.volume))
        tbody.deleteMe()
    tdoc.close(False)
    return out


def run(context):
    global tbm
    app = adsk.core.Application.get()
    os.makedirs(OUT, exist_ok=True)
    try:
        tbm = adsk.fusion.TemporaryBRepManager.get()
        parts, ref, info, extras = build()
        log('outer dimensions (mm): %.1f x %.1f x %.1f' % (info['width'], info['height'], info['T']))
        log('info: %r' % (info,))

        # if the active document is already the enclosure, rebuild in it; otherwise create a new one
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design and app.activeDocument.name.startswith('Rugged Monitor'):
            old = design.rootComponent.occurrences
            for occ in [old.item(i) for i in range(old.count)]:
                occ.deleteMe()
            log('rebuilt in document %s' % app.activeDocument.name)
        else:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)
        # a "Part" design accepts only one component
        try:
            design.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        except Exception:
            log('designIntent not changed:\n' + traceback.format_exc())
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        parametric = design.designType == adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        occs = {}
        for name, body in parts.items():
            occs[name] = add_component(root, name, body, parametric)
            b = occs[name].component.bRepBodies.item(0)
            bb = b.boundingBox
            log('%s: volume %.1f cm3, %d lump(s), bbox %.1f x %.1f x %.1f mm' % (
                name, b.volume, b.lumps.count,
                (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
                (bb.maxPoint.z - bb.minPoint.z) * 10))

        ref_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        ref_occ.component.name = 'EP-0084 kit (reference)'
        for name, body in ref.items():
            rc = ref_occ.component
            if parametric:
                base = rc.features.baseFeatures.add()
                base.startEdit()
                rc.bRepBodies.add(body, base)
                base.finishEdit()
            else:
                rc.bRepBodies.add(body)
            rc.bRepBodies.item(rc.bRepBodies.count - 1).name = name

        if parametric:
            for name, z, dist, outer in (('Front bezel', 0.0, P['chamfer'], True),
                                         ('Front bezel', 0.0, P['win_chamfer'], False),
                                         ('Rear cover', info['T'], P['chamfer'], True)):
                try:
                    chamfer_loop(occs[name].component, z, dist, outer)
                except Exception:
                    log('chamfer failed on %s:\n%s' % (name, traceback.format_exc()))

        # interferences between printed parts and kit components
        try:
            bodies = adsk.core.ObjectCollection.create()
            for name in ('Front bezel', 'Chassis', 'Rear cover', 'Keypad frame', 'Keypad strip (TPU)',
                         'Sun hood'):
                bodies.add(occs[name].bRepBodies.item(0))
            for i in range(ref_occ.bRepBodies.count):
                bodies.add(ref_occ.bRepBodies.item(i))
            res = design.analyzeInterference(design.createInterferenceInput(bodies))
            log('interferences: %d' % res.count)
            for r in res:
                log('  %s x %s: %.3f cm3' % (r.entityOne.name, r.entityTwo.name, r.interferenceBody.volume))
        except Exception:
            log('interference analysis failed:\n' + traceback.format_exc())

        em = design.exportManager
        em.execute(em.createSTEPExportOptions(os.path.join(OUT, 'rugged-monitor.step'), root))
        files = {'Front bezel': 'front-bezel', 'Chassis': 'chassis', 'Rear cover': 'rear-cover',
                 'HDMI+DC port cap (TPU)': 'port-cap-hdmi-dc-tpu', 'USB port cap (TPU)': 'port-cap-usb-tpu',
                 'Keypad strip (TPU)': 'keypad-strip-tpu', 'Keypad frame': 'keypad-frame',
                 'Sun hood': 'sun-hood'}
        # copies of the document bodies (chamfers included) to export at the end
        jobs = [(name, tbm.copy(occs[name].component.bRepBodies.item(0)), fn + '.stl')
                for name, fn in files.items()]
        jobs += [('LCD pocket test', extras['LCD pocket test'], 'test-lcd-pocket.stl'),
                 ('Hardware test', extras['Hardware test'], 'test-hardware.stl'),
                 ('Port wall test', extras['Port wall test'], 'test-port-walls.stl')]

        def show(**vis):
            for name, occ in occs.items():
                occ.isLightBulbOn = vis.get(name, vis.get('default', True))
            ref_occ.isLightBulbOn = vis.get('ref', True)

        cz = info['T'] / 20.0
        show(**{'Sun hood': False})
        snapshot(app, '1-front.png', (-18, 12, -30), target=(0, 0, cz))
        show()
        snapshot(app, '11-sun-hood.png', (-22, 16, -30), target=(0, 0, cz))
        snapshot(app, '2-rear.png', (18, 14, 30), target=(0, 0, cz))
        show(**{'Rear cover': False, 'HDMI+DC port cap (TPU)': False, 'USB port cap (TPU)': False, 'Keypad strip (TPU)': False,
                'Keypad frame': False})
        snapshot(app, '3-interior.png', (10, 14, 30), target=(0, 0, cz))
        snapshot(app, '4-interior-top.png', (0, 0.01, 40), target=(0, 0, cz))
        show(default=False, **{'Rear cover': True}, ref=False)
        snapshot(app, '5-rear-cover-inside.png', (-12, 14, -30), target=(0, 0, cz))
        show(default=False, **{'Front bezel': True}, ref=False)
        snapshot(app, '6-front-bezel-inside.png', (10, 14, 30), target=(0, 0, cz))
        show(default=False, **{'Front bezel': True, 'Rear cover': True, 'HDMI+DC port cap (TPU)': True,
                               'USB port cap (TPU)': True}, ref=False)
        snapshot(app, '9-port-caps.png', (-22, 26, 16), up=(0, 0, 1), target=(0, 0, cz))
        show(default=False, **{'Chassis': True}, ref=False)
        snapshot(app, '10-chassis-underside.png', (14, -16, -30), target=(0, 0, cz))
        show(default=False, **{'Keypad strip (TPU)': True, 'Keypad frame': True}, ref=False)
        snapshot(app, '7-keypad-frame.png', (20, -14, 30), target=(7, 0, cz))
        show(default=False, **{'Keypad strip (TPU)': True}, ref=False)
        snapshot(app, '8-keypad-strip-underside.png', (20, -14, -30), target=(7, 0, cz))
        show()
        snapshot(app, '2-rear.png', (18, 14, 30), target=(0, 0, cz))
        log('STL files in print orientation:')
        for line in export_stls(app, jobs):
            log('  ' + line)
        log('OK')
    except Exception:
        log('ERROR:\n' + traceback.format_exc())
    finally:
        with open(os.path.join(OUT, 'build.log'), 'w') as f:
            f.write('\n'.join(log_lines) + '\n')
        log_lines.clear()

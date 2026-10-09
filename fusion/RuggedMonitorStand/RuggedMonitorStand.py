# Desk stand for the rugged enclosure of the 52Pi EP-0084 display.
#
# Fusion script: Utilities > Scripts and Add-Ins > RuggedMonitorStand > Run.
# Rebuilds the "Desk Stand" document if it is active (otherwise creates a new
# one) with the two printed parts (base and tilt bracket), the enclosure and the M4
# hardware as reference, checks that the enclosure and the bracket clear the base over
# the whole tilt range, and writes the STL files, the STEP file and the images to out/.
#
# The enclosure comes from RuggedMonitor.py (same repository), so the stand follows
# any change to its dimensions.
#
# Axes: the same as the enclosure (REAR view): X to the right, Y up, Z = 0 at the
# front face of the bezel, increasing towards the back. The enclosure is drawn
# upright; its tilt is a rotation about the pivot axis (parallel to X). In the
# stand's side-view coordinates "a" is distance towards the back (+Z) and "b" is
# height (+Y), both measured from the pivot axis.
#
# How it works: the bracket (plate + two side walls) bolts to the four M4 inserts of
# the rear cover and rotates about a bolt through the walls and the two arms of the
# base. A second bolt per side runs in an arc slot of the arm and clamps the wall
# against the arm to hold the angle.

import importlib
import math
import os
import sys
import traceback

import adsk.core
import adsk.fusion

P = dict(
    # --- bracket: bolts to the four M4 inserts of the rear cover ---
    vesa=75.0,
    plate_h=90.0, plate_t=6.0, plate_r=6.0,
    screw_hole_d=4.5,
    screw_head_d=8.2, screw_head_depth=2.6,   # M4x8 button head (ISO 7380): 7.6 x 2.2
    plate_in_w=90.0,        # distance between the inner faces of the walls
    wall_t=6.0,             # side walls, which carry the pivot and the lock bolt
    # --- pivot and tilt ---
    pivot_e=18.0,           # pivot axis behind the back face of the cover
    pivot_u=-37.5,          # pivot position from the VESA centre (the lower VESA row)
    pivot_h=48.0,           # pivot axis above the table
    tilt_max=60.0,          # largest tilt back from vertical
    lock_r=30.0,            # radius of the lock bolt about the pivot
    wall_boss_r=10.5, wall_lock_r=7.5,
    # --- M4 hardware: hex head bolts, head held in a pocket of the wall ---
    bolt_hole_d=4.5, hex_af=7.3, hex_depth=3.0,
    bolt_len=20.0, bolt_d=4.0, head_af=7.0, head_h=2.8,
    washer_d=9.0, washer_t=0.8, nut_d=7.5, nut_h=5.0,       # nylon lock nut on the pivot
    wing_body_d=8.0, wing_h=8.0, wing_span=20.0, wing_t=3.0,  # wing nut on the lock bolt
    # --- arms (fixed to the base) ---
    arm_t=7.0, arm_gap=0.6, arm_front=14.0, arm_rear=45.0, arm_boss_r=10.5,
    slot_w=4.6, slot_step=1.0,
    # --- base ---
    base_w=150.0, base_front=75.0, base_rear=85.0, base_t=5.0, base_r=12.0,
    foot_d=10.5, foot_depth=1.0, foot_inset=16.0,      # recess for a stick-on rubber foot
    # --- checks and views ---
    view_tilt=30.0, tilt_step=5.0,
    min_clear=3.0,          # warn when the enclosure gets closer than this to the base
)

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'out')

MON_PARTS = ('Front bezel', 'Chassis', 'Rear cover', 'HDMI+DC port cap (TPU)', 'USB port cap (TPU)',
             'Keypad strip (TPU)', 'Keypad frame', 'Sun hood')

tbm = None
rm = None
log_lines = []


def log(msg):
    log_lines.append(str(msg))


def pt(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def vec(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


def box(x0, x1, y0, y1, z0, z1):
    return rm.box(x0, x1, y0, y1, z0, z1)


def cyl(p0, p1, d):
    return rm.cyl(p0, p1, d)


def add(target, tool):
    rm.add(target, tool)


def cut(target, tool):
    rm.cut(target, tool)


def rot_x(body, deg, y, z):
    # rotates a copy of the body about the axis parallel to X through (y, z); positive
    # angles tip the top of the enclosure towards the back
    b = tbm.copy(body)
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(deg), vec(1, 0, 0), pt(0, y, z))
    tbm.transform(b, m)
    return b


def hex_x(x0, x1, y, z, af):
    # hexagonal prism along X, from x0 to x1, centred on (y, z)
    h = rm.hexprism(0.0, 0.0, 0.0, x1 - x0, af)
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(90), vec(0, 1, 0), adsk.core.Point3D.create(0, 0, 0))
    tbm.transform(h, m)
    t = adsk.core.Matrix3D.create()
    t.translation = vec(x0 / 10.0, y / 10.0, z / 10.0)
    tbm.transform(h, t)
    return h


def poly_prism(pts, x0, x1):
    # convex polygon extruded along X. pts are (Z, Y) vertices in counter-clockwise
    # order (Z to the right, Y up). Built from a box and one half-space cut per edge.
    zs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    body = box(x0, x1, min(ys), max(ys), min(zs), max(zs))
    big = 400.0
    for i in range(len(pts)):
        z0, y0 = pts[i]
        z1, y1 = pts[(i + 1) % len(pts)]
        ln = math.hypot(z1 - z0, y1 - y0)
        dz, dy = (z1 - z0) / ln, (y1 - y0) / ln
        nz, ny = dy, -dz        # outward normal: to the right of the edge direction
        obb = adsk.core.OrientedBoundingBox3D.create(
            pt((x0 + x1) / 2, (y0 + y1) / 2 + ny * big / 2, (z0 + z1) / 2 + nz * big / 2),
            vec(0, dy, dz), vec(0, ny, nz), big / 10.0, big / 10.0, (x1 - x0 + 20.0) / 10.0)
        cut(body, tbm.createBox(obb))
    return body


def rrect_xz(x0, x1, z0, z1, y0, y1, r):
    # rounded rectangle in the XZ plane, extruded along Y
    b = box(x0 + r, x1 - r, y0, y1, z0, z1)
    add(b, box(x0, x1, y0, y1, z0 + r, z1 - r))
    for x in (x0 + r, x1 - r):
        for z in (z0 + r, z1 - r):
            add(b, cyl((x, y0, z), (x, y1, z), 2 * r))
    return b


def build(info):
    p = P
    cx, cy, T = info['cx'], info['cy'], info['T']
    assert p['arm_front'] < p['pivot_e'] - 2.0, 'arm too close to the back of the cover'

    # pivot axis and table
    y_p = cy + p['pivot_u']
    z_p = T + p['pivot_e']
    y_b = y_p - p['pivot_h']            # top face of the base plate

    def at(a, b):
        return (z_p + a, y_p + b)       # side-view (a, b) -> (Z, Y)

    # X layout, measured from the VESA centre
    pw = p['plate_in_w'] + 2 * p['wall_t']
    xw_in = p['plate_in_w'] / 2
    xw_out = pw / 2
    xa_in = xw_out + p['arm_gap']
    xa_out = xa_in + p['arm_t']

    # lock bolt: at the start of the range (tilt 0) it sits behind and below the pivot
    # and ends straight below it at the largest tilt
    al = math.radians(p['tilt_max'])
    la, lb = p['lock_r'] * math.sin(al), -p['lock_r'] * math.cos(al)
    t_a, t_b = at(la, lb)

    # ---------------- tilt bracket ----------------
    pl_b = (cy - p['plate_h'] / 2) - y_p      # bottom edge of the plate, from the pivot
    bracket = rm.rrect(cx - pw / 2, cx + pw / 2, cy - p['plate_h'] / 2, cy + p['plate_h'] / 2,
                       T, T + p['plate_t'], p['plate_r'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * p['vesa'] / 2, cy + sy * p['vesa'] / 2
            cut(bracket, rm.cyl_z(x, y, T - 1, T + p['plate_t'] + 1, p['screw_hole_d']))
            cut(bracket, rm.cyl_z(x, y, T + p['plate_t'] - p['screw_head_depth'], T + p['plate_t'] + 1,
                                  p['screw_head_d']))
    for s in (-1, 1):
        x0, x1 = sorted((cx + s * xw_in, cx + s * xw_out))
        # wall: starts inside the plate and runs back to the pivot and the lock bolt
        tab = poly_prism([at(-p['pivot_e'] + 1.0, pl_b + 0.5), (t_a, t_b), at(0.0, p['wall_boss_r']),
                          at(-p['pivot_e'] + 1.0, p['wall_boss_r'])], x0, x1)
        add(tab, cyl((x0, y_p, z_p), (x1, y_p, z_p), 2 * p['wall_boss_r']))
        add(tab, cyl((x0, t_b, t_a), (x1, t_b, t_a), 2 * p['wall_lock_r']))
        add(bracket, tab)
        xi = cx + s * xw_in
        for y, z in ((y_p, z_p), (t_b, t_a)):
            cut(bracket, cyl((x0 - 1, y, z), (x1 + 1, y, z), p['bolt_hole_d']))
            xs = sorted((xi - s * 0.5, xi + s * p['hex_depth']))
            cut(bracket, hex_x(xs[0], xs[1], y, z, p['hex_af']))

    # ---------------- base ----------------
    base = rrect_xz(cx - p['base_w'] / 2, cx + p['base_w'] / 2, z_p - p['base_front'], z_p + p['base_rear'],
                    y_b - p['base_t'], y_b, p['base_r'])
    plate_only = tbm.copy(base)         # to measure the clearance to the table
    ab = -p['pivot_h'] - 1.0            # arms sink 1 mm into the base
    for s in (-1, 1):
        x0, x1 = sorted((cx + s * xa_in, cx + s * xa_out))
        arm = poly_prism([at(-p['arm_front'], ab), at(p['arm_rear'], ab), at(p['arm_rear'] - 5.0, -10.0),
                          at(p['arm_boss_r'], 0.0), at(-p['arm_boss_r'], 0.0)], x0, x1)
        add(arm, cyl((x0, y_p, z_p), (x1, y_p, z_p), 2 * p['arm_boss_r']))
        cut(arm, cyl((x0 - 1, y_p, z_p), (x1 + 1, y_p, z_p), p['bolt_hole_d']))
        # lock slot: an arc of overlapping cylinders about the pivot
        n = int(round(p['tilt_max'] / p['slot_step']))
        slot = None
        for i in range(n + 1):
            a_ = math.radians(p['tilt_max'] * i / n)
            z, y = at(p['lock_r'] * math.sin(a_), -p['lock_r'] * math.cos(a_))
            c = cyl((x0 - 1, y, z), (x1 + 1, y, z), p['slot_w'])
            if slot is None:
                slot = c
            else:
                add(slot, c)
        cut(arm, slot)
        add(base, arm)
    for sx in (-1, 1):
        for z in (z_p - p['base_front'] + p['foot_inset'], z_p + p['base_rear'] - p['foot_inset']):
            x = cx + sx * (p['base_w'] / 2 - p['foot_inset'])
            cut(base, cyl((x, y_b - p['base_t'] - 1, z), (x, y_b - p['base_t'] + p['foot_depth'], z), p['foot_d']))

    # ---------------- reference: M4 hardware (at tilt 0) ----------------
    hw = None
    for s in (-1, 1):
        for kind, (y, z) in (('pivot', (y_p, z_p)), ('lock', (t_b, t_a))):
            def xr(d0, d1):
                return sorted((cx + s * d0, cx + s * d1))
            x_head0 = xw_in + 0.2
            x_head1 = x_head0 + p['head_h']
            parts_hw = [hex_x(xr(x_head0, x_head1)[0], xr(x_head0, x_head1)[1], y, z, p['head_af'])]
            parts_hw.append(cyl((cx + s * x_head1, y, z), (cx + s * (x_head1 + p['bolt_len']), y, z), p['bolt_d']))
            x_w1 = xa_out + p['washer_t']
            parts_hw.append(cyl((cx + s * xa_out, y, z), (cx + s * x_w1, y, z), p['washer_d']))
            if kind == 'pivot':
                parts_hw.append(cyl((cx + s * x_w1, y, z), (cx + s * (x_w1 + p['nut_h']), y, z), p['nut_d']))
            else:
                parts_hw.append(cyl((cx + s * x_w1, y, z), (cx + s * (x_w1 + p['wing_h']), y, z), p['wing_body_d']))
                parts_hw.append(cyl((cx + s * x_w1, y, z), (cx + s * (x_w1 + p['wing_t']), y, z), p['wing_span']))
            for h_ in parts_hw:
                if hw is None:
                    hw = h_
                else:
                    add(hw, h_)

    # ---------------- hinge test pieces: one arm on a slab, one wall on a plate stub ----------------
    xs0, xs1 = cx + xa_in - 3.0, cx + xa_out + 3.0
    test_arm = tbm.copy(base)
    tbm.booleanOperation(test_arm, box(xs0, xs1, y_b - p['base_t'] - 1, y_b + p['pivot_h'] + 30.0,
                                       z_p - p['arm_front'] - 6.0, z_p + p['arm_rear'] + 6.0),
                         adsk.fusion.BooleanTypes.IntersectionBooleanType)
    test_wall = tbm.copy(bracket)
    tbm.booleanOperation(test_wall, box(cx + xw_in - 14.0, cx + xw_out + 1.0, t_b - p['wall_lock_r'] - 4.0,
                                        y_p + p['wall_boss_r'] + 4.0, T - 1, z_p + p['pivot_e'] + 60.0),
                         adsk.fusion.BooleanTypes.IntersectionBooleanType)

    parts = {'Stand base': base, 'Tilt bracket': bracket}
    info2 = dict(y_p=y_p, z_p=z_p, y_b=y_b, lock=(t_b, t_a), x_arm=(xa_in, xa_out), x_wall=(xw_in, xw_out),
                 plate=plate_only)
    return parts, hw, info2, {'Hinge test arm': test_arm, 'Hinge test wall': test_wall}


# rotation (axis, degrees) that puts each part in its print orientation: the face
# that sits on the bed ends up at Z = 0, with no supports needed
PRINT_ROT = {
    'Stand base': ((1, 0, 0), 90),     # underside on the bed, arms pointing up
    'Hinge test arm': ((1, 0, 0), 90),
    # the bracket and its test wall already have the plate face on the bed (lowest Z)
}


def print_oriented(name, body):
    b = tbm.copy(body)
    r = PRINT_ROT.get(name)
    if r:
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(r[1]), vec(*r[0]), adsk.core.Point3D.create(0, 0, 0))
        tbm.transform(b, m)
    bb = b.boundingBox
    t = adsk.core.Matrix3D.create()
    t.translation = vec(-(bb.minPoint.x + bb.maxPoint.x) / 2, -(bb.minPoint.y + bb.maxPoint.y) / 2, -bb.minPoint.z)
    tbm.transform(b, t)
    return b


def export_stls(app, jobs):
    # exports [(file, body already in print orientation)] from a temporary document,
    # without touching the main document
    tdoc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    tdes = adsk.fusion.Design.cast(app.activeProduct)
    tdes.designType = adsk.fusion.DesignTypes.DirectDesignType
    em = tdes.exportManager
    out = []
    for fname, body in jobs:
        tbody = tdes.rootComponent.bRepBodies.add(body)
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


def overlap(a, b):
    t = tbm.copy(a)
    tbm.booleanOperation(t, b, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return t.volume


def sweep(app, mon, bracket, hw, base, plate, y_p, z_p):
    # moves the enclosure, the bracket and the hardware through the tilt range and
    # reports overlaps, the closest approach to the base and the clearance to the table
    p = P
    mm = app.measureManager
    rows, worst = [], None
    steps = int(round(p['tilt_max'] / p['tilt_step']))
    for i in range(steps + 1):
        deg = p['tilt_step'] * i
        d_mon, d_hw, d_tab = None, None, None
        ov = 0.0
        rb = rot_x(bracket, deg, y_p, z_p)
        rh = rot_x(hw, deg, y_p, z_p)
        d_br = mm.measureMinimumDistance(rb, base).value * 10.0
        ov += overlap(rb, base)
        # the hardware must clear the base (washers only touch the arm) and sit in the bracket holes
        ov_hw = overlap(rh, base) + overlap(rh, rb)
        for name, body in mon.items():
            r = rot_x(body, deg, y_p, z_p)
            d = mm.measureMinimumDistance(r, base).value * 10.0
            ov += overlap(r, base)
            if d_mon is None or d < d_mon[0]:
                d_mon = (d, name)
            d = mm.measureMinimumDistance(r, plate).value * 10.0
            if d_tab is None or d < d_tab:
                d_tab = d
            ov_hw += overlap(rh, r)
            d = mm.measureMinimumDistance(rh, r).value * 10.0
            if d_hw is None or d < d_hw:
                d_hw = d
        rows.append((deg, d_mon, d_tab, d_br, d_hw, ov, ov_hw))
    return rows


def snapshot(app, name, eye, target, up=(0, 1, 0), ortho=False):
    vp = app.activeViewport
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType if ortho \
        else adsk.core.CameraTypes.PerspectiveCameraType
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


def run(context):
    global tbm, rm
    app = adsk.core.Application.get()
    os.makedirs(OUT, exist_ok=True)
    try:
        src = os.path.join(os.path.dirname(HERE), 'RuggedMonitor')
        if src not in sys.path:
            sys.path.insert(0, src)
        import RuggedMonitor as rm_mod
        rm = importlib.reload(rm_mod)
        tbm = adsk.fusion.TemporaryBRepManager.get()
        rm.tbm = tbm

        mon_all, _ref, info, _extras = rm.build()
        mon = {n: mon_all[n] for n in MON_PARTS}
        parts, hw, sinfo, tests = build(info)
        y_p, z_p = sinfo['y_p'], sinfo['z_p']
        log('pivot axis: Y=%.2f Z=%.2f, table (top of base) Y=%.2f, VESA centre X=%.2f Y=%.2f' % (
            y_p, z_p, sinfo['y_b'], info['cx'], info['cy']))

        rows = sweep(app, mon, parts['Tilt bracket'], hw, parts['Stand base'], sinfo['plate'], y_p, z_p)
        log('tilt sweep (distances in mm, overlaps in cm3):')
        log('  tilt  enclosure-base  (closest part)        enclosure-table  bracket-base  hardware-enclosure  overlaps')
        for deg, d_mon, d_tab, d_br, d_hw, ov, ov_hw in rows:
            flag = '  <-- OVERLAP' if ov > 1e-4 or ov_hw > 1e-4 else (
                '  <-- close' if d_mon[0] < P['min_clear'] else '')
            log('  %4.0f  %14.1f  %-24s %9.1f  %12.1f  %18.1f  %.4f / %.4f%s' % (
                deg, d_mon[0], d_mon[1], d_tab, d_br, d_hw, ov, ov_hw, flag))

        # --- document ---
        design = adsk.fusion.Design.cast(app.activeProduct)
        rebuilt = False
        if design:
            occs_ = design.rootComponent.occurrences
            names = [occs_.item(i).component.name for i in range(occs_.count)]
            if 'Stand base' in names:
                for occ in [occs_.item(i) for i in range(occs_.count)]:
                    occ.deleteMe()
                rebuilt = True
                log('rebuilt in document %s' % app.activeDocument.name)
        if not rebuilt:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)
            design.designType = adsk.fusion.DesignTypes.DirectDesignType
        try:
            design.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        except Exception:
            log('designIntent not changed:\n' + traceback.format_exc())
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent

        occs = {}
        for name, body in parts.items():
            occs[name] = rm.add_component(root, name, tbm.copy(body), False)
            b = occs[name].component.bRepBodies.item(0)
            bb = b.boundingBox
            log('%s: volume %.1f cm3, %d lump(s), bbox %.1f x %.1f x %.1f mm' % (
                name, b.volume, b.lumps.count,
                (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
                (bb.maxPoint.z - bb.minPoint.z) * 10))

        encl = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        encl.component.name = 'EP-0084 enclosure (reference)'
        for name, body in mon.items():
            encl.component.bRepBodies.add(tbm.copy(body))
            encl.component.bRepBodies.item(encl.component.bRepBodies.count - 1).name = name
        hwo = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        hwo.component.name = 'M4 hardware (reference)'
        hwo.component.bRepBodies.add(tbm.copy(hw))
        hwo.component.bRepBodies.item(0).name = 'M4 bolts, nuts and washers'

        def set_tilt(deg):
            m = adsk.core.Matrix3D.create()
            m.setToRotation(math.radians(deg), vec(1, 0, 0), pt(0, y_p, z_p))
            for o in (encl, hwo, occs['Tilt bracket']):
                o.transform2 = m
            adsk.doEvents()

        def show(**vis):
            for name, o in occs.items():
                o.isLightBulbOn = vis.get(name, vis.get('default', True))
            encl.isLightBulbOn = vis.get('encl', True)
            hwo.isLightBulbOn = vis.get('hw', True)

        # interferences in the document at the reference tilt
        try:
            set_tilt(P['view_tilt'])
            bodies = adsk.core.ObjectCollection.create()
            for o in list(occs.values()) + [encl, hwo]:
                for i in range(o.bRepBodies.count):
                    bodies.add(o.bRepBodies.item(i))
            res = design.analyzeInterference(design.createInterferenceInput(bodies))
            log('interferences at %.0f deg: %d' % (P['view_tilt'], res.count))
            for r in res:
                log('  %s x %s: %.4f cm3' % (r.entityOne.name, r.entityTwo.name, r.interferenceBody.volume))
        except Exception:
            log('interference analysis failed:\n' + traceback.format_exc())

        em = design.exportManager
        set_tilt(P['view_tilt'])
        em.execute(em.createSTEPExportOptions(os.path.join(OUT, 'desk-stand.step'), root))

        # images: the stand with the enclosure at the reference tilt, then side views
        cxm, cym = info['cx'] / 10.0, (sinfo['y_p'] + 25.0) / 10.0
        tgt = (cxm, cym, (z_p - 15.0) / 10.0)
        snapshot(app, '12-stand-front.png', (tgt[0] - 22, tgt[1] + 14, tgt[2] - 34), tgt)
        snapshot(app, '13-stand-rear.png', (tgt[0] + 22, tgt[1] + 16, tgt[2] + 34), tgt)
        show(encl=False, **{'Tilt bracket': True})
        snapshot(app, '14-stand-rear-detail.png', (tgt[0] + 16, tgt[1] + 8, tgt[2] + 22), tgt)
        show()
        side_eye = (tgt[0] + 60, tgt[1], tgt[2])
        for deg in (0, 30, 60):
            set_tilt(deg)
            snapshot(app, '15-stand-side-%d.png' % deg, side_eye, tgt, ortho=True)
        set_tilt(P['view_tilt'])

        # --- STL files in print orientation ---
        jobs = [('stand-base.stl', print_oriented('Stand base', parts['Stand base'])),
                ('stand-bracket.stl', print_oriented('Tilt bracket', parts['Tilt bracket']))]
        ta = print_oriented('Hinge test arm', tests['Hinge test arm'])
        tw = print_oriented('Hinge test wall', tests['Hinge test wall'])
        wa = ta.boundingBox
        ww = tw.boundingBox
        half = (((wa.maxPoint.x - wa.minPoint.x) + (ww.maxPoint.x - ww.minPoint.x)) / 2 + 1.0) / 2   # cm
        for body, dx in ((ta, -half), (tw, half)):
            sh = adsk.core.Matrix3D.create()
            sh.translation = vec(dx, 0, 0)
            tbm.transform(body, sh)
        add(ta, tw)
        jobs.append(('test-stand-hinge.stl', ta))
        log('STL files in print orientation:')
        for line in export_stls(app, jobs):
            log('  ' + line)
        log('OK')
    except Exception:
        log('ERROR:\n' + traceback.format_exc())
    finally:
        with open(os.path.join(OUT, 'build-stand.log'), 'w') as f:
            f.write('\n'.join(log_lines) + '\n')
        print('\n'.join(log_lines))
        log_lines.clear()

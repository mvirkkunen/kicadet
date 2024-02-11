#!/usr/bin/env python3

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.append(str(root.parent))

from kicadet.values import *
import kicadet.footprint as fp
import kicadet.symbol as sym
import kicadet.schematic as sch
import kicadet.pcb as pcb

connector_lib = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Connector.kicad_sym")
device_lib = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Device.kicad_sym")
pin_header_sym = connector_lib.get("Conn_01x02_Pin")
resistor_sym = device_lib.get("R")

connector_pinheader_lib = fp.FootprintLibrary("/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty")
resistor_smd_lib = fp.FootprintLibrary("/usr/share/kicad/footprints/Resistor_SMD.pretty")
pin_header_fp = connector_pinheader_lib.load("PinHeader_1x02_P2.54mm_Vertical")
resistor_fp = resistor_smd_lib.load("R_0805_2012Metric")

schematic = sch.SchematicFile()

sch_j1 = schematic.place(pin_header_sym, "J1", (25.4, 25.4), footprint=pin_header_fp)
sch_r1 = schematic.place(resistor_sym, "R1", (50.8, 25.4), footprint=resistor_fp)

schematic.append(sch.Wire([sch_j1.get_pin_position("1"), sch_r1.get_pin_position("1")]))
schematic.append(sch.Wire([sch_j1.get_pin_position("2"), sch_r1.get_pin_position("2")]))

schematic.save(root / "exampleproject" / "exampleproject.kicad_sch")

board = pcb.PcbFile()
p1_net = board.add_net("P1")
p2_net = board.add_net("P2")

pcb_j1 = board.place(pin_header_fp, at=(25.4, 25.4), layer=pcb.Layer.FCu, path=sch_j1)
pcb_r1 = board.place(resistor_fp, at=(50.8, 25.4, -90), layer=pcb.Layer.FCu, path=sch_r1)

pcb_j1.get_pad("1").net = pcb_r1.get_pad("1").net = p1_net
pcb_j1.get_pad("2").net = pcb_r1.get_pad("2").net = p2_net

board.append(pcb.TrackSegment(start=pcb_j1.get_pad("1").position, end=pcb_r1.get_pad("1").position, width=0.5, layer=pcb.Layer.FCu, net=p1_net))
board.append(pcb.TrackSegment(start=pcb_j1.get_pad("2").position, end=pcb_r1.get_pad("2").position, width=0.5, layer=pcb.Layer.FCu, net=p2_net))

board.append(pcb.Rect(start=(0, 0), end=(76.2, 76.2), width=0.5, layer=pcb.Layer.EdgeCuts))

board.save(root / "exampleproject" / "exampleproject.kicad_pcb")

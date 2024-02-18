from kicadet.pcb import Stackup
from .util import TestCase

class TestPcbStackup(TestCase):
    def test_stackup_1_layer(self) -> None:
        stackup = Stackup.generate_stackup(1)

        self.assertSexprEqual(stackup, """
            (stackup
                (layer "F.SilkS" (type "Top Silk Screen"))
                (layer "F.Paste" (type "Top Solder Paste"))
                (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
                (layer "F.Cu" (type "copper") (thickness 0.035))
                (layer "dielectric 1" (type "core") (thickness 1.555) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
            )
        """)

    def test_stackup_2_layer(self) -> None:
        stackup = Stackup.generate_stackup(2)

        self.assertSexprEqual(stackup, """
            (stackup
                (layer "F.SilkS" (type "Top Silk Screen"))
                (layer "F.Paste" (type "Top Solder Paste"))
                (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
                (layer "F.Cu" (type "copper") (thickness 0.035))
                (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
                (layer "B.Cu" (type "copper") (thickness 0.035))
                (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
                (layer "B.Paste" (type "Bottom Solder Paste"))
                (layer "B.SilkS" (type "Bottom Silk Screen"))
            )
        """)


    def test_stackup_4_layer(self) -> None:
        stackup = Stackup.generate_stackup(4)

        self.assertSexprEqual(stackup, """
            (stackup
                (layer "F.SilkS" (type "Top Silk Screen"))
                (layer "F.Paste" (type "Top Solder Paste"))
                (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
                (layer "F.Cu" (type "copper") (thickness 0.035))
                (layer "dielectric 1" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
                (layer "In1.Cu" (type "copper") (thickness 0.035))
                (layer "dielectric 2" (type "core") (thickness 1.24) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
                (layer "In2.Cu" (type "copper") (thickness 0.035))
                (layer "dielectric 3" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
                (layer "B.Cu" (type "copper") (thickness 0.035))
                (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
                (layer "B.Paste" (type "Bottom Solder Paste"))
                (layer "B.SilkS" (type "Bottom Silk Screen"))
            )
        """)


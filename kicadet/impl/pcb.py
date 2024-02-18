import copy
from typing import overload, Annotated, ClassVar, Optional

from kicadet.node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from kicadet.common import BaseRotate, BaseTransform, Generator, Layer, Net, PageSettings, PaperSize, Property, KICADET_GENERATOR, KICADET_VERSION
from kicadet.values import SymbolEnum, Pos2, ToPos2, ToVec2, Uuid, Vec2
from kicadet import util
from kicadet import footprint as fp, symbol as sym, schematic as sch

class Transform(BaseTransform): pass

class Rotate(BaseRotate): pass

class GeneralSettings(Node):
    node_name = "general"

    thickness: float

    def __init__(
            self,
            thickness: float
    ) -> None:
        super().__init__(locals())

class LayerType(SymbolEnum):
    Jumper = "jumper"
    Mixed = "mixed"
    Power = "power"
    Signal = "signal"
    User = "user"

class PcbLayer(Node):
    ordinal: Annotated[int, Attr.Positional]
    canonical_name: Annotated[str, Attr.Positional]
    type: Annotated[LayerType, Attr.Positional]
    user_name: Annotated[Optional[str], Attr.Positional]

    def __init__(
            self,
            ordinal: int,
            canonical_name: str,
            type: LayerType,
            user_name: Optional[str] = None
    ) -> None:
        super().__init__(locals())

class PcbLayers(ContainerNode):
    node_name = "layers"
    child_types = (PcbLayer,)

    default_non_copper_layers: ClassVar[list[tuple[str, LayerType, Optional[str]]]] = [
        (Layer.BAdhes, LayerType.User, "B.Adhesive"),
        (Layer.FAdhes, LayerType.User, "F.Adhesive"),
        (Layer.BPaste, LayerType.User, None),
        (Layer.FPaste, LayerType.User, None),
        (Layer.BSilkS, LayerType.User, "B.Silkscreen"),
        (Layer.FSilkS, LayerType.User, "F.Silkscreen"),
        (Layer.BMask, LayerType.User, None),
        (Layer.FMask, LayerType.User, None),
        (Layer.DwgsUser, LayerType.User, "User.Drawings"),
        (Layer.CmtsUser, LayerType.User, "User.Comments"),
        (Layer.Eco1User, LayerType.User, "User.Eco1"),
        (Layer.Eco2User, LayerType.User, "User.Eco2"),
        (Layer.EdgeCuts, LayerType.User, None),
        (Layer.Margin, LayerType.User, None),
        (Layer.BCrtYd, LayerType.User, "B.Courtyard"),
        (Layer.FCrtYd, LayerType.User, "F.Courtyard"),
        (Layer.BFab, LayerType.User, None),
        (Layer.FFab, LayerType.User, None),
        (Layer.User1, LayerType.User, None),
        (Layer.User2, LayerType.User, None),
        (Layer.User3, LayerType.User, None),
        (Layer.User4, LayerType.User, None),
        (Layer.User5, LayerType.User, None),
        (Layer.User6, LayerType.User, None),
        (Layer.User7, LayerType.User, None),
        (Layer.User8, LayerType.User, None),
        (Layer.User9, LayerType.User, None),
    ]

    def __init__(
            self,
            children: Optional[list[PcbLayer]] = None,
    ) -> None:
        super().__init__(locals())

    @staticmethod
    def generate_layers(num_copper_layers: int) -> "PcbLayers":
        """Generates layer list with KiCad defaults"""

        if num_copper_layers % 2 != 0 or not (1 <= num_copper_layers <= 32):
            raise ValueError(f"Don't know how to generate a board setup with {num_copper_layers} copper layers")

        layers = PcbLayers()

        ordinal = 0

        layers.append(PcbLayer(ordinal, Layer.FCu, LayerType.Signal))
        ordinal += 1

        if num_copper_layers > 2:
            for i in range(1, num_copper_layers - 1):
                layers.append(PcbLayer(ordinal, f"In{i}.Cu", LayerType.Signal))
                ordinal += 1
        ordinal = max(ordinal, 31)

        if num_copper_layers > 1:
            layers.append(PcbLayer(ordinal, Layer.BCu, LayerType.Signal))
            ordinal += 1

        for attrs in PcbLayers.default_non_copper_layers:
            layers.append(PcbLayer(ordinal, *attrs))
            ordinal += 1

        return layers

class StackupColor:
    Black = "Black"
    White = "White"

class StackupLayer(Node):
    node_name = "layer"

    name: Annotated[str, Attr.Positional]
    type: str
    color: Optional[str]
    thickness: Optional[float]
    material: Optional[str]
    epsilon_r: Optional[float]
    loss_tangent: Optional[float]

    def __init__(
            self,
            name: str,
            type: str,
            color: Optional[str] = None,
            thickness: Optional[float] = None,
            material: Optional[str] = None,
            epsilon_r: Optional[float] = None,
            loss_tangent: Optional[float] = None,
    ):
        super().__init__(locals())

class Stackup(ContainerNode):
    node_name = "stackup"
    child_types = (StackupLayer),

    copper_finish: Optional[str]

    def __init__(
            self,
            children: Optional[list[StackupLayer]] = None,
            copper_finish: Optional[str] = None):
        super().__init__(locals())

    @staticmethod
    def generate_stackup(
            num_copper_layers: int,
            thickness: float = 1.6,
            copper_thickness: float = 0.035,
            prepreg_thickness: float = 0.1,
            mask_thickness: float = 0.01,
            mask_color: Optional[str] = None,
            silkscreen_color: Optional[str] = None) -> "Stackup":
        """Generates board stackup with KiCad defaults"""

        if not (1 <= num_copper_layers <= 32) or (num_copper_layers >= 2 and num_copper_layers % 2 != 0):
            raise ValueError(f"Don't know how to generate a board stackup with {num_copper_layers} copper layers")

        stackup = Stackup()

        core_thickness = thickness - (
            (mask_thickness * (2 if num_copper_layers >= 2 else 1))
            + (copper_thickness * num_copper_layers)
            + (prepreg_thickness * ((num_copper_layers - 2) if num_copper_layers >= 2 else 0))
        )

        if core_thickness <= 0:
            raise ValueError(f"Your settings would result in a board with a non-positive thickness")

        stackup.append(StackupLayer(Layer.FSilkS, "Top Silk Screen", color=silkscreen_color))
        stackup.append(StackupLayer(Layer.FPaste, "Top Solder Paste"))
        stackup.append(StackupLayer(Layer.FMask, "Top Solder Mask", color=mask_color, thickness=0.01))

        dielectric_id = 1

        for i in range(num_copper_layers):
            if i == 0:
                layer = Layer.FCu
            elif i == num_copper_layers - 1:
                layer = Layer.BCu
            else:
                layer = f"In{i}.Cu"

            stackup.append(StackupLayer(layer, "copper", thickness=0.035))

            d_type, d_thickness = None, None
            if i == max((num_copper_layers // 2) - 1, 0):
                d_type = "core"
                d_thickness = core_thickness
            elif i < num_copper_layers - 1:
                d_type = "prepreg"
                d_thickness = prepreg_thickness

            if d_type:
                stackup.append(StackupLayer(f"dielectric {dielectric_id}", d_type, thickness=d_thickness, material="FR4", epsilon_r=4.5, loss_tangent=0.02))
                dielectric_id += 1

        if num_copper_layers >= 2:
            stackup.append(StackupLayer(Layer.BMask, "Bottom Solder Mask", color=mask_color, thickness=0.01))
            stackup.append(StackupLayer(Layer.BPaste, "Bottom Solder Paste"))
            stackup.append(StackupLayer(Layer.BSilkS, "Bottom Silk Screen", color=silkscreen_color))

        return stackup


class Setup(Node):
    node_name = "setup"

    stackup: Optional[Stackup]
    pad_to_mask_clearance: float
    solder_mask_min_width: Optional[float]
    pad_to_paste_clearance: Optional[float]
    pad_to_paste_clearance_ratio: Optional[float]
    aux_axis_origin: Optional[Vec2]
    grid_origin: Optional[Vec2]

    def __init__(
            self,
            pad_to_mask_clearance: float = 0,
            solder_mask_min_width: Optional[float] = None,
            pad_to_paste_clearance: Optional[float] = None,
            pad_to_paste_clearance_ratio: Optional[float] = None,
            aux_axis_origin: Vec2 = NEW_INSTANCE,
            grid_origin: Vec2 = NEW_INSTANCE,
    ) -> None:
        super().__init__(locals())

class TrackArc(Node):
    node_name = "arc"

    start: Annotated[Vec2, Attr.Transform]
    mid: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    net: int
    tstamp: Uuid

    @overload
    def __init__(
            self,
            *,
            start: ToVec2,
            mid: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            net: int | Net,
    ) -> None:
        """
        :param start: Start point of the arc.
        :param mid: Mid point of the arc.
        :param end: End point of the arc.
        :param stroke: Stroke style.
        :param fill: Fill style.
        """
        ...

    @overload
    def __init__(
            self,
            *,
            center: ToVec2,
            radius: float,
            start_angle: float,
            end_angle: float,
            width: float,
            layer: str,
            net: int | Net,
    ) -> None:
        """
        :param center: Center point of the circle that defines the arc.
        :param radius: Radius of the arg.
        :param start: Start angle of the arg.
        :param end: End angle of the arg.
        :param stroke: Stroke style.
        :param fill: Fill style.
        """
        ...

    def __init__(
            self,
            *,
            start: Optional[ToVec2] = None,
            mid: Optional[ToVec2] = None,
            end: Optional[ToVec2] = None,
            center: Optional[ToVec2] = None,
            radius: Optional[float] = None,
            start_angle: Optional[float] = None,
            end_angle: Optional[float] = None,
            width: float,
            layer: str,
            net: int | Net,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        """
        To create a new arc, define either (start, mid, end) or (center, radius, start_angle, end_angle).

        :param start: Start point of the arc.
        :param mid: Mid point of the arc.
        :param end: End point of the arc.
        :param center: Center point of the circle that defines the arc.
        :param radius: Radius of the arg.
        :param start: Start angle of the arg.
        :param end: End angle of the arg.
        :param stroke: Stroke (outline) style.
        :param fill: Fill style.
        """

        start, mid, end = util.calculate_arc(locals())

        super().__init__(locals())

class TrackSegment(Node):
    node_name = "segment"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    net: int
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            net: int | Net,
            tstamp: Uuid = NEW_INSTANCE
    ) -> None:
        super().__init__(locals())

class ViaType(SymbolEnum):
    Blind = "blind"
    Micro = "micro"

class ViaLayers(Node):
    node_name = "layers"

    start: Annotated[str, Attr.Positional]
    end: Annotated[str, Attr.Positional]

    def __init__(
            self,
            start: str = Layer.FCu,
            end: str = Layer.BCu,
    ) -> None:
        super().__init__(locals())

class TrackVia(Node):
    node_name = "via"

    type: Annotated[Optional[ViaType], Attr.Positional]
    locked: Annotated[bool, Attr.Bool.SymbolInList]
    at: Annotated[Vec2, Attr.Transform]
    size: float
    drill: float
    layers: ViaLayers
    net: int
    tstamp: Uuid

    def __init__(
            self,
            at: ToVec2,
            size: float,
            drill: float,
            net: int | Net = 0,
            layers: ViaLayers = NEW_INSTANCE,
            type: Optional[ViaType] = None,
            locked: bool = False,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        super().__init__(locals())

class Arc(Node):
    node_name = "gr_arc"

    start: Annotated[Vec2, Attr.Transform]
    mid: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            mid: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        super().__init__(locals())

class Rect(Node):
    node_name = "gr_rect"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        super().__init__(locals())

class Circle(Node):
    node_name = "gr_circle"

    center: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    tstamp: Uuid

    def __init__(
            self,
            center: ToVec2,
            radius: float,
            width: float,
            layer: str,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        end = Vec2(center) + Vec2(radius, 0)

        super().__init__(locals())

GraphicsItems = (fp.Footprint, Net, Arc, Circle, Rect, Rotate, TrackArc, TrackSegment, TrackVia, Transform)
Rotate.child_types = GraphicsItems
Transform.child_types = GraphicsItems

class PcbFile(ContainerNode, NodeLoadSaveMixin):
    child_types = GraphicsItems
    node_name = "kicad_pcb"
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    general: GeneralSettings
    page: PageSettings
    layers: PcbLayers
    setup: Setup

    def __init__(
        self,
        layers: PcbLayers | list[PcbLayer] | int = 2,
        thickness: float = 1.6,
        mask_color: Optional[str] = None,
        silkscreen_color: Optional[str] = None,
        page: Optional[PageSettings] = None,
        setup: Optional[Setup] = NEW_INSTANCE,
        version: int = KICADET_VERSION,
        generator: Generator = KICADET_GENERATOR,
    ) -> None:
        if isinstance(layers, list):
            layers = PcbLayers(layers)

        if isinstance(layers, int):
            num_copper_layers = layers
            layers = PcbLayers.generate_layers(num_copper_layers)

            if not setup or setup is NEW_INSTANCE:
                setup = Setup()

            if not setup.stackup:
                setup.stackup = Stackup.generate_stackup(num_copper_layers, thickness=thickness, mask_color=mask_color, silkscreen_color=silkscreen_color)

        general = GeneralSettings(thickness=thickness)
        page = page or PageSettings(PaperSize.A4)

        super().__init__(locals())

        self.append(Net(0, ""))

    def add_net(self, name: str) -> Net:
        if self.get_net(name):
            raise ValueError(f"Net '{name} already exists")

        net = Net(sum(1 for _ in self.find_all(Net)), name)
        self.append(net)
        return net

    def get_net(self, name: str) -> Optional[Net]:
        return self.find_one(Net, lambda n: n.name == name)

    def place(
            self,
            footprint: fp.Footprint | fp.LibraryFootprint,
            at: ToPos2,
            layer: str,
            path: Optional[str] = None,
            symbol: Optional[sch.SchematicSymbol] = None,
            library_link: Optional[str] = None,
            parent: Optional[ContainerNode] = None,
    ) -> fp.Footprint:
        """
        Places a footprint onto the PCB.
        """

        if not layer in (Layer.FCu, Layer.BCu):
            raise ValueError("Footprints can only be placed on layers F.Cu and B.Cu")

        if not library_link:
            library_link = footprint.library_link

        if not library_link:
            raise ValueError("library_link is required if footprint does not provide one")

        children: list[Node] = []

        if path is None and symbol is not None:
            for prop in symbol.find_all(sym.Property, lambda p: p.name.startswith("ki_")):
                children.append(Property(prop.name, prop.value))

            path = f"/{symbol.uuid.value}"

        children.extend(c.clone() for c in footprint)

        pcb_fp = fp.Footprint(
            library_link=library_link,
            layer=layer,
            at=at,
            path=path,
            descr=footprint.descr,
            tags=footprint.tags,
            children=children,
            attr=footprint.attr.clone() if footprint.attr else None
        )

        pcb_fp.unknown = copy.deepcopy(footprint.unknown)

        if symbol:
            for (prop_type, sym_prop_name) in [
                (fp.TextType.Reference, sym.Property.Reference),
                (fp.TextType.Value, sym.Property.Value)
            ]:
                text = pcb_fp.find_one(fp.Text, lambda p: p.type == prop_type)
                value = symbol.get_property(sym_prop_name)
                if text and value:
                    text.text = value

        if layer == Layer.BCu:
            for pad in pcb_fp.find_all(fp.Pad):
                pad.layers.layers = [Layer.flip(l) for l in pad.layers.layers]

        (parent or self).append(pcb_fp)

        return pcb_fp

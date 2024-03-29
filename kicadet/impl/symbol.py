from pathlib import Path
from typing import overload, ClassVar, Annotated, Optional

from kicadet.values import Pos2, SymbolEnum, Vec2, ToPos2, ToVec2
from kicadet.common import BaseRotate, BaseTransform, CoordinatePoint, CoordinatePointList, FillDefinition, Generator, StrokeDefinition, TextEffects, KICADET_VERSION, KICADET_GENERATOR
from kicadet.node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from kicadet import util

class Property(Node):
    node_name = "property"

    Reference: ClassVar[str] = "Reference"
    Value: ClassVar[str] = "Value"
    Footprint: ClassVar[str] = "Footprint"
    Datasheet: ClassVar[str] = "Datasheet"

    name: Annotated[str, Attr.Positional]
    value: Annotated[str, Attr.Positional]
    at: Annotated[Pos2, Attr.Transform]
    effects: TextEffects

    def __init__(
            self,
            name: str,
            value: str,
            at: ToPos2,
            effects: TextEffects = NEW_INSTANCE,
    ) -> None:
        """
        :param name: The name of the property. Must be unique within symbol.
        :param value: The value of the property.
        :param at: The position and angle of the property.
        :param effects: Defines how the text is displayed.
        """
        super().__init__(locals())

class Transform(BaseTransform):
    """
    Translates and rotates its child nodes. This node is not part of the KiCad data model and will transparently disappear when serialized.
    """

    pass

class Rotate(BaseRotate):
    """
    Rotates its child nodes. This node is not part of the KiCad data model and will transparently disappear when serialized.
    """

    pass

class Arc(Node):
    node_name = "arc"

    start: Annotated[Vec2, Attr.Transform]
    mid: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    stroke: StrokeDefinition
    fill: FillDefinition

    @overload
    def __init__(
            self,
            *,
            start: ToVec2,
            mid: ToVec2,
            end: ToVec2,
            stroke: Optional[StrokeDefinition] = None,
            fill: Optional[FillDefinition] = None,
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
            stroke: Optional[StrokeDefinition] = None,
            fill: Optional[FillDefinition] = None,
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
            stroke: Optional[StrokeDefinition] = None,
            fill: Optional[FillDefinition] = None,
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

        if stroke is None:
            stroke = StrokeDefinition()

        if fill is None:
            fill = FillDefinition()

        super().__init__(locals())

class Circle(Node):
    node_name = "circle"

    center: Annotated[Vec2, Attr.Transform]
    radius: float
    stroke: StrokeDefinition
    fill: FillDefinition

    def __init__(
            self,
            center: Vec2,
            radius: float,
            stroke: StrokeDefinition = NEW_INSTANCE,
            fill: FillDefinition = NEW_INSTANCE,
    ) -> None:
        """
        :param center: Center point of the circle.
        :param radius: Radius of the circle.
        :param stroke: Stroke (outline) style.
        :param fill: Fill style.
        """

        super().__init__(locals())

class Bezier(Node):
    node_name = "bezier"

    pts: CoordinatePointList
    stroke: StrokeDefinition
    fill: FillDefinition

    def __init__(
            self,
            pts: CoordinatePointList = NEW_INSTANCE,
            stroke: StrokeDefinition = NEW_INSTANCE,
            fill: FillDefinition = NEW_INSTANCE,
    ) -> None:
        """
        :param pts: Points that define the cubic bezier curve. Exactly 4 must be defined before serialization.
        :param stroke: Stroke (outline) style.
        :param fill: Fill style.
        """

        super().__init__(locals())

    def validate(self) -> None:
        super().validate()

        if len(self.pts) != 4:
            raise ValueError("Bezier must have exactly 4 points")

class PolyLine(Node):
    node_name = "polyline"

    pts: CoordinatePointList
    stroke: StrokeDefinition
    fill: FillDefinition

    def __init__(
            self,
            pts: CoordinatePointList = NEW_INSTANCE,
            stroke: StrokeDefinition = NEW_INSTANCE,
            fill: FillDefinition = NEW_INSTANCE,
    ) -> None:
        """
        :param pts: Points that define the polyline. At least 2 must be defined before serialization.
        :param stroke: Stroke (outline) style.
        :param fill: Fill style.
        """

        super().__init__(locals())

    def validate(self) -> None:
        super().validate()

        if len(self.pts) < 2:
            raise ValueError("PolyLine must have at least 2 points")

class Rectangle(Node):
    node_name = "rectangle"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    stroke: StrokeDefinition
    fill: FillDefinition

    def __init__(
            self,
            start: Vec2,
            end: Vec2,
            stroke: StrokeDefinition = NEW_INSTANCE,
            fill: FillDefinition = NEW_INSTANCE,
    ) -> None:
        """
        :param start: Start (e.g. top left) point of the rectangle.
        :param end: End (e.g. bottom right) point of the rectangle.
        :param stroke: Stroke (outline) style.
        :param fill: Fill style.
        """

        super().__init__(locals())

class Text(Node):
    node_name = "text"

    text: Annotated[str, Attr.Positional]
    at: Annotated[Pos2, Attr.Transform]
    effects: TextEffects

    def __init__(
            self,
            text: str,
            at: Vec2,
            effects: TextEffects = NEW_INSTANCE,
    ) -> None:
        """
        :param text: Text to display.
        :param at: Position and rotation angle of the text.
        :param effects: Text display effects.
        """

        super().__init__(locals())

class PinName(Node):
    node_name = "name"

    name: Annotated[str, Attr.Positional]
    effects: TextEffects

    def __init__(
            self,
            name: str,
            effects: TextEffects = NEW_INSTANCE,
    ) -> None:
        """
        :param name: Name of the pin.
        :param effects: Text display effects.
        """

        super().__init__(locals())

class PinNumber(Node):
    node_name = "number"

    number: Annotated[str, Attr.Positional]
    effects: TextEffects

    def __init__(
            self,
            number: str,
            effects: TextEffects = NEW_INSTANCE,
    ) -> None:
        """
        :param number: Number of the pin.
        :param effects: Text display effects.
        """

        super().__init__(locals())

class PinElectricalType(SymbolEnum):
    Input = "input"
    Output = "output"
    Bidirectional = "bidirectional"
    TriState = "tri_state"
    Passive = "passive"
    Free = "free"
    Unspecified = "unspecified"
    PowerIn = "power_in"
    PowerOut = "power_out"
    OpenCollector = "open_collector"
    OpenEmitter = "open_emitter"
    No_Connect = "no_connect"

class PinGraphicalType(SymbolEnum):
    Line = "line"
    Inverted = "inverted"
    Clock = "clock"
    InvertedClock = "inverted_clock"
    InputLow = "input_low"
    ClockLow = "clock_low"
    OutputLow = "output_low"
    EdgeClockHigh = "edge_clock_high"
    NonLogic = "non_logic"

class Pin(Node):
    node_name = "pin"

    electrical_type: Annotated[PinElectricalType, Attr.Positional]
    graphical_type: Annotated[PinGraphicalType, Attr.Positional]
    at: Annotated[Pos2, Attr.Transform]
    length: float
    name: PinName
    number: PinNumber

    def __init__(
            self,
            electrical_type: PinElectricalType,
            graphical_type: PinGraphicalType,
            at: Pos2,
            length: float,
            name: PinName | str,
            number: PinNumber | str,
    ) -> None:
        """
        :param electrical_type: Electrical type of the pin.
        :param graphical_type: Graphical type of the pin.
        :param at: Position and rotation angle of the pin.
        :param length: Length of the pin.
        :param name: Name of the pin and its attributes.
        :param number: Number of the pin and its attributes.
        """

        super().__init__(locals())

class BaseSymbol(ContainerNode):
    node_name = "symbol"

    name: Annotated[str, Attr.Positional]

    def all_pins(self) -> list[Pin]:
        r = []

        for child in self:
            if isinstance(child, Pin):
                r.append(child)
            elif isinstance(child, ChildSymbol):
                r.extend(child.all_pins())

        return r

class ChildSymbol(BaseSymbol):
    child_types = (Arc, Circle, Bezier, PolyLine, Rectangle, Text, Pin, Transform, Rotate)

    unit_name: Optional[str]

    def __init__(
            self,
            name: str,
            unit_name: Optional[str] = None,
    ) -> None:
        """
        :param name: Name of the child symbol.
        :param unit_name: If defined, this child symbol is a separate unit of the main symbol with the defined name.
        """

        super().__init__(locals())

class PinNumbers(Node):
    node_name = "pin_numbers"

    hide: bool

    def __init__(
            self,
            hide: bool = False
    ) -> None:
        """
        :param hide: True to hide the pin numbers of the symbol.
        """

        super().__init__(locals())

class PinNames(Node):
    node_name = "pin_names"

    offset: Optional[float]
    hide: bool

    def __init__(
            self,
            offset: Optional[float] = None,
            hide: bool = False
    ) -> None:
        """
        :param offset: Pin name offset for all pins. If not defined, the pin name offset is 0.508mm (0.020").
        :param hide: True to hide the pin names of the symbol.
        """

        super().__init__(locals())

class Symbol(BaseSymbol):
    child_types = (Property, Arc, Circle, Bezier, PolyLine, Rectangle, Text, Pin, ChildSymbol, Transform, Rotate)

    extends: Optional[str]
    pin_numbers: Optional[PinNumbers]
    pin_names: Optional[PinNames]
    in_bom: Annotated[bool, Attr.Bool.YesNo]
    on_board: Annotated[bool, Attr.Bool.YesNo]

    def __init__(
            self,
            name: str,
            extends: Optional[str] = None,
            pin_numbers: Optional[PinNumbers] = None,
            pin_names: Optional[PinNames] = None,
            in_bom: bool = True,
            on_board: bool = True,
    ):
        """
        :param name: Name of the symbol.
        :param extends: If defined, this symbol extends another symbol.
        :param pin_numbers: Display attributes for this symbol's pin numbers.
        :param pin_names: Display attributes for this symbol's pin names.
        :param in_bom: Include symbol in BOM output.
        :param on_board: Export symbol from schematic to PCB.
        """

        super().__init__(locals())

class SymbolLibrary(ContainerNode, NodeLoadSaveMixin):
    node_name = "kicad_symbol_lib"
    child_types = (Symbol,)
    order_attrs = ("version", "generator")

    filename: Annotated[str, Attr.Ignore]
    version: int
    generator: Generator

    def __init__(
        self,
        filename: str,
        version: int = KICADET_VERSION,
        generator: Generator = KICADET_GENERATOR,
    ):
        self.filename = filename

        super().__init__(locals())

    def _set_path(self, path: Path) -> None:
        self.filename = path.stem

    def get(self, name: str) -> Optional[Symbol]:
        """
        Gets a symbol by name.
        """
        return self.find_one(Symbol, lambda c: c.name == name)

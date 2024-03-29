import copy
from typing import Annotated, Iterable, Optional

from kicadet.values import Pos2, Rgba, ToVec2, SymbolEnum, Uuid, Vec2
from kicadet.node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from kicadet.common import BaseRotate, BaseTransform, CoordinatePoint, CoordinatePointList, Generator, PageSettings, PaperSize, Property, StrokeDefinition, TextEffects, KICADET_GENERATOR, KICADET_VERSION
from kicadet.footprint import LibraryFootprint
from kicadet import symbol

class Junction(Node):
    node_name = "junction"

    at: Annotated[Vec2, Attr.Transform]
    diameter: float
    color: Rgba
    uuid: Uuid

    def __init__(
            self,
            at: Vec2,
            diameter: float = 0,
            color: Rgba = NEW_INSTANCE,
            uuid: Uuid = NEW_INSTANCE
    ):
        super().__init__(locals())

class NoConnect(Node):
    node_name = "no_connect"

    at: Annotated[Vec2, Attr.Transform]
    uuid: Uuid

    def __init__(
            self,
            at: Vec2,
            uuid: Uuid = NEW_INSTANCE
    ):
        super().__init__(locals())

class LabelShape(SymbolEnum):
    Input = "input"
    Output = "output"
    Bidirectional = "bidirectional"
    TriState = "tri_state"
    Passive = "passive"

class GlobalLabel(ContainerNode):
    child_types = (Property,)
    node_name = "global_label"

    name: Annotated[str, Attr.Positional]
    shape: LabelShape
    fields_autoplaced: Annotated[bool, Attr.Bool.SymbolInList]
    effects: TextEffects
    at: Annotated[Pos2, Attr.Transform]
    uuid: Uuid

    def __init__(
            self,
            name: str,
            at: Pos2,
            shape: LabelShape = LabelShape.Input,
            fields_autoplaced: bool = True,
            effects: TextEffects = NEW_INSTANCE,
            uuid: Uuid = NEW_INSTANCE,
    ):
        super().__init__(locals())

class BaseWire(Node):
    pts: CoordinatePointList
    stroke: StrokeDefinition
    uuid: Uuid

    def __init__(
            self,
            pts: "CoordinatePointList | Iterable[ToVec2 | CoordinatePoint]" = NEW_INSTANCE,
            stroke: StrokeDefinition = NEW_INSTANCE,
            uuid: Uuid = NEW_INSTANCE,
    ):
        if not isinstance(pts, CoordinatePointList):
            pts = CoordinatePointList(pts)

        pts._set_parent(self)

        super().__init__(locals())

class Wire(BaseWire):
    node_name = "wire"

class Bus(BaseWire):
    node_name = "bus"

class SchematicSymbolPin(Node):
    node_name = "pin"

    number: Annotated[str, Attr.Positional]
    uuid: Uuid

    def __init__(
            self,
            number: str,
            uuid: Uuid = NEW_INSTANCE
        ):
        super().__init__(locals())

class SchematicSymbolInstancePath(Node):
    node_name = "path"

    path: Annotated[str, Attr.Positional]
    reference: str
    unit: int

    def __init__(
            self,
            path: str,
            reference: str,
            unit: int,
        ):
        super().__init__(locals())

class SchematicSymbolInstanceProject(Node):
    node_name = "project"

    name: Annotated[str, Attr.Positional]
    path: SchematicSymbolInstancePath

    def __init__(
            self,
            name: str,
            path: SchematicSymbolInstancePath = NEW_INSTANCE,
        ):
        super().__init__(locals())

class SchematicSymbolInstances(ContainerNode):
    child_types = (SchematicSymbolInstanceProject,)
    node_name = "instances"

    def __init__(
            self,
            children: Optional[list[SchematicSymbolInstanceProject]] = None,
        ):
        super().__init__(locals())

class Transform(BaseTransform):
    pass

class Rotate(BaseRotate):
    pass

class Mirror(SymbolEnum):
    X = "x"
    Y = "y"

class SchematicSymbol(ContainerNode):
    child_types = (symbol.Property, Transform, SchematicSymbolPin)
    node_name = "symbol"

    lib_id: str
    at: Annotated[Pos2, Attr.Transform]
    mirror: Optional[Mirror]
    unit: int
    in_bom: Annotated[bool, Attr.Bool.YesNo]
    on_board: Annotated[bool, Attr.Bool.YesNo]
    dnp: Annotated[bool, Attr.Bool.YesNo]
    fields_autoplaced: Annotated[bool, Attr.Bool.SymbolInList]
    uuid: Uuid
    instances: SchematicSymbolInstances

    def __init__(
            self,
            lib_id: str,
            at: Pos2,
            unit: int,
            mirror: Optional[Mirror] = None,
            in_bom: bool = True,
            on_board: bool = True,
            dnp: bool = False,
            fields_autoplaced: bool = True,
            uuid: Uuid = NEW_INSTANCE,
            instances: SchematicSymbolInstances = NEW_INSTANCE,
            children: Optional[list[symbol.Property | SchematicSymbolPin]] = None,
        ):

        super().__init__(locals())

    def validate(self) -> None:
        super().validate()

        if self.at.r % 90 != 0:
            raise ValueError("SchematicSymbols can only be rotated in increments of 90 degrees")

        if any(p for p in self.find_all(symbol.Property) if p.at.r % 90 != 0):
            raise ValueError("SchematicSymbol Properties can only be rotated in increments of 90 degrees")

    def get_pin_position(self, number: str) -> Pos2:
        schematic_file = self.closest(SchematicFile) # type: ignore
        if not schematic_file:
            raise RuntimeError("Cannot get pin position because there is no parent schematic")

        lib_sym = schematic_file.lib_symbols.get(self.lib_id)
        if not lib_sym:
            raise RuntimeError(f"Could not find library symbol '{self.lib_id}' in schematic")

        pin = next((p for p in lib_sym.all_pins() if p.number.number == number), None)
        if not pin:
            raise RuntimeError(f"Symbol does not have a pin with number '{number}'")

        return self.transform_pos(self.at) + self.transform_pos(pin.at.flip_y())

    def set_property(self, name: str, value: str) -> None:
        prop = self.find_one(symbol.Property, lambda p: p.name == name)
        if prop:
            prop.value = value
        else:
            self.append(symbol.Property(
                name,
                value,
                (0, 0),
                TextEffects(hide=True),
            ))

    def get_property(self, name: str) -> Optional[str]:
        prop = self.find_one(symbol.Property, lambda p: p.name == name)
        if not prop:
            return None

        return prop.value

    @property
    def pins(self) -> Iterable[SchematicSymbolPin]:
        return self.find_all(SchematicSymbolPin)

Transform.child_types = (symbol.Property, SchematicSymbol, Junction, NoConnect, Wire, Bus, Transform, Rotate)
Rotate.child_types = (symbol.Property, SchematicSymbol, Junction, NoConnect, Wire, Bus, Transform, Rotate)

class SchematicLibSymbols(ContainerNode):
    node_name = "lib_symbols"
    child_types = (symbol.Symbol,)

    def get(self, name: str) -> Optional[symbol.Symbol]:
        """
        Gets a symbol by name.
        """
        return self.find_one(symbol.Symbol, lambda c: c.name == name)

class SchematicFile(ContainerNode, NodeLoadSaveMixin):
    node_name = "kicad_sch"
    child_types = (Junction, NoConnect, Wire, Bus, GlobalLabel, SchematicSymbol, Transform, Rotate)
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    uuid: Uuid
    page: PageSettings
    lib_symbols: SchematicLibSymbols

    def __init__(
        self,
        uuid: Uuid = NEW_INSTANCE,
        page: Optional[PageSettings] = None,
        lib_symbols: SchematicLibSymbols = NEW_INSTANCE,
        version: int = KICADET_VERSION,
        generator: Generator = KICADET_GENERATOR,
    ):
        if not page:
            page = PageSettings(PaperSize.A4)

        super().__init__(locals())

    def import_symbol(
            self,
            sym: symbol.Symbol,
    ) -> str:
        """
        Imports a symbol into lib_symbols and returns the lib_id. If the symbol has already been imported, this does nothing.
        """

        lib_file = sym.closest(symbol.SymbolLibrary) # type: ignore
        if not lib_file:
            raise RuntimeError("Only LibSymbols that are part of a SymbolLibFile can be imported")

        lib_id = f"{lib_file.filename}:{sym.name}"
        if not self.lib_symbols.find_one(symbol.Symbol, lambda s: s.name == lib_id):
            lsym = sym.clone()
            lsym.name = lib_id
            self.lib_symbols.append(lsym)

        return lib_id

    def place(
            self,
            sym: symbol.Symbol,
            reference: str,
            at: Pos2,
            value: Optional[str] = None,
            mirror: Optional[Mirror] = None,
            footprint: Optional[str | LibraryFootprint] = None,
            in_bom: Optional[bool] = None,
            on_board: Optional[bool] = None,
            dnp: bool = False,
            parent: Optional[ContainerNode] = None,
    ) -> SchematicSymbol:
        """
        Places a library symbol onto the schematic. If the symbol has not already been imported, it is automatically imported into lib_symbols.

        :param symbol: The library symbol to place.
        :param reference: Reference designator for the symbol.
        :param at: Position and rotation angle for the symbol.
        :param in_bom: True is the part should be included in the BOM. By default, inherited from the library symbol.
        :param on_board: True is the part should be placed onto the PCB. By default, inherited from the library symbol.
        :param dnp: True to set Do Not Place for the part.
        :returns: a SchematicSymbol instance
        """

        lib_id = self.import_symbol(sym)

        ssym = SchematicSymbol(
            lib_id=lib_id,
            at=at,
            mirror=mirror,
            unit=1,
            in_bom=sym.in_bom if in_bom is None else in_bom,
            on_board=sym.on_board if on_board is None else on_board,
            dnp=dnp,
            instances=SchematicSymbolInstances([
                SchematicSymbolInstanceProject(
                    "project",
                    SchematicSymbolInstancePath(f"/{self.uuid.value}", reference, 1)
                )
            ]),
        )
        ssym.unknown = copy.deepcopy(sym.unknown)

        for pin in sym.all_pins():
            ssym.append(SchematicSymbolPin(pin.number.number))

        for prop in sym.find_all(symbol.Property):
            sprop = prop.clone()
            if sprop.name == symbol.Property.Footprint:
                if isinstance(footprint, str):
                    sprop.value = footprint
                elif isinstance(footprint, LibraryFootprint):
                    sprop.value = f"{footprint.library_name}:{footprint.name}"
            elif sprop.name == symbol.Property.Reference:
                sprop.value = reference
            elif sprop.name == symbol.Property.Value and value is not None:
                sprop.value = value

            sprop.at = Pos2(Vec2(at)) + sprop.at.flip_y()
            ssym.append(sprop)

        (parent or self).append(ssym)

        return ssym


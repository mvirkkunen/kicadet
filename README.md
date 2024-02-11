kicadet - KiCad Editing Tools
=============================

Python library for loading, modifying and saving KiCad board, footprint, symbol and schematic files.

Work in progress. Don't expect it to work perfectly.

Supported file types
--------------------

- Board (`.kicad_pcb`)
- Footprint (`.kicad_mod`)
- Schematic (`.kicad_sch`)
- Symbol library (`.kicad_sym`)

Not all items types are yet supported, and since the documentation isn't entirely up to date, some version incompatibilities are to be expected.

When loading a file with unknown items, an attempt is made to preserve them when saving the file, but the result is not necessarily perfect.

TODO
----

- [ ] Verify all the Node implementations more thorougly
- [ ] Implement automatic detection for system library directories
- [ ] Support writing `.kicad_pro` / `.kicad_prl` and such so that a new project can be generated
- [ ] Support editing `fp-lib-table` and `sym-lib-table` files
- [ ] Write some actual tests

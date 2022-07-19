# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import pathlib

import mkdocs_gen_files
from capellambse import MelodyModel, aird

from capellambse_context_diagrams import context, filters, styling

logging.basicConfig()

dest = pathlib.Path("assets") / "images"
model_path = pathlib.Path(__file__).parent.parent / "tests" / "data"
model = MelodyModel(path=model_path, entrypoint="ContextDiagram.aird")
general_context_diagram_uuids = {
    "Environment": "e37510b9-3166-4f80-a919-dfaac9b696c7",
    "Eat": "8bcb11e6-443b-4b92-bec2-ff1d87a224e7",
    "Middle": "da08ddb6-92ba-4c3b-956a-017424dbfe85",
    "Capability": "9390b7d5-598a-42db-bef8-23677e45ba06",
    "Lost": "a5642060-c9cc-4d49-af09-defaa3024bae",
    "Left": "f632888e-51bc-4c9f-8e81-73e9404de784",
    "educate Wizards": "957c5799-1d4a-4ac0-b5de-33a65bf1519c",
    "Weird guy": "098810d9-0325-4ae8-a111-82202c0d2016",
    "Top secret": "5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6",
}
interface_context_diagram_uuids = {
    "Left to right": "3ef23099-ce9a-4f7d-812f-935f47e7938d",
}
diagram_uuids = general_context_diagram_uuids | interface_context_diagram_uuids


def generate_index_images() -> None:
    for uuid in diagram_uuids.values():
        diag: context.ContextDiagram = model.by_uuid(uuid).context_diagram
        with mkdocs_gen_files.open(f"{str(dest / diag.name)}.svg", "w") as fd:
            print(diag.as_svg, file=fd)


def generate_no_symbol_images() -> None:
    for name in ("Capability", "Middle"):
        uuid = general_context_diagram_uuids[name]
        diag: context.ContextDiagram = model.by_uuid(uuid).context_diagram
        diag.display_symbols_as_boxes = True
        diag.invalidate_cache()
        filepath = f"{str(dest / diag.name)} no_symbols.svg"
        with mkdocs_gen_files.open(filepath, "w") as fd:
            print(diag.as_svg, file=fd)


def generate_no_edgelabel_image(uuid: str) -> None:
    diagram: context.ContextDiagram = model.by_uuid(uuid).context_diagram
    diagram.invalidate_cache()
    filename = " ".join((str(dest / diagram.name), "no_edgelabels"))
    with mkdocs_gen_files.open(f"{filename}.svg", "w") as fd:
        print(diagram.render("svg", no_edgelabels=True), file=fd)


def generate_filter_image(
    uuid: str, filter_name: str, suffix: str = ""
) -> None:
    obj = model.by_uuid(uuid)
    diag: context.ContextDiagram = obj.context_diagram
    diag.filters = {filter_name}
    filename = " ".join((str(dest / diag.name), suffix))
    with mkdocs_gen_files.open(f"{filename}.svg", "w") as fd:
        print(diag.as_svg, file=fd)


def generate_styling_image(
    uuid: str, styles: dict[str, styling.Styler], suffix: str = ""
) -> None:
    obj = model.by_uuid(uuid)
    diag: context.ContextDiagram = obj.context_diagram
    diag.filters.clear()
    diag.invalidate_cache()
    diag.render_styles = styles
    filename = " ".join((str(dest / diag.name), suffix))
    with mkdocs_gen_files.open(f"{filename}.svg", "w") as fd:
        print(diag.as_svg, file=fd)


generate_index_images()
generate_no_symbol_images()

wizard = general_context_diagram_uuids["educate Wizards"]
generate_no_edgelabel_image(wizard)

lost = general_context_diagram_uuids["Lost"]
generate_filter_image(lost, filters.EX_ITEMS, "ex")
generate_filter_image(lost, filters.FEX_EX_ITEMS, "fex and ex")
generate_filter_image(lost, filters.FEX_OR_EX_ITEMS, "fex or ex")

generate_styling_image(
    lost,
    dict(
        styling.BLUE_ACTOR_FNCS,
        **{"junction": lambda _: {"fill": aird.RGB(220, 20, 60)}},  # type: ignore
    ),
    "red junction",
)
generate_styling_image(wizard, {}, "no_styles")

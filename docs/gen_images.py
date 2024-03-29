# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import pathlib

import mkdocs_gen_files
from capellambse import MelodyModel, diagram

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
hierarchy_context = "16b4fcc5-548d-4721-b62a-d3d5b1c1d2eb"
diagram_uuids = general_context_diagram_uuids | interface_context_diagram_uuids
class_tree_uuid = "b7c7f442-377f-492c-90bf-331e66988bda"
realization_fnc_uuid = "beaf5ba4-8fa9-4342-911f-0266bb29be45"
realization_comp_uuid = "b9f9a83c-fb02-44f7-9123-9d86326de5f1"
data_flow_uuid = "3b83b4ba-671a-4de8-9c07-a5c6b1d3c422"


def generate_index_images() -> None:
    for uuid in diagram_uuids.values():
        diag: context.ContextDiagram = model.by_uuid(uuid).context_diagram
        with mkdocs_gen_files.open(f"{str(dest / diag.name)}.svg", "w") as fd:
            print(diag.render("svg", transparent_background=False), file=fd)


def generate_no_symbol_images() -> None:
    for name in ("Capability", "Middle"):
        uuid = general_context_diagram_uuids[name]
        diag: context.ContextDiagram = model.by_uuid(uuid).context_diagram
        diag.display_symbols_as_boxes = True
        diag.invalidate_cache()
        filepath = f"{str(dest / diag.name)} no_symbols.svg"
        with mkdocs_gen_files.open(filepath, "w") as fd:
            print(diag.render("svg", transparent_background=False), file=fd)


def generate_no_edgelabel_image(uuid: str) -> None:
    cdiagram: context.ContextDiagram = model.by_uuid(uuid).context_diagram
    cdiagram.invalidate_cache()
    filename = " ".join((str(dest / cdiagram.name), "no_edgelabels"))
    with mkdocs_gen_files.open(f"{filename}.svg", "w") as fd:
        print(
            cdiagram.render(
                "svg", no_edgelabels=True, transparent_background=False
            ),
            file=fd,
        )


def generate_filter_image(
    uuid: str, filter_name: str, suffix: str = ""
) -> None:
    obj = model.by_uuid(uuid)
    diag: context.ContextDiagram = obj.context_diagram
    diag.filters = {filter_name}
    filename = " ".join((str(dest / diag.name), suffix))
    with mkdocs_gen_files.open(f"{filename}.svg", "w") as fd:
        print(diag.render("svg", transparent_background=False), file=fd)


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
        print(diag.render("svg", transparent_background=False), file=fd)


def generate_hierarchy_image() -> None:
    obj = model.by_uuid(hierarchy_context)
    diag: context.ContextDiagram = obj.context_diagram
    with mkdocs_gen_files.open(f"{str(dest / diag.name)}.svg", "w") as fd:
        print(
            diag.render(
                "svg", include_inner_objects=True, transparent_background=False
            ),
            file=fd,
        )


def generate_class_tree_images() -> None:
    obj = model.by_uuid(class_tree_uuid)
    diag = obj.tree_view
    with mkdocs_gen_files.open(f"{str(dest / diag.name)}.svg", "w") as fd:
        print(diag.render("svg"), file=fd)
    with mkdocs_gen_files.open(
        f"{str(dest / diag.name)}-params.svg", "w"
    ) as fd:
        print(
            diag.render(
                "svg",
                edgeRouting="ORTHOGONAL",
                direction="Right",
                partitioning=False,
                edgeLabelsSide="ALWAYS_DOWN",
                transparent_background=False,
            ),
            file=fd,
        )


def generate_realization_view_images() -> None:
    for uuid in (realization_fnc_uuid, realization_comp_uuid):
        obj = model.by_uuid(uuid)
        diag = obj.realization_view
        with mkdocs_gen_files.open(f"{str(dest / diag.name)}.svg", "w") as fd:
            print(
                diag.render(
                    "svg",
                    depth=3,
                    search_direction="ALL",
                    show_owners=True,
                    transparent_background=False,
                ),
                file=fd,
            )


def generate_data_flow_image() -> None:
    diag: context.DataFlowViewDiagram = model.by_uuid(
        data_flow_uuid
    ).data_flow_view
    with mkdocs_gen_files.open(f"{str(dest / diag.name)}.svg", "w") as fd:
        print(diag.render("svg", transparent_background=False), file=fd)


generate_index_images()
generate_hierarchy_image()
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
        junction=lambda o, s: {"stroke": diagram.RGB(220, 20, 60)},
    ),
    "red junction",
)
generate_styling_image(wizard, {}, "no_styles")
generate_class_tree_images()
generate_realization_view_images()
generate_data_flow_image()

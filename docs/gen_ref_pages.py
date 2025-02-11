# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files

src = "capellambse_context_diagrams"
PACKAGE_PATH = Path("src", src)
nav = mkdocs_gen_files.Nav()

for path in sorted(PACKAGE_PATH.rglob("*.py")):
    module_path = path.relative_to(PACKAGE_PATH).with_suffix("")
    doc_path = path.relative_to(PACKAGE_PATH).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)
    parts = [src]
    if (filename := module_path.parts[-1]) != "__init__":
        parts += list(module_path.parts)
    else:
        parts += list(module_path.parts)[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    if filename == "__main__":
        continue

    nav[tuple(parts)] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)
        print("::: " + identifier, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)


with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

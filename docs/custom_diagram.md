<!--
 ~ SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Custom Diagram

You can easily create custom diagrams based on the data in the model. You define the data collection, and the ´builders´ module takes care of the rest.

??? example "Custom Diagram of `PP 1 `"

    ``` py
    import capellambse

    def _collector(
        target: m.ModelElement,
    ) -> cabc.Iterator[m.ModelElement]:
        visited = set()
        def collector(
            target: m.ModelElement,
        ) -> cabc.Iterator[m.ModelElement]:
            if target.uuid in visited:
                return
            visited.add(target.uuid)
            for link in target.links:
                yield link
                yield from collector(link.source)
                yield from collector(link.target)
        yield from collector(target)

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    obj = model.by_uuid("c403d4f4-9633-42a2-a5d6-9e1df2655146")
    diag = obj.context_diagram
    diag.render("svgdiagram", collect=_collector(obj)).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Context of PP 1.svg" width="1000000">
        <figcaption>Context of PP 1 [PAB]</figcaption>
    </figure>

You can find more examples of collectors in the
[`collectors`][capellambse_context_diagrams.collectors]

## Check out the code

To understand the collection have a look into the
[`builders`][capellambse_context_diagrams.builders]
module.

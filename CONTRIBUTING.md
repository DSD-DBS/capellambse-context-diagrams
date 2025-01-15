<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Introduction

First off, thank you for considering contributing to capellambse-context-diagrams. It's people like you that make capellambse-context-diagrams and therefore [capellambse](https://github.com/DSD-DBS/py-capellambse) such great tools.

Please take a moment to review this document in order to make the contribution process easy and effective for everyone involved.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Opening an issue

GitHub's issue tracker is the preferred channel for [bug reports](#bug-reports), [features requests](#feature-requests), submitting [pull requests](#pull-requests) and improving the [documentation](#extending-the-documentation), but please respect the following restrictions:

* Please do not use the issue tracker for personal support requests.
    - For internals (collegues from DB): You can reach the maintainers via our internal messaging tool or via email and ask for guidance.

    - For externals: You can reach the founder of this extension via [email](mailto:ernst.wuerger@deutschebahn.com?subject=[capellambse-context-diagrams]%20My%20problem).

* Please **do not** derail or troll issues. Keep the discussion on topic and
  respect the opinions of others.

## Contributions we are especially looking for

### Extending the Documentation

If you find paragraphs or sections unintuitive or you have a more clear way of explaining and showing the capabilities of a feature an issue can be opened.

You can install needed libraries via

```bash
pip install "[.docs]"
```

and see your changes to the markdown files live by executing

```bash
mkdocs serve
```

command in the root directory. Keep in mind that the code reference is generated from the docstrings via [mkdocsstrings](https://mkdocstrings.github.io/). This is a plugin for [mkdocs](https://www.mkdocs.org/). Here we are using [material for mkdocs](https://squidfunk.github.io/mkdocs-material/) which gives a modern theme for mkdocs.

### Bug reports

A bug is a _demonstrable problem_ that is caused by the code in the repository.
Good bug reports are extremely helpful - thank you!

Guidelines for bug reports:

1. **Use the GitHub issue search** &mdash; check if the issue has already been
   reported.

2. **Check if the issue has been fixed** &mdash; try to reproduce it using the
   latest `master` branch in the repository.

3. **Isolate the problem** &mdash; ideally create a reduced test case.

A good bug report shouldn't leave others needing to chase you up for more
information. Please try to be as detailed as possible in your report. What is
your environment? What steps will reproduce the issue? What OS experiences the
problem? What would you expect to be the outcome? All these details will help
people to fix any potential bugs.

Example:

> Short and descriptive example bug report title
>
> A summary of the issue and the browser/OS environment in which it occurs. If
> suitable, include the steps required to reproduce the bug.
>
> 1. This is the first step
> 2. This is the second step
> 3. Further steps, etc.
>
> `<url>` - a link to the reduced test case
>
> Any other information you want to share that is relevant to the issue being
> reported. This might include the lines of code that you have identified as
> causing the bug, and potential solutions (and your opinions on their
> merits).

### Feature requests

Feature requests are welcome. But take a moment to find out whether your idea
fits with the scope and aims of the project. You might want to check if your feature is already on the [menue](https://github.com/DSD-DBS/capellambse-context-diagrams/projects?type=beta).

A frequently appearing kind of requested feature is to add `.context_diagram` to more ModelObjects. Please check if the class-type of your requested ModelObject is not [already implemented](https://capellambse-context-diagrams.readthedocs.io/#features). Then it is important to describe how the context of this specific ModelObject is formed and how it shall be collected. There are 3 stages in building context diagrams:

  1. Collect the context data.
  2. Layouting via elkjs, size and position calculation.
  3. Serialization of ELKOutputData to aird elements.

For the 2nd stage it is most certainly useful to use the interactive JSON editor from the [ELK demonstrator](https://rtsys.informatik.uni-kiel.de/elklive/) to check the positioning and routing. There you can test and see the behavior of configurations for ELKInput elements.

It's up to *you* to make a strong case to convince the project's developers of the merits of your feature. Please provide as much detail and context as possible.

## Known limitations and future challenges

Dealing with hierarchical diagrams/graphs is complex and needs further research for the right configuration parameters for ELK such that the orthogonal routing is working as intended. The edges that connect a subcomponent (A) with a component (B) outside of component (C) (parent of A) need to be global edges (i.e. listed in the edges array in the group component their source and target are located). If there is no joint parent component to be found for source and target of an edge this edge is a global edge. It should be listed in the first edges container.

# Ground Rules

Introducing a new feature also shares responsibility to add tests and documentation. Tests will help to maintain the correctness of your feature and the latter will explain the intent and showcase the capabilities of your contributions. Very often the examples given in the documentation are stemming from the respective test case. Here we are using pytest to automate unit and integration tests.

Example:

> Integration test for capability context diagrams seen in `tests/test_capability_diagrams.py`:
>
> ```python
> # SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
> # SPDX-License-Identifier: Apache-2.0
>
> import capellambse
> import pytest
> from capellambse.model.layers import ctx, oa
>
> TEST_TYPES = (oa.OperationalCapability, ctx.Capability, ctx.Mission)
>
>
> @pytest.mark.parametrize(
>     "uuid",
>     [
>         pytest.param(
>             "da08ddb6-92ba-4c3b-956a-017424dbfe85", id="OperationalCapability"
>         ),
>         pytest.param("9390b7d5-598a-42db-bef8-23677e45ba06", id="Capability"),
>         pytest.param("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6", id="Mission"),
>     ],
> )
> def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
>     obj = model.by_uuid(uuid)
>
>     diag = obj.context_diagram
>
>     assert isinstance(obj, TEST_TYPES)
>     assert diag.nodes
> ```
>
> The OperationalCapability, Capability and Mission were added to the test model (`tests/data/ContextDiagram.capella`) via Capella 5.2 and the new `.context_diagram` generation is tested.
>
> Documentation can look like this `docs/index.md`:
> ```markdown
> - ??? example "[`ctx.Mission`][capellambse.metamodel.sa.Mission] (MCB)"
>
>         ``` py
>         import capellambse
>
>         model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
>         diag = model.by_uuid("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6").context_diagram
>         diag.render("svgdiagram").save(pretty=True)
>         ```
>         <figure markdown>
>             <img src="assets/images/Context of Top secret.svg" width="1000000">
>             <figcaption>Context diagram of Mission Top secret with type [MCB]</figcaption>
>         </figure>
> ```
>
> Make sure to work urself into [material for mkdocs](https://squidfunk.github.io/mkdocs-material/reference/) as we are using several extensions like admonitions and figure markdown. The used diagram SVG should be added to the `docs/gen_images.py` script such that mkdocs generates it while building the documentation.

To meet needed prerequisites execute
```bash
uv pip install
```

You can then run all tests in the terminal by executing

```bash
uv run pytest
```

or if you are using VSCode you can use the integrated test functionality via task profiles.

Additionally we want to keep being REUSE-compliant (i.e. license compliant). We are using the [reuse.software](https://reuse.software/tutorial/) python tool to check for compliancy and add license headers where they are missing.

We are also using pre-commit hooks as seen in the `.pre-commit-config.yaml`. It is wise to install pre-commit such that your commits are bullit-proof against the checks that are also executed in the workflow on GitHub.

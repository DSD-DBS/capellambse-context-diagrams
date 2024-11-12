<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Custom Diagram

`Custom diagram`s let's you create custom diagrams based on the data in the model. You define the data collection using a YAML-based declarative language.
You can access `.custom_diagram` on any supported model element.

## Example

Here is an example YAML file that declares a context diagram:

```yaml
get:
    - name: inputs
    include:
        - name: exchanges
        - name: links
    - name: outputs
    include:
        - name: exchanges
        - name: links
    - name: ports
    include:
        - name: exchanges
        - name: links
```

## Collector definition

-   `get` element at attribute defined in `name`
-   `include` element at attribute defined in `name` or all elements if element is a list as boxes or edges
-   `filter` elements if element is a list
-   `repeat` elements if for n times

## API Usage

```python
import capellambse
import yaml

my_model = capellambse.MelodyModel(...)
my_element = my_model.by_uuid(...)
my_yaml = "..."

my_element.custom_diagram(collect=yaml.safe_load(my_yaml)).render("svgdiagram").save(pretty=True)
```

## Supported Elements

-   [`sa.SystemFunction`][capellambse.metamodel.sa.SystemFunction]
-   [`cs.PhysicalLink`][capellambse.metamodel.cs.PhysicalFunction]
-   [`la.LogicalFunction`][capellambse.metamodel.la.LogicalFunction]
-   [`pa.PhysicalFunction`][capellambse.metamodel.pa.PhysicalFunction]
-   [`fa.ComponentExchange`][capellambse.metamodel.fa.ComponentExchange]

## Check out the code

To understand the collection have a look into the
[`cable_tree`][capellambse_context_diagrams.collectors.cable_tree]
module.

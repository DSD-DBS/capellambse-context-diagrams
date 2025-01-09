// SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
// SPDX-License-Identifier: Apache-2.0

const elkgraphsprotty = require("./elkgraph-to-sprotty");
const ELK = require("elkjs");
const elk = new ELK();

var fs = require("fs");
var stdinBuffer = fs.readFileSync(0);

const elk_stdin = JSON.parse(stdinBuffer.toString());

elk
  .layout(elk_stdin)
  .then((res) =>
    console.log(
      JSON.stringify(new elkgraphsprotty.ElkGraphJsonToSprotty().transform(res))
    )
  )
  .catch(console.error);

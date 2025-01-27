// SPDX-FileCopyrightText: 2024 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
// SPDX-License-Identifier: Apache-2.0

import { createInterface } from "node:readline";
import process from "node:process";
import ELK from "npm:elkjs";
import { ElkGraphJsonToSprotty } from "./elkgraph-to-sprotty.ts";

// @ts-ignore Deno doesn't find this type for some reason
const elk = new ELK();

console.log("--- ELK layouter started ---");

for await (const line of createInterface({ input: process.stdin })) {
  const input = JSON.parse(line);
  const layouted = await elk.layout(input);
  const transformed = new ElkGraphJsonToSprotty().transform(layouted);
  console.log(JSON.stringify(transformed));
}

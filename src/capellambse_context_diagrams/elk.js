// SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
// SPDX-License-Identifier: Apache-2.0

const http = require("http");
const elkgraphsprotty = require("./elkgraph-to-sprotty");
const ELK = require("elkjs");
const elk = new ELK();

const server = http.createServer((req, res) => {
  if (req.method === "POST") {
    let body = "";

    req.on("data", chunk => {
      body += chunk.toString();
    });

    req.on("end", () => {
      try {
        const elk_stdin = JSON.parse(body);

        elk.layout(elk_stdin)
          .then(result => {
            const transformedResult = new elkgraphsprotty.ElkGraphJsonToSprotty().transform(result);
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify(transformedResult));
          })
          .catch(error => {
            console.error(error);
            res.writeHead(500, { "Content-Type": "text/plain" });
            res.end("Internal Server Error");
          });
      } catch (error) {
        console.error(error);
        res.writeHead(400, { "Content-Type": "text/plain" });
        res.end("Bad Request");
      }
    });
  } else {
    res.writeHead(405, { "Content-Type": "text/plain" });
    res.end("Method Not Allowed");
  }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server is listening on port ${PORT}`);
});

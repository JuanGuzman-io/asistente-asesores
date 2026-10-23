#!/bin/sh
node -v
npm view vite@8.3.5 engines.node; npm view vitest@5.0.5 engines.node; npm view jsdom@30.1.3 engines.node
node -e 'const [a,b]=process.versions.node.split(".").map(Number); console.log(a===22 && b>=22 ? "OK: cumple ^22.22.2" : "FALLA")'

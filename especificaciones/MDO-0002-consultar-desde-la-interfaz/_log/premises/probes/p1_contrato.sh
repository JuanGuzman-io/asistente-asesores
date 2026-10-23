#!/bin/sh
git show "feat/MDO-0001-consultar-la-base-documental-con-fuentes:especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md" | sed -n '/^## Contract/,/^## Risks/p'

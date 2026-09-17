# Adopted PYMSS WebUI

This `hub` branch preserves the administrator's running Chinese PYMSS workbench.
Upstream is `pymss-project/pymss-webui`; the organization fork is
`FC-TTD/pymss-webui`. Native provider/runtime and deployment belong to
`FC-TTD/pymss` on its `hub` branch.

The initial adopted UI changes are commit `fcbd50b`; rebuilding with the existing
lockfile reproduced the live `index.html`, JS and CSS byte-for-byte. Model
selection, advisory catalog, batch downloads, audio preview, parameters and
output controls are preserved. No UI redesign is part of model-pool adoption.

Run `npm ci && npm run build`. For the 352-entry advisory consistency check,
point explicitly at the adopted provider checkout:

```sh
PYMSS_SOURCE_ROOT=/absolute/path/to/pymss npm run check:advisory
```

Generated `dist/`, node_modules, source audio, downloaded weights and output
files remain outside Git. Provider images retain the verified static bundle;
future UI releases must record this repository's source commit and artifact hash.

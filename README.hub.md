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

## Film media candidate

The `codex/film-media-import` branch adds source-preserving CPU video ingest, enumerated audio tracks and cached stereo extraction. First audio stream is default; selection is explicit. No video export or device/offload substitution. The existing native worker and managed transport remain unchanged. Long audio uses bounded 240-second model windows with 2-second context and a 1-second output crossfade, exact final frame checks, and RF64 when required. Inputs are no longer capped at600seconds; source file cap16GiB and batch cap64GiB/20files. Long-film acceptance must include selected stream identity, center/surround/LFE retention and full-length output; health alone is insufficient. Interrupted/unknown managed executions must not be automatically replayed.

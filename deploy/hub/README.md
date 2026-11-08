# Scoped song transport

Build runtime only from committed read-only snapshot through the registered docker_ci_cd launcher on Nest. Keep the actual Stage runtime image, management deployment, mounts/ports and non-song worker path. Three song models use existing managed PYMSS native load+inference with batch_size1 and mandatory model identity; float output is resampled by the original CPU scipy function and written 48k/PCM24. No shared GPU provider, SDK, Hub, frontend or other model rebuild. Verify original model assets/effective config, three native outputs, pending/drain and historical Range before promotion.

2026-10-27: Stage runtime promoted to sha256:77aab4346028ddfb2e17f7c96f5ddab8ffdbd5b3fce17dc90c9b4f0810aeca98, API sourcee1576ce. Song load/inference now use http://model-gateway/internal/native/music-separation with an exact-grant internal key mounted read-only at /run/music-gateway.key. Browser receives no key. Existing PYMSS model is the sole GPU owner; no SDK/provider rebuild. Three CLI sample models passed; promoted API returned two 6s/48k/PCM24 tracks, 900 peaks and Range206. Native output SHA matched the previous direct-native transport. Management/evidence: Stage /opt/music-hub-release-20261027/studio-release-queue. Formal frontend, chain, model mounts and non-song device assignment unchanged. Original audio results and old msst/ui consumers still return media.

## Concurrent LAN separation and channel-preserving exports

`STUDIO_MAX_ACTIVE_JOBS` accepts 1–4 (default 1). Keep one ASGI worker. Raise
the setting only on the runtime whose GPU and model mix passed concurrent
inference checks. A job or a batch occupies one slot. Direct CUDA workers
reserve estimated memory before launch, retain the shared volume lock for
compatibility with older exclusive workers, and release the reservation on exit.
A GPU without capacity may still delay an accepted job. Gateway song model
admission and switching retain their own concurrency policy.

Media extraction preserves mono and stereo, with the existing surround
downmix for inputs above two channels. New WAV exports match the prepared
source channel count, including long-file joins, at 48 kHz / PCM24.

2026-11-04 Stage isolated smoke used runtime base
`sha256:8143933a72a63d950d89d1111908b5f3757682765a3919a03def1eb008fdce1c`,
candidate runtime sources, an isolated job store, and read-only model mounts.
Four independent batch start requests returned success and reached the native
inference section concurrently on Stage GPU0 using HTDemucs4. Each completed in
7.4–7.7 seconds, with 611730944 peak allocated CUDA bytes per worker. Downloads
had 1/2/1/2 channels and 1152000 frames each. GPU0 free memory returned to the
pre-test 5519 MiB. The test covers one model and one host with four simultaneous
API clients. Mixed heavier models, managed song concurrency, and four physical
workstations remain to be verified.

## Deshimmer music repair

Set `STUDIO_ENABLE_DESHIMMER=1` on the selected runtime to expose `deshimmer`
and its `restored` track through the existing studio job and batch routes.
This uses the MIT-licensed Deshimmer DSP at upstream commit
`76d77e38d7802c31d952ad99a6c8b256042e59ca` with a checksum-pinned archive,
without model weights, Gradio, mastering, or an optimizer. One CPU repair
process runs at a time and shares the ordinary application admission limit.
Long audio reuses the existing windowed render with 60-second windows,
context, and crossfades. Outputs are 48 kHz PCM24 WAV and follow the source
mono/stereo layout. Existing multichannel downmix rules still apply.

## Concurrent uploads

Independent workbench batches can upload, reuse an asset, or start processing
while a slow client is still uploading to a different batch. State updates
within a batch remain ordered. Video audio preparation is scoped to the source
media so unrelated media can be prepared independently. Keep one ASGI worker
for the shared file-backed state. GPU admission and Deshimmer CPU scheduling
are separate from upload concurrency.

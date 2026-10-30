## 当前显存抢占修复版本（2026-10-25）

Stage17896 release **h-dc49c42eaaba679f**；Webaa94c4601eaf13eb4a6fc65e84531d3149ea1581d8d338cf9aa88abb6602dbe6/runtime00667f6572e35c1c91522f58714bd64fc7ca97439be5a9bd34fed4d4e4e24bf4，管理/opt/pymss-ui-preview/releases/h-dc49c42eaaba679f。resources.py在原worker外做GPU显存等待、有限OOM重试、每次独立日志、成功峰值档案。模型权重/精度/offload/设备策略不变；应用固定STUDIO_GPU_UUID避免CDI对PID1 NVIDIA_VISIBLE_DEVICES=void改写，部署必须与原reservationUUID一致。

修复自身等待中的任务时，deploy.sh显式EXPECTED_WAITING_JOB允许且仅允许唯一活动job ID匹配并处于waiting；之后仍必须无worker/smoke进程。普通active任务继续阻止部署。此参数不是任意打断任务授权，本次仅用于本聊天发起的故障原批次重试等待。输入、历史失败日志保留。实际原batch546133be93ad45488d2a20e7d733a762整曲9.97s成功2轨/48kPCM24，详情../../design-qa.md。回退上一稳定he925使用当前固定网段Compose，不删NAS数据与新profile；未执行。以下是历史记录。

## 当前批量操作版本（2026-10-25）

release **h-e92556e09ea24f95**，管理目录/opt/pymss-ui-preview/releases/h-e92556e09ea24f95；Web sha256:f70c764fd749aebc0caa9ebbb3aef63d0d82999ed4fca6a5981cb0ed875718c4，runtime sha256:45b7c7f526338f2bcdb79ff6a4585ae5a83586e6a8fdba227e6acb96f35efded。受管理deploy.sh，仍为隔离Stage17896，Hub未更新。UI/runtime源码快照未commit/push，不作formal发布。

新增runtime/batch.py安装batches/inputs/start/read及exports路由。复用原生单worker GPU槽，批次串行、按文件持久job；刷新恢复，不重复成功项。worker.py未变，37/38注册状态保持。/data/batches与/data/exports位于既有NAS应用目录，ZIP按输入身份缓存，CPU分块写不占GPU；无自动清理。20文件/2GiB合计、每文件512MiB/10分钟限制，导出≤400轨。

UI移除授权/内部测试说明、可用库按钮允许忙碌中选择并保留输入；新旧任务按原快照运行。用户明确恢复ZIP，HTTP下载限制仍未解决，生成链接不等于落盘通过。检查报告../../design-qa.md，证据/tmp/pymss-batch-qa/。Chrome文件上传扩展权限缺失改用独立IAB验证，未变更权限。

回退：通过同一Compose、保留当前显式10.35.0.0/24，仅PREVIEW_RELEASE设为上一稳定h-3c60e8ce73ab2a17，up -d --no-build --pull never；旧UI无batch/export入口但旧job和新增batch/export持久数据仍保留，不回滚/删数据。回滚未执行。以下条目是历史发布记录。

# PYMSS 新版工作台与真实模型 Stage 预览

2026-10-25。入口 [http://ttd-stage:17896/ui/](http://ttd-stage:17896/ui/)。当前release **h-3c60e8ce73ab2a17**。
用户已授权界面精修、移除样例、修正选模、下拉及置顶，以及本轮模型下载和可用性验证。正式Hub发布仍等用户测试确认。

## 最新分类、稳定卡片与波形

release h-3c60e8ce73ab2a17；37可用/38注册。卡片点击不排序/不移除旧卡，下拉浮层不占位，实际鼠标页面位置不变。保留人声/伴奏两分类及质量排序；乐器父项点击延展，取消常驻细类行；影视包含双轨及DME，purpose存盘。2个AliceN真实CUDA通过，原35 worker/artifact指纹保留。

独立waveform.py从PCM分区读取900峰值，写源文件旁.waveform-v1-900.json缓存，按大小+mtime失效、原子替换；不改原文件/GPUworker，不让前端整曲解码。API新结果和旧结果都补waveform_url/bytes。238秒旧双轨无需重跑，实际点波形→119秒/50%并试听通过。purpose-aware labels确保影视other是其余声音，不伪装伴奏或三轨。

固定准备/manifest/验证备份在/opt/pymss-ui-preview/model-prep/cinema-20261025；小配置下载重试按固定Gitblob9889301eceec52a85fb799161ab2aac5039734c5校验，原权重不改。模型输入锁38。最新证据stable-cinema-waveform-verification.json、cinema-waveform-api-verification.json及../../design-qa.md。家庭32来源制品/API37/238秒波形通过；实际家庭Mac/手机及Chrome下载限制未完成。下文35/27/19是历史基础。

## 最新分轨能力与乐器更新

release h-3c60e8ce73ab2a17；35可用/36注册。330卡作者链接移除，显示实际分轨与文件大小；未就绪只写目录目标。主页2当前+3经典，当前选择优先；16用途/乐器入口展开，空闲cursor:pointer，只有真实busy等待。8乐器模型真实CUDA成功，SW6浏览器任务f54ced789023403ea9b3df6ebd5b3cf9成功输出6条48kPCM24双声道6秒音轨。XL四轨在现有负载下GPU OOM，未改precision/offload/CPU或停止其他服务，显式显存不足，不可选。worker不变，前27验证保留。新证据本release/capabilities-verification.json及instrument-models-verification.json；旧27/19描述属于历史基础。

固定模型准备/备份在/opt/pymss-ui-preview/model-prep/instruments-20261025，原缓存只读。家庭32来源资源/版本/API35通过；实际家庭Mac/新移动控件未验收。Chrome下载限制保持partial。下文旧模型库更新为历史，最新界面见../../design-qa.md。

## 本轮模型库更新（2026-10-25）

当前release h-3c60e8ce73ab2a17，27/27真实可用；330目录默认按8组全部平铺，原目录说明原文/完整文件名可见可搜索，7用途展开，每卡“使用此模型处理”返回正确工作台并保留文件。当前模型按钮不再禁用。右侧更多列表420px，可滚动和拖动调整高度，包含第一版经典模型，质量排序、年份只作标签。

新增8个经典版本真实6秒歌曲CUDA全部通过；权重复用旧缓存，固定来源/校验与配置在runtime/models-lock.json。未改worker，保留前19验证。Becruily浏览器真实任务e63e0dcf941248b88f735f9c8961f006完成双轨，48kHz/PCM24/288000帧。家庭32来源最终制品hash/API27ready、desktop/390布局和真实拖动/跳转通过。最新证据本release/grouped-library-verification.json、legacy-models-verification.json及../../design-qa.md；下文19模型/整曲为历史基础证据。

此前Chrome直链下载限制保持partial，未绕过。准备资产/备份/日志在/opt/pymss-ui-preview/model-prep/legacy-20261025，不编辑不可变release输入。只读共享缓存，preview自有配置及结果持久保留。默认仍同一GPU0，无精度/offload变化。Hub未发布。

## 版本与来源

| 项 | 当前值 |
|---|---|
| Lane | ttd-stage-docker-preview，仅内网server:port |
| UI组织fork/基线 | FC-TTD/pymss-webui hub /771d394c7ad313b2cd78f0c754a61907ee4a4336，带本任务未提交改动 |
| Provider组织fork/基线 | FC-TTD/pymss hub /90ebd6e6cff86e081189c400f15735a2b2a23fe2，原checkout未改动 |
| Stage管理目录 | /opt/pymss-ui-preview/releases/h-3c60e8ce73ab2a17 |
| Compose项目 | pymss-ui-preview |
| Web容器 / image | pymss-ui-preview-web /sha256:018a73273795f17a21007bd4e64283c4a3b764015a4235b7569413774b625f47 |
| Runtime容器 / image | pymss-preview-runtime /sha256:c01813aa8cd60a64215b8c676824827ff9b1091f2c4c9e52c1c8c693c8697a7c |
| 前端基镜像 | nginx@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 |
| 模型运行基镜像 | registry.ttd/pymss/native@sha256:a5bb212a097c35e9d99cb6eefd33323aaa82717530992976c282ef61cd9b672a |
| 核心依赖 | 原Torch2.7.1+cu128；pymss-core0.1.8；DBS官方代码ff526463a58ee0278e7bd05c4b8bce112b743e34；固定wheel版本及SHA在bundle输入清单 |

构建输入、provider源码、DBS源码、wheel及hash均保存在不可变release bundle。仅preview未提交快照，不冒充formal发布。未commit/push。
静态UI和后端分层构建，复用已缓存固定原生CUDA镜像；依赖wheel层在源码更新时复用，不重新下载权重或构建其他模型服务。

## 运行与数据边界

- 前端仅192.168.100.18:17896→8080；后端8000只在此Compose网络可达，Web同源代理/api/studio/。没有注册域名、公开公网、改DNS/Caddy/防火墙/认证。
- 网络显式10.35.0.0/24，已核验与Docker和真实路由不重叠；家庭32网段回程via192.168.100.2 deveth0。共享规则唯一正文是TTD:/00_项目/共享测试部署标准.md v1.2。
- Web非root101/只读64MiB/0.5CPU；Runtime只读rootfs、16GiB/6CPU、单API worker，tmpfs缓存，unless-stopped。API进程只管理文件/任务，每次分离单独GPU子进程；退出即释放本请求模型分配，文件结果保留。
- 只挂Stage GPU0 GPU-731f9bc4-8979-6abb-98e1-c2dae293693e。发布前可用5519MiB；19个模型在此与既有负载共用条件下实测通过。保持原CUDA精度/AMP配置，不切CPU推理或offload；batch_size=1使用原生参数降低同时处理的块数，不改变模型或原配置音频块长。
- 原 /mnt/TTD-Data/pymss/models **只读**。发现管理员改过部分配置，保留原文件，在预览自有目录下载固定来源配置，不覆盖Hub缓存。
- 新权重、下载/转换校验表：/mnt/TTD-Data/pymss-ui-preview。模型目录不烘焙进镜像。
- 测试输入、任务状态及WAV结果：/mnt/TTD/04_应用/pymss-ui-preview，已核实共享挂载。上传即进入此测试服务，不再声称只在浏览器读取；未添加自动删除策略。旧下载片段/转换原始权重保留为本任务审计材料。
- /healthz报告busy；一次只接纳一个分离任务，第二请求429。所有worker共享文件锁以避免同时加载模型；后台状态落盘，服务重启时将未完成任务明确标失败，不伪装已完成。模型切换不会改正式Hub全局选择。

## 模型与输出

本轮19个版本均有权重/配置/来源/大小/SHA256和真实6秒歌曲输出证据，19模型功能验证详见历史h-81e06e57ef1c5261的model-verification.md、verified-models.json、real-model-smoke-details.json；当前worker/权重指纹未变，现场19ready。固定权重仍见runtime/models-lock.json。

Leap XE双款固定作者revision4e47d6662ae82eaa8b4ac4329fe66099a843b48e；DBS-TIGER权重固定22da7d4cd3ea63f9365181008bff1c0d2ab6fb2b，保持原生mono，不伪装立体声。
BandIt v2多语种来自官方Zenodo12701995；原始MD5 fea2868787551b0cff36cfcf7c3622a3，抽取state_dict时2946个tensor名称/形状严格匹配64-band配置，记录移除model.前缀与新SHA，然后再CUDA实测。未使用访问受限的第三方链接作为唯一来源。
SCNet XL DNR在所给官方来源没有对应权重/配置，模型库明确说明，未以MUSDB音乐四轨替代影视DNR。

可使用标记依赖下载校验与实际worker源码/权重指纹一致的通过记录；不是硬编码已就绪。原生other/instrument在已核实的歌曲双轨配置中显示伴奏，内部stem ID保持以便准确提交；下载文件使用中文音轨名。Karaoke使用主唱目标/和声及其余声音，不承诺残差是纯和声。统一导出48kHz/PCM24，时长按真实输入保留。

## 验证与范围

- 19/19 CUDA真实6秒歌曲分离，各输出48000Hz/PCM24/288000frames；立体声模型2声道，DBS1声道。GPU子进程结束后Stage GPU0回到既有6393MiB基线；其他卡保持。
- API实际Leap XE伴奏提交202、第二并发429、无效stem400、未知模型409、结果/下载200；输出中文标签与内部stem对应，双轨帧数、位深、声道实读通过。历史证据h-81e06e57ef1c5261/api-verification.json；本轮整曲证据../../../pymss-ui-evidence/long-song-final-verification.json，/models有19个有效记录。
- 历史Chrome6秒Blob WAV下载通过；本轮改为整轨URL流式播放与直链附件，238秒双轨播放/末段定位/刷新恢复通过。公司Chrome直链WAV显示失败-已阻止，当前浏览器下载**未通过**；未绕过警告/扩展公网/改变认证。ZIP继续移除。
- 本轮默认3张质量推荐卡片、其余下拉，只有1个aria-checked=true；置顶刷新后仍优先、试验置顶已撤销；正文/控件收紧，中文最小12px。实际桌面和390×844 DevTools排布无横向溢出；真实手机浏览器未测。
- 家庭路由器绑定192.168.32.2，对当前版本入口/版本文件/全部JS与CSS/API19就绪均200，字节hash对齐bundle。实际家庭Mac浏览器NOT_RUN。
- Svelte诊断0错误0警告，目录/筛选/无演示/单选架构检查、default/design构建与diff-check通过。浏览器最终无应用error/warn。界面QA在../../design-qa.md；截图/证明在work/pymss-ui-evidence。

整曲故障修复：nginx默认缓冲写满16MiB的/tmp，68.5MB WAV被截断；现关闭响应缓冲/代理临时文件。新238秒真实歌曲任务27f3aaf6e7c84100976b946a4ffc4605双轨18.88秒成功，家庭32来源完整下载两轨SHA一致，尾部Range206、48kHz/PCM24/11,424,000帧。/tmp仅4KB、无OOM/重启，GPU回基线。原用户结果b7cb240e0dbf4d67bd756a26e1e61bd8可直接恢复。默认可用范围/质量排序，一句优势，依据../../quality-review.md。

结论：**real-inference-ok（独立Stage预览、19个模型功能冒烟和整曲播放恢复通过，浏览器直链下载仍被拦截）**。不代表全部330目录均已接入、用户素材音质已获确认、完整三端共享、宿主重启或线上回滚已经验收；正式Hub未发布。

## 重复发布与恢复

初次准备模型使用runtime/prepare_models.py及固定HF元数据；BandIt多语种使用download_bandit_multi.py和convert_bandit_multi.py的官方校验/严格转换。权重准备与CUDA实测分开；不把下载完成直接当可使用。

当前版本更新：

```sh
EXPECTED_PREVIEW_RELEASE=h-3c60e8ce73ab2a17 deploy/preview/deploy.sh
```

脚本核对owner/旧release/活动任务/IPAM，先构建两个不可变镜像，再Compose更新；Web等待Runtime healthy，避免启动DNS竞争。固定源快照和制品保留在stage/local release目录。

需回退镜像时继续用当前固定10.35网络的Compose与已有数据挂载。例如回到前一版h-623bef0efb56c63e（含分类和波形）：

```sh
ssh root@ttd-stage 'cd /opt/pymss-ui-preview/releases/h-3c60e8ce73ab2a17 && PREVIEW_RELEASE=h-623bef0efb56c63e docker compose --env-file .env -f compose.yaml up -d --no-build --pull never'
```

本次未实际回滚，不恢复旧自动网段，不删除权重/任务/卷，不修改任何正式Hub实例。下一步由用户测试界面和自身素材，再决定正式集成/发布。

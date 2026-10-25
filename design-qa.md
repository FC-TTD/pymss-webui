# 组合入口、试听排序与上传复用（2026-10-25）

当前Stage17896 **h-bd63eb3d3ceeebfe**。用户已请求最终版本合并到原MSST入口，首页名称“音频分离”、备注“MSST 和 PYMSS”、默认PYMSS；随后要求InstVox Duality v2与BS Roformer12.97在duo前两，以及多模型比较不要重复上传。**整合/复用已Stage验证，正式MSST与首页尚未切换；用户已单独授权本次提交并继续发布；当前执行正式发布，完成状态见后续正式验收记录。未push。**

## 实现与边界

- AudioWorkspace.svelte固定64px顶栏、两个明显导航，默认PYMSS，MSST首次点击才加载原http://msst/?native=msst iframe；切回只隐藏，不卸载Studio/原生iframe，保留输入。明确tool=msst直链可打开MSST，不记录为默认。PYMSS原工作台、单选稳定、模型库/原说明/波形/ZIP/显存等待均保留。
- 根据用户本次真实试听，duo质量顺序首两款改为InstVox Duality v2、BS Roformer12.97，非年份排序；用户置顶仍可覆盖默认偏好。默认新选择为InstVox，恢复任务尊重原模型。baseModelCards仍包含新旧模型，首两款直接平铺。
- 原来start每次uploadBatch全部文件，现首次上传后取input_asset_id，随后POST batch/reuse仅传引用。server job的input直接指向同一只读原输入，独立输出目录，无重传/无音频复制。上传边读边SHA；新旧job API动态补input_url/bytes/duration，刷新可恢复输入并从服务端Range试听。源UUID校验、路径范围、缺失源、每批20文件/2GiB、模型/分轨验证保留；没有按同名文件猜测身份或静默替换源。
- publish.py/compose及merged-route fixture已准备：新增64MiB/.5CPU独立只读CPU入口，用同一个经过测试的静态镜像加入既有backend网络和集群caddy overlay；源业务标签只处理私有msst的根/UI/StudioAPI，native=msst与__gradio__继续原Hub入口，不重启/替换MSST或新增GPU实例。不改Caddy全局/DNS/认证/公网。首页工具通过原links API仅修改目标text/title，保留其他实时条目，要求durable-before备份。
- 正式门禁：publish.py要求单独授权的完整源码commit，所有候选本仓库构建输入与git show逐字节匹配、manifest内容哈希匹配、脚本与Compose来自同一commit，backend仍是同一验证版本。当前仅准备，未执行--apply。私有Caddy实际多源合并/新CPU overlay连接仍待正式阶段验证，不能把fixture适配当成上线。
- 发布前检查发现nginx相对跳转会自动拼内部8080端口，现absolute_redirect off，/和/ui均保留batch/tool query并返回相对/ui/；两个实际HEAD Location均正确。部署脚本空EXPECTED_WAITING_JOB经SSH参数省略导致$4未绑定，已用${4:-}修复，普通空参数部署通过。

## 实际验收

| 检查 | 结果 |
|---|---|
| Stage身份/非空/遮罩 | 音频分离·PYMSS/MSST，真实页面，无错误层 |
| 双导航/保留状态 | PYMSS→MSST真实原Gradio界面→PYMSS，输入仍1、iframe保留；默认PYMSS |
| 指定排序 | duo实际DOM前两为InstVox/BS12.97，切卡不重排；model330/37ready38注册不变 |
| 整曲复用 | 原用户248.56秒/9944883字节音频，切BS12.97，batch f36e1bf412ab408ab157d189511f1f1f成功2轨；uploaded_bytes0/reused_files1，canonical源1a9f758c3a994b23b36277bda465e32f，原输入SHA不变 |
| 首次上传→第二模型 | IAB真实导入6秒片段，InstVox batch7020be12c0ff4945b14c414a04cbba10上传1058572字节、成功；切BS batchc1f80c985a8346b7a3bd05366a74a063成功，uploaded_bytes0/reused_files1，完全同asset ba56255315a746b5a5a06e91a1723d58 |
| 服务端效率 | 两个reuse job目录均不存在input.audio副本，input直接引用原文件；新输出独立；不是客户端缓存伪进度 |
| 刷新 | 第二模型完成后reload恢复1输入、源URL/6秒播放器、PYMSS默认与结果；服务器源Range206/128字节通过 |
| CPU隔离验证 | 连续引用归一到canonical、零音频复制、原SHA不变、遍历及源缺失拒绝；不计模型推理证据 |
| 桌面/手机 | 1280×720/390×844，无横向溢出，新页面可见中文≥12px，两个手机导航72px可点 |
| 控制台 | 组合页/PYMSS无应用error；原MSST独立页面也有22条相同Tabs hidden warning，嵌入沿用，未把旧原生warning归为新增工作台错误 |
| 构建源码 | Svelte0/0、330质量/去重/稳定检查、default/design构建、Python语法、diff检查通过；既有大chunk提示保留。worker.py完全未变 |
| 部署材料 | Compose config --quiet通过；Caddy2适配fixture通过，仅未格式化提示，未加载实际配置；正式发布脚本/首页脚本语法通过、门禁未绕过 |
| 家庭方向 | 最终release/HTML/JS/CSS哈希及Range可用；路由器32.2绑定方向，实际家庭Mac/手机NOT_RUN。固定10.35/24、回程via100.2保持 |

证据/tmp/audio-separation-unified-qa/，04-final-ranked-input.png、02-msst-tab.png、03-mobile.png、reuse-proof.json、reused-bs-batch.json、final-verification.json。正式msst原容器、首页tools.msst线上文本仍MSST已现场复核；源ttd-file仅text/title两字段改好，href仍http://msst/。没有提交/推送/正式切换。当前partial仅因提交授权尚待，Stage三项主线已完成。

以下保留历史QA。

---

# 显存抢占排查与原批次恢复（2026-10-25）

当前Stage17896 **h-dc49c42eaaba679f**；Websha256:aa94c4601eaf13eb4a6fc65e84531d3149ea1581d8d338cf9aa88abb6602dbe6，runtime00667f6572e35c1c91522f58714bd64fc7ca97439be5a9bd34fed4d4e4e24bf4。未commit/push/正式Hub发布。

- 用户批次546133be93ad45488d2a20e7d733a762 / job1a9f758c3a994b23b36277bda465e32f，InstVox Duality v2。原失败14:09（UTC日志06:09）：模型加载model.to(cuda)阶段，原常驻PID5504约6.23GiB、额外临时PID344816约3.68GiB、当前workerPID344994约1.69GiB，free13.75MiB。额外PID现已结束，具体服务归属未能现场确认；没有据猜测停其他服务。当前baselineGPU0=6393MiB，其他7681/11413不变。原失败job/log备份/opt/pymss-ui-preview/incident-20261025-546133。
- 新resources.py在启动GPU worker前读取固定卡的空闲显存，依据已验证分离峰值+512MiB余量估算需求，成功后记录真实整曲峰值至/data/gpu-requirements.json。不足时持久waiting、保留输入、最多等10分钟；容量抢占导致原生OOM时先等待旧worker退出释放，再有限自动重试2次。非OOM不重复处理，独立尝试日志保留。worker.py/模型/精度/chunk/offload/原GPU分工完全未改，37/38验证保留。
- 兼容坑：CDI启动PID1的NVIDIA_VISIBLE_DEVICES实际为void，而docker exec看到的是配置UUID；初版预检因此读不到状态。已新增STUDIO_GPU_UUID为原固定GPU0 UUID，和Compose reservation保持一致；实际应用已从waiting进入CUDA并成功，不能仅用docker exec测试代替PID1环境核对。部署脚本仅允许显式EXPECTED_WAITING_JOB且唯一活动job恰为该waiting ID/无GPUworker时修复自身等待任务，不打断其他任务。中间h1ad被最终版本取代。
- 原链接已原位恢复，同job/model/input，不重传。实际整曲248.56秒、9.97秒成功，retry_count0，Torch peak3689458176 bytes（之后需求更新为4031MiB）。两轨均11930880帧/48k/stereo/PCM24、71585324字节；输入SHA973006d0defdeeef07456a24a92cb65bb04b8f09cecee6466827ed5f252a5e96不变。每轨真实900峰值/时长及Range206通过；UI原链接模型InstVox、全部分离完成、1文件2轨、无error/warn/横向溢出。
- CPU隔离测试通过：不足先等、瞬时OOM后成功、最多3次、非OOM不重试、等待超时/探测失败不盲启、旧日志不覆盖；模拟void+固定UUID探测通过。没有人为占用其他GPU来制造线上OOM；资源抢占路径是CPU状态测试，本次真实重试在资源已恢复时完成。Svelte0/0/source330/default+designbuild/diffcheck通过，已有chunk提示保留。
- 家庭路由器绑定32.2已验证最终release/HTML/JS/CSS字节哈希及同批次成功结果；实际家庭Mac/手机/新下载落盘/宿主重启/回滚NOT_RUN。固定10.35/24与32.214回程via100.2不变，容器OOMfalse/restart0（实例重建不等于宿主重启）。浏览器HTTP保存限制未在本轮宣称解决。

证据/tmp/pymss-vram-qa/{cpu-checks.json,recovered-batch.json,recovered-results.png,final-verification.json,deploy-final.log}。回滚用当前固定IPAM Compose+上一稳定h-e92556e09ea24f95镜像，保留所有输入/输出/batches/exports/profile；新STUDIO_GPU_UUID旧镜像忽略，无数据schema回滚。未执行回滚。当前用户报错已恢复/真实主线推理通过，不声称完整共享/专业音质验收。

以下保留历史QA：

---

# 批量导入导出与按钮修复（2026-10-25）

Stage http://ttd-stage:17896/ui/，release h-e92556e09ea24f95；未提交/推送，正式Hub未更新。用户明确要求移除商用授权及内部测试展示，仅界面移除，来源与许可数据继续内部保留。

## 本轮实现

- 模型库可用项按钮不再依赖全局busy。chooseLibrary可在后台任务处理中进入工作台、选择模型并保留多文件列表；实际任务按已提交快照运行。未接入项保持不可运行。Deux原说明、415MB、输出分轨仍显示，授权提示不显示；Stage标识/关于测试版/页脚说明移除，实际隔离部署保持。
- 多文件选择/拖放、按文件试听和移除；每批20文件/合计2GiB，每个512MiB/10分钟，读取元信息失败逐文件报错。server batches持久化到/data/batches，每个输入仍为原job；start串行持有同一个GPU槽，浏览器退出/刷新不阻断后续文件，重复start不重复成功项，失败重试只处理未成功项。新batch.py不修改worker.py，37个就绪模型验证指纹不变。
- 按文件/轨道勾选，支持逐个WAV和ZIP。ZIP由CPU逐文件写到/data/exports，按输入文件分目录、Unicode安全名称，保留WAV原字节、不做有损转码。按来源size/mtime哈希复用缓存，空间不足拒绝打包。提供明确下载链接，生成成功和下载落盘分开。导出/批次持久文件不自动删除。

## 验收

| 检查 | 结果 |
|---|---|
| 页面/空白/遮罩 | PASS，Stage PYMSS真实内容，无框架错误层 |
| 控制台 | PASS，相关error/warn 0 |
| 桌面1280×720/手机390×844 | PASS，无横向溢出、可见中文均≥12px；截图在/tmp/pymss-batch-qa |
| 模型按钮 | PASS，Deux库按钮可点且返回工作台；批次busy=true时实测enabled=true，2个输入仍保留，selected=Deux |
| 界面提示 | PASS，Deux商用许可、Stage/内部测试标识不展示，原说明/文件名/大小/能力保留 |
| 多导入/真实分离 | IAB filechooser一次选2个真实歌曲6秒片段→UI2输入→2个原生CUDA任务依次成功→4条48kPCM24双声道结果；批次365a181ac8864e1dae4c847da05cbf33。Chrome扩展setFiles缺少文件URL权限，未改扩展权限；改用独立IAB验证 |
| 刷新恢复 | PASS，同一batch ID恢复2完成任务/4轨，重建容器后结果仍可读，不重跑 |
| 勾选/打包 | PASS，取消一轨→已选3，服务端生成3轨ZIP；全选4轨ZIP通过CRC并逐字节SHA匹配各原WAV，Unicode目录不冲突，重复start保持ID |
| 错误与状态机制 | PASS，空/越界/无效任务导出拒绝；CPU隔离状态测试：槽互斥、重复start、仅重试失败项、开始后禁止新增、重启标记保留已完成均通过。CPU替身不计模型推理证据 |
| 下载浏览器落盘 | 未通过验收。IAB及Chrome点击下载事件超时，生成链接仍可读；此前HTTP下载拦截未绕过。浏览器安全策略拒绝chrome://downloads读取，不改权限/证书或绕过警告 |
| 构建源码 | Svelte0错误0警告、sourcechecks330通过、default/design构建与diff-check通过；既有大chunk提醒保留 |

证据：/tmp/pymss-batch-qa/{01-batch-results.png,02-mobile.png,03-library-button.png,batch.json,two-files.zip,export.json,check-batch-state.py,final-verification.json}。GPU0回6393MiB，其他7681/11413不变；容器OOMfalse/restart0，固定10.35/24、家庭32.214回程via100.2保持。新代码没有CPU/offload/精度/权重/认证/DNS/公网变更。家庭方向资源/API/批次通过；137088458字节ZIP首次90秒超时（收到134314320字节），180秒有界复测完整SHA和Range206通过，整曲包CRC及两条原WAV逐字节比对通过；实际家庭Mac/手机、实体存储下载/宿主重启/回滚仍NOT_RUN。

上一版本QA如下，保留其历史边界。

---

# PYMSS 分类、稳定卡片与真实波形 QA

2026-10-25，Stage http://ttd-stage:17896/ui/，当前 **h-3c60e8ce73ab2a17**。未commit/push，正式Hub未发布。

## 本轮变更

- 保留人声与伴奏综合入口，恢复“人声分离”“伴奏分离”独立分类，沿用旧目录归属并按用途质量顺序展示可用模型，不按年份过滤。
- 乐器子类取消常驻独立一行，由“乐器分轨”父选项点击延展，菜单含全部、四轨、六轨、鼓、贝斯、吉他、钢琴、弦乐；子类选择后收起，父项保持高亮。
- 上次选中项自动排首是卡片跳动根因。本轮presentation.ts固定同用途基线；点击只更新选中态，下拉新项稳定追加且切回其他卡不会移除。菜单浮层不占页面高度，不自动滚页；关闭浏览器滚动锚定，并在选择完成后保留视口。
- 影视入口改为“影视分离 DME”，包含对白/其余、人声/其余双轨及对白/配乐/音效三轨。引入2个原缓存AliceN对白模型，均真实CUDA6秒通过；电影用途下通用人声模型的other显示其余声音，不误标纯伴奏或虚构M/E。purpose随任务保存，刷新可恢复用途；旧任务保留默认语义。
- 每条结果加入真实PCM波形、播放进度、点击/键盘定位，保留原有逐轨播放器和下载动作。新老结果均可用，不必重跑模型。API返回waveform_url/bytes；独立waveform.py按900个精确区间逐块读取PCM并取双声道最大幅度，生成小JSON及持久缓存，避免整曲浏览器Blob/解码。缓存按文件大小+mtime校验、原子写入；请求超时可重试。GPU worker完全未改，原35验证指纹保留。

## 验证结果

| 项目 | 实际结果 |
|---|---|
| 页面身份/非空/遮罩 | Stage PYMSS Studio · 音轨分离，真实页面，无构建错误层 |
| 父项延展 | 常驻instrumentbar数量0；父按钮点击展开8项，选钢琴→MVSEP钢琴/菜单收起/父项active |
| 卡片稳定 | 实际鼠标反复选卡：全部卡片文档坐标不变、1个checked；从下拉选择后页面Y449.5→449.5，新增项追加，切回旧卡不移除新增卡 |
| 自动化差异 | locator点击自动居中曾令视口449.5→598，属于控制器动作；改用可见区域实际坐标鼠标点击验证，未把该居中误记为应用仍跳动 |
| 分类 | 人声：Leap/Deux/Resurrection/Becruily/FT2等；伴奏：Deux/HyperACE INST/Resurrection INST/Becruily INST/InstVox；影视同时可见AliceN2轨/Leap2轨/BandIt3轨 |
| 目录 | 330卡/330ID，包含独立人声、伴奏、影视等19组；作者链接0、大小/真实或声明分轨保留；37可用/38注册，XL4仍显存不足不可用 |
| 新对白模型 | AliceN BS3.78秒、Mel4.1秒真实6秒CUDA通过，既有只读权重复用，管理员配置不覆盖；固定HF配置与SHA记录在models-lock |
| 电影任务 | e0f9945d9eca420283528dd9d9b26c1f Alice BS对白/其余；942d1ae8943a472d905ef04f107a8344 Leap人声/其余；purpose=dme、两轨48kPCM24双声道288000帧。UI刷新第二任务保持影视分类及正确标签 |
| 波形算法 | 合成静音/单侧立体声正弦、时长/峰值、缓存复用与文件变更失效检查通过；真实6秒双轨及原238秒双轨，各4个独立区间（含尾段）和PCM逐值比对一致 |
| 波形交互 | 原b7cb240e0dbf4d67bd756a26e1e61bd8旧结果2×238秒，各900真实峰值；点中点→119秒，游标与clip50%、01:59/03:58一致；实际播放time119.198659/进度50.081%并继续前进 |
| 六轨旧结果 | f54旧任务6条波形均900点、duration6、无加载错误，不重跑推理 |
| 控制台/布局 | 最终桌面1512×772应用error/warn为空；新菜单/波形实际手机和家庭MacNOT_RUN，旧390布局证据仅历史引用 |
| 家庭方向 | 路由器绑定32.2：最终release/HTML/JS/CSS SHA匹配、API37就绪、238秒波形JSON通过；不是实际家庭Mac浏览器验收 |
| 运行 | 无容器OOM、restart0；GPU0回6393MiB/其他GPU未变；10.35/24与家庭32.214回程via100.2保持；未改精度/offload/CPU路线 |
| 源码 | Svelte0错误0警告；分类、原文、去重、固定卡片/追加、能力及网络检查通过；default/design构建、diff-check通过（既有大chunk提示） |

## 证据与边界

38-long-song-waveforms.png、39-parent-instrument-menu.png、40-cinema-dual-and-triple.png；stable-cards-browser-verification.json、waveform-seek-verification.json、real-waveform-bin-checks.json、cinema-waveform-api-verification.json；最终release/stable-cinema-waveform-verification.json记录家庭方向及镜像。

波形是实时音频数据的峰值视图，不是演示/随机图，也没有改写原WAV。38注册模型中37功能可用，XL4显存不足不冒充完成。6秒功能验证不替代用户电影素材专业音质评审。此前Chrome HTTP直接WAV下载拦截仍未解决/未绕过；本轮未声称下载、实际家庭Mac/手机、完整三端、宿主重启或回滚已验收。Hub继续等待用户确认。

结论：本轮分类/层级/卡片稳定/真实波形与目的标签通过；完整共享/下载仍partial。

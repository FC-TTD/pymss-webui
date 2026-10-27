## 主推荐模型与结果二次处理（2026-10-26—27，当前17896）

- 用户确认将两个工具对应模型加主推荐，并要求人声→和声、国际声→音乐/音效二次分离。按已说明范围：Stemdeck原生htdemucs_6s对应现有HTDemucs六轨，提升stems/six默认首位；YingMusic专用BS-RoFormer加入karaoke默认首位，置顶仍优先、duo前两Instvox/BS12.97不变。不是把Stemdeck的可选UVR-MDX Karaoke2接入；那款本轮未接。
- Stage最终Web **h-fa900232858e1f41 / sha256:9ff491b3b085ad165c0417b81bc1d92201db458548f0039227b59482e81ce048**，管理/opt/pymss-ui-preview/releases/h-fa900232858e1f41。仅web更新；共享PYMSS8ff9aa43/5e7c82a2/h-bd63eb3d3ceeebfe、正式msst cb9dddb8、原30911 yingmusic-svc c5535e4e/ff3cb7cf及ClearVoice bfd1保持。今日无commit/push/正式发布/原30911替换。
- 原30911能开网页但health当前cuda_available=false，不能直接以页面作为可用证明。新增独立edge YingMusic native provider **h-c2feb0194eb722fb / sha256:b2f4e6dfa5337fdf2afdf19bcc716ce51bd0e04174972711f3d288f6c7b67cd1**，/opt/yingmusic-audio-preview/releases/h-c2feb0194eb722fb，私有100.15:17903→Stage/api/ym。源FC-TTD/YingMusic-SVC4974a80c6044c4557059548409379f6365129f88，新副本work/yingmusic-audio-api，未改原部署。复用NAS只读官方bs_roformer.ckpt1295074954bytes/SHA364964794b0c82c843c53099d80b6ecfee852cf2bf42f098515276c779623bb6，不加载SVC-full变声模型。
- edge GPU0 UUID5dda4827，native44.1k立体声/8s分块/overlap2/batch4/use_amp原配置，严格1195tensor匹配；每job独立CUDA子进程退出释放，资源预检等待，不CPU/offload/降精度。基于既有cu128缓存镜像ff9a2418，只新增原需求beartype0.14.1官方校验wheel，无多GB基础层重拉。直接执行锁定原生BSRoformer及从原utils AST原样提取demix/window/prefer函数，排除训练依赖导入，不改算法源码。6s/24s/官方35.761625s文件真实3轨均成功；48kPCM24导出。原30911用mix-lead覆盖instrumental；本provider保留三路原生预测，避免把带和声残差称纯伴奏。
- 新CPU链路服务 **h-df4d5149651815e8 / sha256:a504443d9abffbcb2dd3e85f9f6daa8dbde2bcf0406a50cbc0ecee94f936b5ac**，/opt/pymss-chain-preview/releases/h-df4d5149651815e8，自有NAS /mnt/TTD/04_应用/pymss-chain-preview，复用既有10.35外部网，无新宿主端口/GPU。消费者代码归pymss-webui/deploy/chain，不改PYMSSworker。/api/chain/inputs只接受合法job_id/stem，从已完成PN/CV/YM输出白名单取原WAV，服务器流式导入中央不可变asset一次并SHA校验；同源重复选择幂等复用，无浏览器上传/解码。不接受任意URL/路径。输出及原输入不改，不自动删除。
- 每轨“继续处理这条音轨”→主唱和声/音乐音效/降噪/其他用途；只准备新一轮，不自动跑GPU。保存目标preparing批次及输入引用，刷新恢复选择；新开始可直接启动同批。输入显示来源和查看上一轮链接；链路元数据持久JSON，断线重试先检查pool批次避免二次导入。音乐音效默认选真实三轨模型，仅勾配乐/音效；旧影视结果按purpose显示国际声。所有结果保留，跨provider输出可再用。
- 真业务：HT6 batch f703a11bfe0d45b086ccc42c1228702c输出6轨；Deux影视 f6522d7168174b86bd138a4759b2c400；其余声/国际声→BandIt music+sfx batch85a899140dcd49efb08d179e11034f5d成功2轨；PN人声→Ying ym-bc5b378481fb4053b1891c8496b5f715成功3轨，prepared刷新→相同批次开始已浏览器验证；以上处理任务uploaded_bytes0。母轨输出SHA=派生输入SHA、重复使用asset ID相同，母轨保留。CVclean及YMbacking→中央输入也通过。原始file仍只上传一次；派生WAV首次服务器内部登记不等同零磁盘复制。
- 官方全35.76s source YMbatch ym-66880364a37e44e5aae2f03c865619e5成功，每轨10299398bytes，全部48k/24bit/2ch、900真实峰值、Range206。ZIP30898678bytes（三轨，>16MiB），CRC与每轨WAV SHA完全一致，家庭router32.2绑定来源全包SHA同；浏览器保存落盘NOT_RUN。首次测试6s母素材适合协议，不作为和声音质判断；官方完整样本补真实可见人声/和声。
- Svelte0/0、336唯一元数据/334可选目录、推荐及卡片稳定/过滤/设计检查/build/diff/Python语法通过。实际桌面1280×900与390×844菜单展开无横溢，中文>=12；Ying优先/HT6优先、波形键盘定位、prepared恢复、两个二次流程及ZIP按钮/控制台0通过。最终HTML/JS/CSS家路32.2来源SHA一致；10.35/24、edge10.42/24、CV10.41/24及家庭回程Stage100.2/edge100.1保持。GPU回Stage6393/7681/11413、edge4/15641/12750 MiB基线。
- 证据work/pymss-ui-evidence/yingmusic-chain-20261026/。原生日志在/tmp/yingmusic-native*和providerNASsmoke/verified-model；部署输入在两个/opt管理目录，原源码完整锁定。实际家庭Mac/手机、用户音质盲测/固定长段身份、宿主重启/完整回滚、浏览器落盘NOT_RUN。所有新增均为preview，未作为Hub admission，正式路由尚未纳入/ym及/chain；以后正式推广须源码提交授权、依赖纳管及路由/真实业务回归，不能直接拿旧publisher发布本轮候选。
- 回退仅Web到前h-af473c0073ecb820，固定原10.35和共享runtime；新增Ying/chain可保留供恢复旧结果，不删任何NAS输入/任务/输出/模型。实际未回滚、未停其他服务。

---

## 分类澄清与 ClearVoice Stage 候选（2026-10-26）

测试入口：http://ttd-stage:17896/ui/ 。最终Web h-af473c0073ecb820 / sha256:5f84a1c943da86b08a3ec7720bc6450deb90c3cbde46d4e1fc5a73299d6af53d；/opt/pymss-ui-preview/releases/h-af473c0073ecb820。正式msst仍h-bd63eb3d3ceeebfe/cb9dddb8，原PYMSS容器8ff9aa43与5e7c82a2镜像未变。今日无commit/push/正式推广；等待用户实际素材测试。

- 用途明确区分歌曲人声/伴奏、影视国际声、双人对白分离、人声降噪、音质提升；“对白清理”更名“提取对白”，与去混响/气声分离/去人群声归入“更多人声处理”点击延展。乐器细类继续对应父按钮。选中用途一句解释，单模型不显示空的更多下拉。
- AliceN BS98MB和BandIt v2中文从所有新选择中隐藏，原元数据/权重/历史结果保留（取代本日较早仅移出影视的规则）。影视Deux优先，平铺3双轨+3真实三轨，能单独输出配乐和音效；背景国际声为估计，不能保证等同原始M&E。原模型说明仍保留。
- 新增5款ClearVoice：MOSS双人对白16k、MOSS超分48k、MOSS降噪48k、FRCRN16k、GAN16k。模型大小按锁定权重展示，2026为新收录年份。独立provider FC-TTD/ClearerVoice-Studio native6b3774dc79c46ae8bed2a4fa5f706f0ac8c75c61；新工作副本work/clearvoice-audio-api，未改旧July脏工作副本或原clearervoice服务。
- 独立edge preview h-7eeb8d0d97f78e3f / sha256:bfd1b25c21f10468f149ec1e736376e060c54bd86a15db1f21049886784e0fa3，私有192.168.100.15:17902，Stage相对/api/speech代理；GPU0 UUID5dda4827，原生精度/CUDA，无offload/CPU替代。5模型真实推理及严格tensor匹配通过；每job子进程释放显存，等待资源/任务保留/失败续跑。模型NAS独立只读，结果独立目录；PYMSS原始输入只读引用，不复制或重传。
- 首次ClearVoice导入先上传至既有PYMSS不可变输入池，pool batch保持preparing且不启动；CV新job只引用canonical asset。真实浏览器SS 12秒2轨 cv-333d86a470d74e049e5a224a3ca28be4；SR cv-e22d0e32411341f8b4906a07e43e824c → SE cv-49cdc17aafa341a19dfbe66d5d7e331a → 经典Instvox 0b1434b686d947d5bee259bfa085ed24 均成功，后3同asset15dcec316cb5469387e07969508f82c6，uploaded_bytes0。刷新恢复输入/结果，播放器时间真实推进；全部输出waveform及Range206通过。ZIP2轨CRC及每轨SHA与WAV完全一致，未声明浏览器保存落盘。
- SS原生默认短2秒分块跨段易乱序，改8秒上下文/6秒步长+2秒重叠相关匹配及交叠重建。12秒自建可追溯双源fixture：有效叠音前6秒SI-SDR10.314dB、全段3.098dB、较混音提升2.958dB；不等于中文真实对白或长段身份验收。SR输入按hop上下文补齐后实际模型输出裁至原时长，无输出尾部补零；2.3976875秒正确115089帧，模型高频与纯重采样不同，不保证找回丢失细节。人耳质量/长段A/B固定身份NOT_RUN。
- Svelte0错误0警告、335唯一元数据/333可选目录、质量排序/稳定卡片/电影3轨检查及构建通过。5模型CUDA冒烟和CPU协议/数量/路径/恢复/导出检查通过。实际IAB1280×900/390×844无横溢、可见中文>=12px；菜单点击、单选不重排、库使用按钮直达且保留输入、控制台warn/error0。证据work/pymss-ui-evidence/clearvoice-20261026/；provider测量在NAS结果smoke-report/objective-smoke/verified-models。
- 家庭路由器32.2绑定来源：最终HTML/JS/CSS SHA一致；Stage固定10.35/24/家庭32.214经100.2，edge固定10.41/24/家庭经100.1均与部署前相同。原GPU占用Stage6393/7681/11413、edge4/15641/12750 MiB恢复基线，健康/重启0。实际家庭Mac/手机、宿主重启/回滚、浏览器落盘和真人音质验收NOT_RUN。
- 回退仅Stage Web到h-bd（固定现有10.35网络和共享runtime），不删任务/输入/结果；ClearVoice可保持独立preview以保留结果。未执行回滚。正式发布需用户确认本轮候选后按现有源码/业务发布规则执行，不能仅将原生MSST或ClearVoice视为已纳管Hub能力。

---

# 影视国际声与配乐音效（2026-10-26）

- Stage17896 static-only h-fc7a77da506af035 / sha256:2028d03ca0feb0df28dd12caa6617f3103decfb5c81cc31f714abe2e9b6845f8; backend remains h-bd63eb3d3ceeebfe/5e7c82a2, formal msst UI cb9dddb8 unchanged. No commit/push/formal update, source pending user Stage test.
- Film excludes AliceN BS98MB and BandIt v2中文 (metadata/weights/history preserved, classifiedcleanup); Deux first. Film descriptions distinguish human speech/estimated international background and optional separate music/SFX, preserve original/music wording. Added existing accompaniment models for international focus. Default3dual+3true3stem cards:Deux,Instvox,BS12.97,BandItmulti,Plus,DBSTIGER;single selectionstable/pinspriority retained.
- Official BandIt/DBS capabilities plus current37-readyregistry confirmed. IAB real BandItmulti chooseonlymusic+sfx; batch015cfb3f26704a3aa66002a2dd12f182 succeeded, reuse0upload,2x6sec/48kstereoPCM24/900peaks/Range206. Not film quality acceptance.
- deploy.sh PREVIEW_WEB_ONLY pins sharedruntimeimage/release and fails on backend input changes; --no-deps web only, no runtime rebuild/restart. Publisher understands backend_release for future approved promotion. Svelte0/0/source330checks/build/bash/Python/diff passed. Desktop1280x900/mobile390x844 nooverflow/Han<12px0;consoleclear. Home32.2bound3resourcesSHApass,10.35/24andhomevia100.2 unchanged; actualhomeMac/filmquality/restart/rollbackNOT_RUN. Evidence/tmp/pymss-cinema-20261026/.

---

# 正式音频分离入口发布（2026-10-25）

用户已明确授权本次相关提交并继续发布。正式入口 [音频分离](http://msst/)，首页tools.msst名称“音频分离”、备注“MSST 和 PYMSS”，href仍http://msst/。默认PYMSS，顶部PYMSS/MSST单一选中导航；原MSST通过/?native=msst加载，__gradio__仍由原Hub处理。

- 已推广Stage验证的h-bd63eb3d3ceeebfe，静态镜像cb9dddb8ba18d3cf16f7c738720188413936bc48f77ebdf735e7737941a04c98，本仓库128项构建输入与提交逐字节匹配。业务发布源5fdbc10782c289634f7cfc8642f1259f1f365be1，首页源48a4ff3168afb575c0750cf664e6f0a71eeba76f；全部仅本地提交，未push。
- 新增Stage CPU容器audio-separation-entry，只读101:101/64MiB/.5CPU，复用既有10.35/24网络和API。原caddy overlay按ID、名称接入均实际失败，未更改Swarm/daemon或新建网络；最终仅绑定Stage既有192.168.100.18:17898，业务标签显式upstream，由现有多socket Caddy汇集。正式前端独立于可变17896预览。管理目录/opt/audio-separation/releases/h-bd63eb3d3ceeebfe-5fdbc10782c2/。
- 实际Caddy私有msst路由同时包含新根/UI/StudioAPI handle及原10.0.3.200:8080 catch-all。native=msst排除于新根，公网msst-public-proxy保持原路由；原MSST Hub entry和GPU runtime ID/镜像完全未变，无GPU部署/迁移、权重、精度、offload、DNS/认证/公网变更。
- 实际浏览器http://msst/默认PYMSS；MSST原Gradio完整加载后切回，状态保留。主页卡片真实DOM正确，点击打开新入口；模型卡片前两InstVox/BS12.97；刷新恢复1输入、两轨、波形，控制台error0。
- 正式地址BS12.97批次9de24ab942044546ad9e2990120d99ea成功；随后浏览器切InstVox→开始分离，批次3b70c72641b741b1a758740189099be8成功。两次均uploaded_bytes0/reused_files1，canonical输入相同，无input.audio副本。2×6秒/48kHz/双声道PCM24，每轨900真实波形点及Range206通过。
- 正式ZIP完整3456370字节、2轨、CRC通过，内容SHA与逐轨原WAV一致。生成/完整HTTP传输通过不代表浏览器实际落盘，后者仍NOT_RUN；不绕过HTTP下载安全保护。
- 家庭路由器32.2绑定来源验证正式HTML/JS/CSS哈希、原生MSST/Gradio配置、源/结果Range通过；Stage固定10.35/24、32.214回程via100.2未变。实际家庭Mac/手机、宿主重启、回滚演练NOT_RUN。此前同镜像Stage桌面/390手机无溢出且中文≥12px结果继续有效。
- 首页仅经现有links API修改tools.msst text/title，更新前后全量JSON对比其他字段/条目完全一致。变更前备份及正式证据位于工作区work/pymss-ui-evidence/formal-promotion/h-bd63eb3d3ceeebfe/，并保存到服务器管理目录。未部署/重启首页API。
- 37就绪/38注册保持，原worker未变；CPU容器healthy/OOMfalse/restart0，GPU占用回基线6393/7681/11413MiB。未停止其他任务。回退仅针对新增CPU入口和本次首页两字段，原MSST catch-all可接管，保留所有输入/任务/结果；实际未回退。

本次功能发布与真实业务回归通过，不声称完整三端共享、音质盲测或宿主重启/回滚验收。Stage测试链接继续http://ttd-stage:17896/ui/。

---

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

## 2026-10-27 正式入口推广准备

正式msst仍旧版，未执行运行配置写入。新版h-fa900232858e1f41的UI128/语音85/Ying29/chain4输入、实际镜像/管理目录、全静态资源SHA核对通过；新增speech/ym/chain业务路由的Compose校验与Caddy adapt通过。Svelte零错警、目录336及单选/筛选检查通过。现有整首Ying三轨与国际声后二次music/sfx输出Range、派生来源SHA复核通过，未新启GPU。家庭router32绑定32.2方向页面SHA一致；实际同事质量试听NOT_RUN。准备、路由和LAN证据见../pymss-ui-evidence/formal-entry-20261027/，提交授权待答复；不把Stage验收当正式域名发布后验收。

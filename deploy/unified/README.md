# 音频分离组合入口

## 2026-10-28：旧工作台路径永久跳转

分离工作台已独立到 `http://separation-studio/`。按用户要求，`http://msst/ui`、`/ui/` 及其子路径固定返回 301，直接跳到内网新域名根路径，丢弃旧路径及查询参数。此条替代下文关于 `/ui` 继续展示组合界面的历史记录。

本次仅修改 `entry` 的业务 Caddy label 与路由验证 fixture，沿用当前不可变 CPU 镜像和既有 Compose 网络。配置变更通过 Compose 仅重建 `entry`，短暂切换 CPU 代理，不执行 UI 镜像推广脚本，不重建模型或重启 provider。根路径、原生 MSST 和 API 的路由定义保持。新域名继续使用独立应用登录与授权。

配置发布时保存当前 Compose/override/env，使用已提交版本的 `compose.yaml` 与原固定镜像 override/env 创建新的管理目录，执行 `docker compose --env-file formal.env -f compose.yaml -f formal-override.json up -d --no-build --no-deps entry`。校验 Caddy 实际聚合的 `/ui` handle 为 301，并检查 GET/HEAD、带旧查询参数的子路径、新站内网访问及 API。回退使用保存的原管理目录和同一 Compose 命令，只恢复 CPU 入口配置，保留所有音频与模型数据。

用户已要求把最终工作台合并进原 MSST 入口，首页名称为“音频分离”、备注“MSST 和 PYMSS”，默认 PYMSS。Stage 验证入口始终为 `http://ttd-stage:17896/ui/`。

## 所有权与范围

- `FC-TTD/pymss-webui` 拥有组合页面、明显的 PYMSS/MSST 导航、PYMSS 工作台、音频复用 API 和本入口的业务 Caddy 标签。
- 原 `msst-hub-entry`、MSST 原生界面、租约和 admission 路径保持；MSST 页通过 `http://msst/?native=msst` 加载，API 的 `__gradio__` 路径继续由原 Hub 入口处理。
- 首页卡片由 `FC-TTD/ttd-file/file/index.links.json` 及其现有 `/index-api/links` API 管理。本次仅改 `tools.msst` 的 text/title，保留原 `http://msst/` 链接。
- 不修改平台 Caddy 全局配置，不创建域名/DNS/认证/公网路由，不迁移或新建 GPU runtime。新的正式组件仅为64MiB/.5CPU只读静态入口；复用现有 PYMSS 后端网络和已经验证的 Stage API、GPU、NAS 数据。

## 源码提交授权门禁

用户已于2026-10-25明确授权“本次提交并继续发布”，该授权涵盖本次两个仓库的相关本地提交，不包含push。

当前工作台最初由未提交的任务快照构建，TTD policy 要求正式发布前单独授权代码提交。用户授权发布入口不自动授权 commit/push。先完成 Stage 真实业务验证；未收到提交授权前不得执行 `--apply` 或更新首页。

提交获批后，仅提交本次两个 canonical 仓库的相关文件，不提交工作区其他项目，不默认 push。`publish.py` 要求当前完整 commit 与经过验证的候选 manifest 中所有本仓库构建输入逐字节匹配，脚本/Compose 也从同一 commit 读取。不从可变工作树现场重建模型镜像。

## 发布

1. 从 `work/pymss-ui-evidence/stage-releases/<verified-release>/` 读取当前通过的 manifest/QA。
2. 在已授权的源码提交后运行只读检查：

   `python3 deploy/unified/publish.py <verified-release> <pymss-webui-commit>`

3. 检查通过且发布仍在授权范围时，加 `--apply`。同一 Stage 上复用已测试的不可变静态镜像 ID，新的 CPU 入口加入已有 `pymss-ui-preview_default`，仅绑定既有内网地址192.168.100.18:17898，由业务标签提供明确upstream，不创建新网络或默认桥接网段。原后端和 MSST 容器均不重启。
4. Caddy 把本入口的私有 `/`、`/ui`、`/ui/*`、`/api/studio/*` handle 合并到既有 `msst` 站点；`/?native=msst` 排除在新根路径之外。原 catch-all 继续处理 MSST。`msst-public-proxy` 及公网入口不变。
5. 检查实际 Caddy 合并结果、主页默认 PYMSS、MSST 切换、文件引用/真实分离、Range 和家庭方向资源。`merged-route.Caddyfile` 仅为适配验证 fixture，不能加载为平台全局配置。
6. 再在 `ttd-file` 仓库运行：

   `python3 tools/publish-audio-separation-link.py <ttd-file-commit> --apply --backup <durable-before-json-path>`

   工具保留其他实时条目，保存完整变更前 JSON；检测到读取期间修改则停止。现有 API 没有原子 revision 条件写，本脚本的二次读取不能冒充服务端并发锁。

## 运行与恢复

正式入口管理目录：`/opt/audio-separation/releases/<release>-<source-prefix>/`，含不可变镜像、源码映射、Compose 与网络记录。保留现有 Stage 网络10.35/24及家庭回程，不恢复自动网段。

输入首次上传后以 `input_asset_id` 引用原 NAS 文件，后续模型任务不再上传或复制。新任务有独立输出目录；旧任务刷新也可恢复输入。不得删除仍被其他任务引用的原输入，当前没有自动清理。

回退只针对本次新增 CPU 入口及本次首页字段：使用记录的上一 CPU 镜像/配置；首次发布可在明确授权回退后停止新增入口，使原 MSST catch-all 继续接管。不要停止 MSST/PYMSS GPU 服务，不回滚或删除原始音频、结果、批次或资源峰值档案。实际回滚未执行。

实际Stage worker无法解析既有caddy overlay（名称/ID均失败），未改Swarm/daemon/网关。最终使用仅绑定Stage既有100.18内网接口的17898端口及显式业务upstream，保持独立不可变前端，不把正式UI指向可变17896预览。无公网标签/认证/DNS变化。

## 本次实际发布结果

已按用户单独提交授权发布。有效业务源5fdbc10782c289634f7cfc8642f1259f1f365be1，首页48a4ff3168afb575c0750cf664e6f0a71eeba76f，镜像与Stage h-bd63eb3d3ceeebfe相同。实际最终方案是显式192.168.100.18:17898私有upstream（前述overlay方案未成功且未修改集群），Compose为唯一有效定义。正式默认/切换/两款零重传分离/波形/Range/ZIP与首页两字段对比均通过，详见../../design-qa.md。未push；家庭实际电脑、宿主重启及回滚演练未执行。

正式入口当前依赖同一Stage后端和NAS数据；后续Stage运行时升级须先考虑正式msst调用，不能当作只有预览用户的服务。前端容器已独立，不代表后端隔离。

## 最新候选入口推广准备（2026-10-27）

用户要求先把新版放回 `http://msst/ui/`，供局域网同事试听模型质量。本节取代旧版命令对新增能力的遗漏；本轮尚待独立提交授权，不能将准备记录当作正式发布完成。

- 已验证候选为 `h-fa900232858e1f41`，静态镜像 `sha256:9ff491b3b085ad165c0417b81bc1d92201db458548f0039227b59482e81ce048`。只推广 CPU 入口，不重建模型。原首页名称/备注已经正确，不再更新。
- 新入口补齐 `/api/speech/*`、`/api/ym/*`、`/api/chain/*`，保留 `/api/studio/*`、默认 PYMSS、`?native=msst` 及原 MSST catch-all。只改私有业务标签，无公网/域名/认证变化。
- 外部共享依赖：原 PYMSS 后端 h-bd63eb3d3ceeebfe；edge ClearVoice h-7eeb8d0d97f78e3f；edge YingMusic h-c2feb0194eb722fb；Stage CPU chain h-df4d5149651815e8。它们保留原受管理 Compose/容器/NAS 和固定镜像，不在本次入口更新中重启。正式入口依赖这些服务后，后续预览升级也必须纳入正式调用方影响检查；不能宣称后端隔离或已纳入 Hub GPU 生命周期管理。
- `publish.py --prepare` 对当前工作树做只读检查：候选完整 UI 资源 SHA、128 个 UI 输入、85 个 ClearVoice 输入、29 个 Ying 输入、4 个 chain 输入，以及实际 Compose 管理路径、镜像、健康/可用模型。缺失本仓库输入不能跳过。
- 正式执行要求三个仓库的独立授权提交，逐文件从 commit 读取并与候选 manifest 比对。`promotion-source.json` 记录依赖源码提交、镜像、管理目录、挂载及上一入口配置。推送不在授权范围。

准备检查：

```sh
python3 deploy/unified/publish.py h-fa900232858e1f41 --prepare
```

取得本轮提交授权并完成提交后，先运行不带 `--apply` 的同一命令，检查输出，再按已有入口发布授权执行：

```sh
python3 deploy/unified/publish.py h-fa900232858e1f41 <ui-commit> --speech-commit <clearvoice-commit> --ying-commit <ying-commit> --apply
```

发布脚本在写入前再次核对入口/后端/依赖容器身份，避免并行部署覆盖。CPU 入口管理目录沿用 `/opt/audio-separation/releases/<release>-<source-prefix>`；保存上一容器记录及具体 `rollback.sh`，恢复只涉及旧入口配置/镜像，不回滚音频、结果、批次或派生来源。回退本身须按实际授权执行，不自动触发。

发布后的验收须在正式域名重跑：最新资源 SHA、两套导航、模型可用目录、旧批次恢复、实际新任务/二次处理、波形/Range/ZIP和适用家庭来源。Stage 上既有通过证据为 `work/pymss-ui-evidence/yingmusic-chain-20261026/verification.json`。同事实际试听、三台 Mac、宿主重启及完整回滚演练均尚未执行；质量评价由实际业务素材对比确认，不能从健康检查推断。

## 2026-10-27 已发布

已收到本轮独立提交授权并完成三个仓库本地提交，未push。正式http://msst/ui/已运行h-fa900232858e1f41（与Stage完全相同不可变镜像），管理目录/opt/audio-separation/releases/h-fa900232858e1f41-10ed67982276。发布源UI10ed679/ClearVoice e14252c/Ying49435fa；后续仅发布工具和验收文档提交不改变运行镜像输入。

实际CDP异步刷新先页面后接口，首次脚本postcheck404，路由随后全部自动收敛；已改后续工具等待完整页面+模型+MSST契约。实际Caddy在srv1，不能固定假设srv0；私有speech/ym/chain全部验证，public-proxy与旧JSON一致。未手写平台全局配置。

正式三条真实链路（PN人声→Ying三轨→ClearVoice48k，以及Deux国际声→BandIt音乐音效）均成功，无浏览器重传；完整30MB ZIP/Range/波形/来源SHA、prepared刷新与MSST导航通过。正式源与Stage全11资源SHA一致；家庭router32绑定32.2来源页面/JS/CSS/整ZIP一致。原MSST/30911及所有共享依赖ID不变，正式CPU入口healthy/restart0；回退文件已保存，未演练。证据../../..的work/pymss-ui-evidence/formal-entry-20261027/DEPLOYMENT_REPORT.md。同事质量试听及实际家庭电脑仍NOT_RUN。

## 2026-10-28 静态界面收尾

公共入口不再从localStorage自动加载上次任务；显式当前任务链接仍支持刷新/二次处理。因为其他聊天已将PYMSS及ClearVoice/Ying接到受管Hub，旧publisher的preview镜像门禁不适用于当前依赖；使用update_static.py，仅更新两CPU Web且锁定当前实际后端身份/镜像/管理路径，先Stage后正式，不启动或回退旧GPU服务。代码从授权提交的git archive只读快照构建，源文件前后SHA核对；相同输入第二次构建要求摘要一致并缓存命中。正式推广复用同一个Stage镜像，并核对Stage静态资源SHA。上一容器与Compose/env管理位置写入stage-before/formal-before.json，保留数据及既有网络。命令：python3 deploy/unified/update_static.py <commit>，Stage验收后同commit追加--formal。

# 音频分离组合入口

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

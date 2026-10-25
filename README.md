## 音频分离组合工作台（2026-10-25）

正式入口：[音频分离](http://msst/)。首页名称“音频分离”、备注“MSST 和 PYMSS”；顶部双导航、默认PYMSS。原MSST通过独立导航保留。测试入口仍为[Stage](http://ttd-stage:17896/ui/)。

人声与伴奏默认前两为InstVox Duality v2、BS Roformer12.97。首次上传后换模型直接复用同一服务端音频，刷新恢复已导入列表，结果独立保存。正式地址两款真实分离均0新增上传，波形/Range/ZIP完整传输通过；实际浏览器落盘与完整三端/重启/回滚仍未验收。源码已获授权本地提交，未push。部署范围与恢复见[组合入口说明](deploy/unified/README.md)，实测见[QA](design-qa.md)。以下保留原开发及历史记录。

# pymss WebUI

Svelte and Vite browser interface for the pymss music source separation server.

## Development

Install dependencies:

```sh
npm ci
```

Start the development server:

```sh
npm run dev
```

The development server proxies `/health` and `/v1/*` requests to `http://127.0.0.1:8000`.
Start the pymss server separately before using API-backed views:

```sh
pymss serve --host 127.0.0.1 --port 8000
```

## Build

Build static assets:

```sh
npm run build
```

The built files are written to `dist/`. To vendor the WebUI into the Python package,
copy the contents of `dist/` to `pymss/server/webui_static/` in the pymss repository
before building the Python package.

## 新版工作台 Stage 测试（2026-10-25）

用户测试入口：[http://ttd-stage:17896/ui/](http://ttd-stage:17896/ui/)。正式 Hub 仍等用户确认后再发布。

- 工作台主用途展开；人声/伴奏独立分类，乐器细类由父项点击延展，模型库全部按用途分组平铺，不再继承当前用途隐藏其他组。
- 紧凑工具布局：页面标题24px、分区16px、正文14px、辅助12px；中文不小于等效12px。
- 移除所有演示样例、合成音轨和假进度。上传并开始分离后，文件进入独立Stage测试服务，提供真实音轨试听及逐轨48kHz/24-bit WAV下载。
- 右侧直接平铺2个当前推荐及3个经典模型，点击不改变卡片顺序，其余可用模型收进可搜索下拉菜单，420px滚动区可拖动滚动条/右下角调整高度，经典版本也按质量排列；手动选中的其他款保留为额外卡片。默认按分离质量排序，年份仅作标签，每款说明一句优势。按模型ID保持单一选中；图钉置顶在当前浏览器刷新后保留，置顶模型优先显示。
- 模型库默认全部330目录按19组平铺，保留原有说明及完整文件名；每卡“使用此模型处理”直接进入工作台，已选模型也可点击并保留输入。前27款加8款乐器模型，共37个版本通过真实6秒歌曲CUDA分离；XL四轨当前显存不足不标可用；只有验证有效的版本显示可使用。其他目录项明确标为未接入，不冒充未下载或可运行。
- `2026 精选/新收录`表示本次整理；DBS-TIGER为2026新模型。SCNet XL DNR在推荐所给官方来源未找到对应影视权重，未用音乐四轨版替代。
- 本轮恢复多导入/导出：每批20文件/合计2GB，后端串行持久批次，刷新恢复；每轨勾选，逐个WAV或服务端ZIP。打包后显示下载链接；不绕过HTTP浏览器下载保护，浏览器实际落盘未验收通过。授权与内部测试说明仅从界面隐藏，不修改内部来源/许可记录。
- 原Hub/provider、权重缓存和其他GPU服务保持；缓存只读复用，新增权重/结果在本预览独立目录。Stage固定10.35.0.0/24，发布前后验证家庭来源访问。

整曲修复：nginx关闭响应临时缓冲，238秒歌曲双轨完整传输和末段播放通过；刷新可恢复任务，避免重复分离。当前release `h-dc49c42eaaba679f`。

质量依据见[推荐记录](quality-review.md)。每模型不再展示作者来源，改为实际可导出分轨与权重大小；未接入项仅标目录目标，原说明保留。乐器转圈的禁用等待光标已修复，16类型可以直接浏览。

来源、版本、验证与恢复见[部署记录](deploy/preview/README.md)和[界面QA](design-qa.md)。长期交付以`TTD:/00_项目/共享测试部署标准.md`为准，所有交付用户的测试链接必须在stage。

默认`npm run build/dev`保留LegacyApp。`npm run build:design/dev:design`启用新版；本地命令仅供开发，不能向用户交付localhost链接。

```sh
npm ci
npm exec -- svelte-check --tsconfig ./tsconfig.json
node scripts/check-studio-design.mjs
npm run build:design
```

本轮是独立preview，未commit/push，也未正式发布Hub。37个模型的功能冒烟不替代用户素材音质评审及完整三端/重启/回滚验收。

本轮交互修正：固定卡片顺序，下拉新项追加后保留；浮层不推移页面。影视同时包含双轨/三轨，任务记录用途和实际输出标签。结果新增可点击定位的真实PCM波形，由服务器峰值缓存生成，旧整曲可直接恢复，无需重新分离。新增2款AliceN对白验证通过，当前37可用/38注册，XL4仍不可用。

本轮模型库可用按钮在后台任务忙碌时也可跳到工作台，保留输入列表；已提交任务按快照处理。批次与ZIP追加在/data/batches和/data/exports，未删除旧jobs。两文件真实CUDA→四轨→ZIP逐字节比对和刷新恢复通过。

显存抢占修复：提交文件后先检查固定显卡资源，不足时保留输入排队；瞬时OOM最多自动重试2次，原生推理配置不变。真实整曲InstVox原批次已恢复。详见design-qa；等待状态并非需要重传。

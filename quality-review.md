# PYMSS 质量推荐依据

2026-10-25人工核对；仅对已接入、可运行的模型给出同用途建议顺序，不把收录年份当质量，不展示虚构评分。不同素材仍需试听。用户置顶优先于建议顺序。

- 人声/伴奏：Leap XE VOC、Deux、HyperACE v2 VOC、HyperACE v2 INST、Leap XE INST、Resurrection VOC/INST。前三侧重较少伴奏串音、双轨完整度、人声厚度与细节；对伴奏有专门需求可选择对应INST。
- DME：BandIt v2多语种、中文专用、BandIt Plus、DBS-TIGER。综合任务覆盖、实际输出格式和可取得权重；中文配音可优先中文模型。DBS为mono且不同测试集，次序不是其质量差的数值结论。
- 主唱/和声：Anvuew侧重叠录和声，Becruily适合多层/多歌手人声；实际输出标签保留目标与残差限制，不承诺纯净主唱或纯和声。
- 清理：默认DeNoise保真取向，按需要提供加强降噪、Crowd群杂、DeReverb混响及Aspiration呼吸处理；都是专业能力选择，不以低质量换速度。

公开参考（页面已阅读）：

1. [Leap XE VOC公开测量](https://sg.mvsep.com/quality_checker/entry/10846)：Multisong vocals SDR11.7920；伴奏18.0995来自mixture减人声，**不能归给专用Leap XE INST权重**。公开fp32/overlap等设置与本地原生运行不完全相同，未声称复现这些分数。
2. [HyperACE v2 VOC](https://mvsep.com/quality_checker/entry/9470)：SDR11.3957并提供fullness/bleedless维度。[HyperACE v2 INST](https://mvsep.com/quality_checker/entry/9475)：SDR17.4007。数字仅作为各条公开记录，未生成本地得分或跨集排名。
3. [MSST社区选型指南](https://msst-bible.pages.dev/tldr)：综合Leap、Deux、HyperACE、Resurrection在人声串音、厚度、伴奏完整度上的试听建议，以及Anvuew/Becruily用途。社区意见不等同保证所有素材最佳。
4. [MVSEP影视模型说明](https://mvsep.com/en/algorithms?page=2)：区分DnRv2/v3、BandIt及其专有服务模型；未把无法下载的MVSEP专有权重伪称已安装，也未把音乐四轨SCNet替代影视DNR。

权重来源/功能冒烟与模型质量推荐是不同证据。19版本本地可运行不等于19种专业用途已获用户音质认可。完整顺序在src/lib/studio/quality.ts，2026标签和过滤不会改变质量优先规则。

## 第一版经典模型补充（2026-10-25）

复用并验证8款经典模型：Becruily人声/伴奏、InstVox Duality v2、FT2 Bleedless、Gabox Bleedless v2伴奏、Kim MelBand、Gabox BS人声、BS Roformer12.97。与现有双轨建议一起排序，没有年份门槛。社区指南的bleedless与classic比较作为能力参考，不给未见同集数据的旧模型虚构质量分数。新增简述另外显示，旧目录原文保留。27可用不等于330目录全可运行。

## 乐器与经典展示补充

加入HTDemucs4/6、BS RoformerSW6、Gilliaan鼓/弦乐、Becruily吉他、MVSEP钢琴/贝斯，8款通过当前GPU真实6秒功能验证。XL4显存不足未启用，未改精度/CPU/offload，不能因名称XL假称更优且可用。多轨参考MSST社区4-6 stems说明（https://msst-bible.pages.dev/4-6-stems-drums-bass-others-vocals-opt-guitar-piano）；不为不同模型虚构统一质量分数。主页显示2当前+3经典代表，选择不重排卡片；完整选择仍按同用途质量与置顶。旧原有模型不再统一显示2026整理标签。

## 分类恢复与影视双轨（2026-10-25）

独立恢复原“人声分离”“伴奏分离”，保留旧目录类别并按各自qualityOrder排序。影视不以三轨数量作准入条件：加入AliceN BS/Mel对白双轨和通用高质量人声双轨；默认代表同时覆盖双轨/三轨。AliceN两款真实6秒功能通过，不能把文件名SDR当作跨数据集排名或电影素材音质保证。歌曲模型在影视语境输出其余声音，不能误称已拆开配乐/音效；原有歌曲用途仍显示伴奏。

## 用户试听优先顺序（2026-10-25）

用户同素材比较认为InstVox Duality v2与BS Roformer12.97最好，duo前两按此偏好设置；保留置顶优先及其他用途排序，不伪称跨数据集公开第一，不按年份置前。

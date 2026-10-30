import fs from "node:fs";
import path from "node:path";

const uiRoot = path.resolve(import.meta.dirname, "..");
const providerRoot = process.env.PYMSS_SOURCE_ROOT || path.resolve(uiRoot, "../pymss");
const catalogPath = path.join(providerRoot, "pymss/resources/model_catalog.json");
const outputPath = path.join(uiRoot, "src/lib/model-advisory-index.ts");

const catalog = JSON.parse(fs.readFileSync(catalogPath, "utf8"));
const models = catalog.models;

const scenarioDefs = [
  { id: "vocal", label: "人声分离", description: "提取干净人声，适合歌曲、对白底本和复杂混音。", outputHint: "vocals / dry vocal" },
  { id: "instrumental", label: "伴奏分离", description: "提取伴奏或无人声轨，适合翻唱、KTV 和后期底本。", outputHint: "instrumental" },
  { id: "karaoke", label: "主唱/伴唱/和声", description: "拆分主唱、伴唱、和声与复杂人声层次。", outputHint: "lead vocal / backing vocal" },
  { id: "dereverb", label: "去混响", description: "去除房间声、回声和空间印记，提取干声。", outputHint: "dry / noreverb" },
  { id: "denoise", label: "降噪/去人群声", description: "处理底噪、人群声、串音和非受控环境噪声。", outputHint: "clean / vocals / target" },
  { id: "speech", label: "对白/语音", description: "影视对白、播客、人声语音和 speech/music/effects 路由。", outputHint: "speech / dialogue" },
  { id: "four_stem", label: "4分轨", description: "鼓、贝斯、人声、其他四轨分离。", outputHint: "drums / bass / vocals / other" },
  { id: "six_stem", label: "6分轨", description: "在四轨基础上进一步分出吉他和钢琴。", outputHint: "drums / bass / vocals / guitar / piano / other" },
  { id: "mega_53", label: "53分轨", description: "按具体乐器微观分轨，适合管弦乐和影视配乐。", outputHint: "single instrument stems" },
  { id: "drums", label: "鼓组", description: "鼓组或 kick/snare/toms/hh 等打击乐细分。", outputHint: "drums / kick / snare / toms" },
  { id: "single_instrument", label: "单乐器", description: "吉他、弦乐、贝斯、钢琴等单乐器提取。", outputHint: "instrument / other" },
  { id: "choir", label: "合唱/性别/多人声", description: "背景和声、合唱、男女声或人群歌声分离。", outputHint: "choir / male / female / backing vocal" },
  { id: "spatial", label: "声像空间", description: "中心声像、宽声场、Mono/Stereo 和空间剖离。", outputHint: "center / wide" },
  { id: "restoration", label: "音频修复", description: "低质量 MP3、高频缺失和受损音源修复。", outputHint: "restored" },
  { id: "breath", label: "呼吸/齿音", description: "提取或抑制呼吸声、齿音等细节元素。", outputHint: "aspiration / breath" },
];

const exactAdvisoryOverrides = {
  "Kim_MelBandRoformer.ckpt": {
    level: "primary",
    ability: "vocals（人声）",
    usage: "推荐依据：SOTA 人声分离；高保真人声提取，保护高频齿音。",
    scenarios: ["vocal"],
  },
  "model_bs_roformer_ep_368_sdr_12.9628.ckpt": {
    level: "primary",
    ability: "vocals（人声）",
    usage: "推荐依据：BS-RoFormer 高质量双轨；适合通用歌曲人声分离。",
    scenarios: ["vocal"],
  },
  "mel_band_roformer_vocals_gabox.ckpt": {
    level: "primary",
    ability: "vocals（人声）",
    usage: "推荐依据：MelBand RoFormer 人声强模型；适合复杂混音主唱提取。",
    scenarios: ["vocal"],
  },
  "BS-Roformer-Resurrection.ckpt": {
    level: "primary",
    ability: "vocals（人声）",
    usage: "推荐依据：BS-RoFormer 人声模型；适合高质量通用人声分离。",
    scenarios: ["vocal"],
  },
  "kimmel_unwa_ft2.ckpt": {
    level: "featured",
    ability: "vocals（人声）",
    usage: "推荐依据：社区常用人声微调版；适合保留齿音细节的人声提取。",
    scenarios: ["vocal"],
  },
  "BS-Roformer-Resurrection-Inst.ckpt": {
    level: "primary",
    ability: "instrumental（伴奏）",
    usage: "推荐依据：BS-RoFormer 伴奏强模型；适合高质量去人声。",
    scenarios: ["instrumental"],
  },
  "bs_roformer_instrumental_resurrection_gabox.ckpt": {
    level: "primary",
    ability: "instrumental（伴奏）",
    usage: "推荐依据：RoFormer 伴奏模型；适合伴奏提取与批量处理。",
    scenarios: ["instrumental"],
  },
  "mel_band_roformer_instrumental_becruily.ckpt": {
    level: "primary",
    ability: "instrumental（伴奏）",
    usage: "推荐依据：MelBand 伴奏模型；适合保留伴奏细节。",
    scenarios: ["instrumental"],
  },
  "mel_band_roformer_instrumental_gabox.ckpt": {
    level: "primary",
    ability: "instrumental（伴奏）",
    usage: "推荐依据：伴奏提取强模型；适合去人声与保留伴奏细节。",
    scenarios: ["instrumental"],
  },
  "mel_band_roformer_instrumental_fv8_gabox.ckpt": {
    level: "primary",
    ability: "instrumental（伴奏）",
    usage: "推荐依据：SOTA 双轨分离；适合高质量伴奏/人声拆分。",
    scenarios: ["instrumental"],
  },
  "small_karaoke_gaboxaufr.ckpt": {
    level: "featured",
    ability: "backing_vocal（和声）",
    usage: "推荐依据：轻量伴唱模型；适合 backing vocal/和声测试。",
    scenarios: ["karaoke"],
  },
  "mel_band_roformer_karaoke_gabox_v2.ckpt": {
    level: "primary",
    ability: "lead/backing vocal（主唱/伴唱）",
    usage: "推荐依据：Karaoke 强模型；适合主唱、和声、伴唱分离。",
    scenarios: ["karaoke"],
  },
  "mel_band_roformer_karaoke_gabox.ckpt": {
    level: "primary",
    ability: "lead/backing vocal（主唱/伴唱）",
    usage: "推荐依据：MelBand Karaoke；适合 lead/backing vocal 拆分。",
    scenarios: ["karaoke"],
  },
  "bs_roformer_karaoke_anvuew.ckpt": {
    level: "primary",
    ability: "lead/backing vocal（主唱/伴唱）",
    usage: "推荐依据：BS-RoFormer Karaoke；适合主唱/伴唱分离。",
    scenarios: ["karaoke"],
  },
  "model_chorus_bs_roformer_ep_267_sdr_24.1275.ckpt": {
    level: "primary",
    ability: "male/female vocals（男女声）",
    usage: "推荐依据：男女声/合唱分离；适合对唱、合唱声部拆分。",
    scenarios: ["choir"],
  },
  "bs_roformer_male_female_by_aufr33_sdr_7.2889.ckpt": {
    level: "primary",
    ability: "male/female vocals（男女声）",
    usage: "推荐依据：Male/Female 分离；适合男女声拆分。",
    scenarios: ["choir"],
  },
  "model_scnet_masked_ep_14_sdr_6.9052.ckpt": {
    level: "featured",
    ability: "choir（合唱）",
    usage: "推荐依据：合唱子轨模型；适合 soprano/alto/tenor/bass 测试。",
    scenarios: ["choir"],
  },
  "model_scnet_ep_42_sdr_5.2559.ckpt": {
    level: "featured",
    ability: "choir（合唱）",
    usage: "推荐依据：输出目标 choir；适合合唱提取，需按素材实测。",
    scenarios: ["choir"],
  },
  "model_bandit_plus_dnr_sdr_11.47.ckpt": {
    level: "primary",
    ability: "speech/music/effects（三分轨）",
    usage: "推荐依据：DNR 三分轨模型；适合 speech/music/effects 分离。",
    scenarios: ["speech"],
  },
  "checkpoint-multi_fixed.ckpt": {
    level: "primary",
    ability: "speech/music/effects（三分轨）",
    usage: "推荐依据：对白/音乐/音效三分轨；适合影视素材拆分。",
    scenarios: ["speech"],
  },
  "BS-Roformer-SW.ckpt": {
    level: "primary",
    ability: "6 stems（六分轨）",
    usage: "推荐依据：6 分轨强模型；输出 bass/drums/guitar/piano/vocals/other。",
    scenarios: ["six_stem", "four_stem"],
  },
  "logic_bs_roformer.ckpt": {
    level: "featured",
    ability: "6 stems（六分轨）",
    usage: "推荐依据：BS-RoFormer 六分轨；适合复杂音乐分层。",
    scenarios: ["six_stem"],
  },
  "HTDemucs4_6stems.th": {
    level: "featured",
    ability: "6 stems（六分轨）",
    usage: "推荐依据：Demucs 六分轨；适合稳定通用拆分与对照测试。",
    scenarios: ["six_stem"],
  },
  "gabox_karaoke_25_02_2025.ckpt": {
    level: "featured",
    ability: "instrumental / karaoke（伴奏/和声）",
    usage: "推荐依据：Karaoke 权重实际为单输出头；适合伴奏或和声方向实测，不作为六分轨首选。",
    scenarios: ["instrumental", "karaoke"],
    replaceScenarios: true,
  },
  "HTDemucs4.th": {
    level: "featured",
    ability: "4 stems（四分轨）",
    usage: "推荐依据：稳定四分轨模型；适合通用拆分与对照测试。",
    scenarios: ["four_stem"],
  },
  "model_mdx23c_ep_168_sdr_7.0207.ckpt": {
    level: "primary",
    ability: "4 stems（四分轨）",
    usage: "推荐依据：MDX23C 四分轨；适合 bass/drums/vocals/other。",
    scenarios: ["four_stem"],
  },
  "bs_roformer_4stems_ft.ckpt": {
    level: "featured",
    ability: "4 stems（四分轨）",
    usage: "推荐依据：BS-RoFormer 四分轨；适合高质量音乐分层。",
    scenarios: ["four_stem"],
  },
  "huge_scnet_4stems_fullness.ckpt": {
    level: "featured",
    ability: "4 stems（四分轨）",
    usage: "推荐依据：SCNet 四分轨；适合更高质量但显存更高。",
    scenarios: ["four_stem"],
  },
  "huge_scnet_4stems_v1.2.ckpt": {
    level: "featured",
    ability: "4 stems（四分轨）",
    usage: "推荐依据：SCNet 高质量四分轨；适合更高质量但显存更高。",
    scenarios: ["four_stem"],
  },
  "huge_scnet_4stems_bleedless.ckpt": {
    level: "featured",
    ability: "4 stems（四分轨）",
    usage: "推荐依据：SCNet 防串音四分轨；适合减少鼓、贝斯、人声互漏。",
    scenarios: ["four_stem", "denoise"],
  },
  "aufr33-jarredou_DrumSep_model_mdx23c_ep_141_sdr_10.8059.ckpt": {
    level: "primary",
    ability: "drums（鼓组）",
    usage: "推荐依据：DrumSep 鼓组模型；适合鼓组细分提取。",
    scenarios: ["drums"],
  },
  "drumsep_5stems_mdx23c_jarredou.ckpt": {
    level: "featured",
    ability: "drums（鼓组）",
    usage: "推荐依据：5 stems 鼓组拆分；适合鼓组层次提取。",
    scenarios: ["drums"],
  },
  "model_drumsep.th": {
    level: "featured",
    ability: "drums（鼓组）",
    usage: "推荐依据：鼓组拆分备选；适合稳定对照与轻量测试。",
    scenarios: ["drums"],
  },
  "Apollo_LQ_MP3_restoration.ckpt": {
    level: "featured",
    ability: "restoration（音频修复）",
    usage: "推荐依据：音频修复模型；适合低质 MP3 高频细节补全。",
    scenarios: ["restoration"],
  },
  "apollo_model_v2.ckpt": {
    level: "featured",
    ability: "restoration（音频修复）",
    usage: "推荐依据：频段重建模型；适合压缩损伤和低质素材修复。",
    scenarios: ["restoration"],
  },
  "apollo_model.ckpt": {
    level: "featured",
    ability: "restoration（音频修复）",
    usage: "推荐依据：音频修复模型；适合破音、压缩损伤、低质素材修复。",
    scenarios: ["restoration"],
  },
  "dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt": {
    level: "primary",
    ability: "dereverb（去混响）",
    usage: "推荐依据：BS-RoFormer 去混响；适合人声/对白混响减弱。",
    scenarios: ["dereverb"],
  },
  "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt": {
    level: "primary",
    ability: "dereverb（去混响）",
    usage: "推荐依据：MelBand 去混响强模型；适合提取干爽对白底本。",
    scenarios: ["dereverb"],
  },
  "dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt": {
    level: "primary",
    ability: "dereverb（去混响）",
    usage: "推荐依据：轻度去混响模型；适合保留自然尾音。",
    scenarios: ["dereverb"],
  },
  "dereverb_super_big_mbr_ep_346.ckpt": {
    level: "featured",
    ability: "dereverb（去混响）",
    usage: "推荐依据：大参数去混响模型；适合质量优先的人声干声提取。",
    scenarios: ["dereverb"],
  },
  "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt": {
    level: "primary",
    ability: "denoise（降噪）",
    usage: "推荐依据：降噪专用模型；适合噪声、人群声、底噪处理。",
    scenarios: ["denoise"],
  },
  "denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt": {
    level: "primary",
    ability: "denoise（降噪）",
    usage: "推荐依据：强降噪版本；适合噪声更重的素材。",
    scenarios: ["denoise"],
  },
  "mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt": {
    level: "primary",
    ability: "denoise（去人群声）",
    usage: "推荐依据：去人群声模型；适合演唱会欢呼掌声抑制。",
    scenarios: ["denoise"],
  },
  "speech_bs_roformer_AliceN_sdr_20.4440.ckpt": {
    level: "featured",
    ability: "speech（语音增强）",
    usage: "推荐依据：语音增强模型；适合对白清晰度提升。",
    scenarios: ["denoise"],
  },
  "speech_mel_roformer_AliceN_sdr_16.5716.ckpt": {
    level: "featured",
    ability: "speech（语音增强）",
    usage: "推荐依据：MelBand 语音增强模型；适合对白清晰度提升。",
    scenarios: ["denoise"],
  },
  "aspiration_mel_band_roformer_sdr_18.9845.ckpt": {
    level: "featured",
    ability: "breath（呼吸/齿音）",
    usage: "推荐依据：呼吸声目标模型；适合呼吸、齿音提取或抑制。",
    scenarios: ["breath"],
  },
  "mvsep_mega_model_bs_roformer_53_stems_v1.ckpt": {
    level: "featured",
    ability: "53 stems（53分轨）",
    usage: "推荐依据：53 分轨总模型；适合多乐器对象定位与素材拆解。",
    scenarios: ["mega_53", "single_instrument"],
  },
  "gilliaan_CenterExtractor_Single_StemV1.ckpt": {
    level: "featured",
    ability: "center/wide（声像空间）",
    usage: "推荐依据：声像空间剖离；适合中心结像与宽声场环境音拆分。",
    scenarios: ["spatial"],
  },
};

function lowerParts(model) {
  return [
    model.name,
    model.primary_category,
    model.primary_category_cn,
    model.secondary_category,
    model.secondary_category_cn,
    model.target_stem,
    model.config_instruments,
    model.config_target_instrument,
    model.classification_basis,
    model.model_type,
    model.architecture,
  ].join(" ").toLowerCase();
}

function includesAny(text, words) {
  return words.some((word) => text.includes(word));
}

function mergeScenarios(base, extra) {
  return [...new Set([...(base || []), ...(extra || [])])];
}

function exactScenarioRank(model, scenarioId) {
  const ranks = {
    vocal: {
      "Kim_MelBandRoformer.ckpt": 1,
      "mel_band_roformer_vocals_gabox.ckpt": 2,
      "BS-Roformer-Resurrection.ckpt": 3,
    },
    instrumental: {
      "BS-Roformer-Resurrection-Inst.ckpt": 1,
      "bs_roformer_instrumental_resurrection_gabox.ckpt": 2,
      "mel_band_roformer_instrumental_becruily.ckpt": 3,
    },
    karaoke: {
      "mel_band_roformer_karaoke_gabox_v2.ckpt": 1,
      "mel_band_roformer_karaoke_gabox.ckpt": 2,
      "bs_roformer_karaoke_anvuew.ckpt": 3,
    },
    choir: {
      "model_chorus_bs_roformer_ep_267_sdr_24.1275.ckpt": 1,
      "bs_roformer_male_female_by_aufr33_sdr_7.2889.ckpt": 2,
      "model_scnet_masked_ep_14_sdr_6.9052.ckpt": 3,
    },
    speech: {
      "checkpoint-multi_fixed.ckpt": 1,
      "model_bandit_plus_dnr_sdr_11.47.ckpt": 2,
    },
    four_stem: {
      "model_mdx23c_ep_168_sdr_7.0207.ckpt": 1,
      "bs_roformer_4stems_ft.ckpt": 2,
      "huge_scnet_4stems_fullness.ckpt": 3,
    },
    six_stem: {
      "BS-Roformer-SW.ckpt": 1,
      "logic_bs_roformer.ckpt": 2,
      "HTDemucs4_6stems.th": 3,
    },
    drums: {
      "aufr33-jarredou_DrumSep_model_mdx23c_ep_141_sdr_10.8059.ckpt": 1,
      "drumsep_5stems_mdx23c_jarredou.ckpt": 2,
      "model_drumsep.th": 3,
    },
    mega_53: {
      "mvsep_mega_model_bs_roformer_53_stems_v1.ckpt": 1,
      "bs_mega_53stem_piano_mvsep.ckpt": 2,
      "bs_mega_53stem_strings_mvsep.ckpt": 3,
    },
    single_instrument: {
      "mvsep_mega_model_bs_roformer_53_stems_v1.ckpt": 1,
      "bs_mega_53stem_piano_mvsep.ckpt": 2,
      "bs_mega_53stem_strings_mvsep.ckpt": 3,
    },
    dereverb: {
      "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt": 1,
      "dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt": 2,
      "dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt": 3,
    },
    denoise: {
      "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt": 1,
      "denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt": 2,
      "mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt": 3,
    },
    restoration: {
      "Apollo_LQ_MP3_restoration.ckpt": 1,
      "apollo_model_v2.ckpt": 2,
      "apollo_model.ckpt": 3,
    },
  };
  return ranks[scenarioId]?.[model.name] ?? null;
}

function scenarioRanksFor(model, scenarioIds) {
  const ranks = {};
  for (const scenarioId of scenarioIds) {
    const rank = exactScenarioRank(model, scenarioId);
    if (rank) ranks[scenarioId] = rank;
  }
  return ranks;
}

function instrumentName(model) {
  return (model.target_stem || model.name.replace(/^bs_mega_53stem_/, "").replace(/_mvsep\.ckpt$/i, "")).replaceAll("_", "-");
}

function seriesAdvisoryOverride(model) {
  const exact = exactAdvisoryOverrides[model.name];
  if (exact) return exact;

  const text = lowerParts(model);
  const name = model.name.toLowerCase();

  if (model.name.startsWith("bs_mega_53stem_")) {
    const stem = instrumentName(model);
    const ability = stem === "piano" ? "piano（钢琴）" :
      stem.includes("string") ? "strings（弦乐）" :
      stem.includes("guitar") ? "guitar（吉他）" :
      stem.includes("drum") ? "drums（鼓组）" :
      "53 stems（53分轨）";
    const usage = stem === "piano" ? "推荐依据：53 分轨钢琴子模型；适合钢琴提取与素材定位。" :
      stem.includes("string") ? "推荐依据：53 分轨弦乐子模型；适合弦乐层定位与提取。" :
      stem.includes("guitar") ? "推荐依据：53 分轨吉他子模型；适合吉他声部定位。" :
      stem.includes("drum") ? "推荐依据：53 分轨鼓组子模型；适合鼓组元素定位。" :
      `推荐依据：53 分轨单乐器模型；适合 ${stem} 定位与提取。`;
    return { level: "featured", ability, usage, scenarios: ["mega_53", "single_instrument"] };
  }

  if (model.secondary_category === "dnr_stems" || includesAny(text, ["speech/music/effects", "dnr"])) {
    return {
      level: name.includes("v2") ? "featured" : "primary",
      ability: "speech/music/effects（三分轨）",
      usage: "推荐依据：影视三分轨模型；适合对白、音乐、音效拆分。",
      scenarios: ["speech"],
    };
  }

  if (includesAny(text, ["karaoke", "backing_vocal", "bve", "back-vocal"])) {
    if (name.includes("becruily")) {
      return {
        level: "featured",
        ability: "backing vocal（伴唱）",
        usage: "推荐依据：伴唱分离表现好；适合和声、人声垫底提取。",
        scenarios: ["karaoke"],
      };
    }
    if (name.includes("bve")) {
      return {
        level: "featured",
        ability: "backing vocal（伴唱）",
        usage: model.model_type === "scnet" ? "推荐依据：BVE 人声子轨模型；适合主唱/伴唱辅助拆分。" : "推荐依据：RoFormer BVE 模型；适合复杂人声层次分离。",
        scenarios: ["karaoke"],
      };
    }
    return {
      level: "primary",
      ability: "lead/backing vocal（主唱/伴唱）",
      usage: "推荐依据：Karaoke 强模型；适合主唱、和声、伴唱分离。",
      scenarios: ["karaoke"],
    };
  }

  if (includesAny(text, ["male", "female"])) {
    return {
      level: "primary",
      ability: "male/female vocals（男女声）",
      usage: "推荐依据：男女声分离模型；适合对唱、合唱声部拆分。",
      scenarios: ["choir"],
    };
  }

  if (includesAny(text, ["choir", "chorus", "vocal sub-stem"])) {
    return {
      level: "featured",
      ability: "choir（合唱）",
      usage: "推荐依据：合唱/人声子轨模型；适合合唱、重叠人声测试。",
      scenarios: ["choir"],
    };
  }

  if (model.secondary_category === "drum_stems" || includesAny(text, ["drumsep"])) {
    return {
      level: name.includes("xl") ? "primary" : "featured",
      ability: "drums（鼓组）",
      usage: "推荐依据：鼓组细分模型；适合 kick/snare/cymbals/toms 拆分。",
      scenarios: ["drums"],
    };
  }

  if (model.secondary_category === "six_stem") {
    return {
      level: "featured",
      ability: "6 stems（六分轨）",
      usage: "推荐依据：六分轨模型；适合 bass/drums/guitar/piano/vocals/other 拆分。",
      scenarios: ["six_stem", "four_stem"],
    };
  }

  if (model.secondary_category === "four_stem") {
    if (includesAny(text, ["mdx23", "mvsep mdx23"])) {
      return {
        level: "primary",
        ability: "4 stems（四分轨）",
        usage: "推荐依据：经典四分轨强模型；适合 bass/drums/vocals/other。",
        scenarios: ["four_stem"],
      };
    }
    if (includesAny(text, ["demucs", "htdemucs"])) {
      return {
        level: "featured",
        ability: "4 stems（四分轨）",
        usage: "推荐依据：稳定四分轨模型；适合通用拆分与对照测试。",
        scenarios: ["four_stem"],
      };
    }
    if (includesAny(text, ["scnet"])) {
      return {
        level: "featured",
        ability: "4 stems（四分轨）",
        usage: "推荐依据：SCNet 高质量四分轨；适合更高质量但显存更高。",
        scenarios: ["four_stem"],
      };
    }
  }

  if (model.primary_category === "vocal" || model.secondary_category === "vocal_extraction" || includesAny(text, ["target_instrument=vocals", "vocals_gabox", "vocals_fv"])) {
    if (includesAny(text, ["bs_roformer", "roformer"])) {
      return {
        level: "primary",
        ability: "vocals（人声）",
        usage: "推荐依据：RoFormer 高质量双轨；适合通用歌曲人声分离。",
        scenarios: ["vocal"],
      };
    }
  }

  if (model.primary_category === "instrumental" || model.target_stem === "instrumental") {
    if (includesAny(text, ["bs_roformer", "mel_band_roformer", "roformer"])) {
      return {
        level: "primary",
        ability: "instrumental（伴奏）",
        usage: "推荐依据：伴奏提取强模型；适合去人声与保留伴奏细节。",
        scenarios: ["instrumental"],
      };
    }
    if (includesAny(text, ["uvr-mdx-net", "inst hq", "inst_hq"])) {
      return {
        level: "featured",
        ability: "instrumental（伴奏）",
        usage: "推荐依据：经典伴奏模型；适合稳定去人声与批量处理。",
        scenarios: ["instrumental"],
      };
    }
  }

  if (model.secondary_category === "dereverb" || model.secondary_category === "dereverb_deecho") {
    return {
      level: "primary",
      ability: "dereverb（去混响）",
      usage: "推荐依据：去混响专用模型；适合对白/人声混响减弱。",
      scenarios: ["dereverb"],
    };
  }

  if (includesAny(text, ["denoise", "crowd", "debleed", "noise_bleed_control"])) {
    return {
      level: "primary",
      ability: "denoise（降噪）",
      usage: "推荐依据：降噪专用模型；适合噪声、人群声、底噪处理。",
      scenarios: ["denoise"],
    };
  }

  if (includesAny(text, ["speech_vocal", "speech"])) {
    return {
      level: "featured",
      ability: "speech（语音增强）",
      usage: "推荐依据：语音增强模型；适合对白清晰度提升。",
      scenarios: ["denoise"],
    };
  }

  if (model.secondary_category === "audio_restoration" || includesAny(text, ["restoration", "apollo"])) {
    return {
      level: "featured",
      ability: "restoration（音频修复）",
      usage: "推荐依据：音频修复模型；适合破音、压缩损伤、低质素材修复。",
      scenarios: ["restoration"],
    };
  }

  return null;
}

function scenarioIdsFor(model) {
  const text = lowerParts(model);
  const ids = new Set();
  if (model.primary_category === "vocal" || includesAny(text, ["vocal_extraction", "target_instrument=vocals", " vocals", "人声提取"])) ids.add("vocal");
  if (model.primary_category === "instrumental" || includesAny(text, ["instrumental", "伴奏", "无人声"])) ids.add("instrumental");
  if (model.primary_category === "reverb_echo_control" || includesAny(text, ["dereverb", "deverb", "deecho", "reverb", "echo", "去混响", "回声"])) ids.add("dereverb");
  if (includesAny(text, ["denoise", "noise", "crowd", "bleed", "debleed", "降噪", "串音", "人群"])) ids.add("denoise");
  if (includesAny(text, ["speech/music/effects", "dialogue/music/sfx", "speech/music/sfx", "dialogue", "dialog", "dnr", "effects"])) ids.add("speech");
  if (model.secondary_category === "four_stem" || includesAny(text, ["four_stem", "4 stems", "四轨", "drums/bass/other/vocals"])) ids.add("four_stem");
  if (model.secondary_category === "six_stem" || includesAny(text, ["six_stem", "6分轨", "guitar/piano", "drums/bass/other/vocals/guitar/piano"])) ids.add("six_stem");
  if (model.secondary_category === "mega_53_stems" || model.name.startsWith("bs_mega_53stem_") || includesAny(text, ["53-stem", "53 轨", "53分轨"])) ids.add("mega_53");
  if (model.secondary_category === "drum_stems" || includesAny(text, ["drum", "kick", "snare", "toms", "hh", "ride", "crash", "鼓"])) ids.add("drums");
  if (model.primary_category === "single_instrument" || model.secondary_category === "mega_53_stems" || model.name.startsWith("bs_mega_53stem_") || includesAny(text, ["单乐器"])) ids.add("single_instrument");
  if (includesAny(text, ["backing", "karaoke", "bve", "back-vocal", "伴唱", "和声"])) ids.add("karaoke");
  if (model.secondary_category?.includes("choir") || includesAny(text, ["choir", "chorus", "male", "female", "合唱", "男女"])) ids.add("choir");
  if (model.primary_category === "spatial" || includesAny(text, ["center", "wide", "phantom", "mono", "stereo", "声像", "空间"])) ids.add("spatial");
  if (model.secondary_category === "audio_restoration" || includesAny(text, ["restoration", "restored", "apollo", "mp3", "修复"])) ids.add("restoration");
  if (includesAny(text, ["aspiration", "breath", "sibilance", "呼吸", "齿音"])) ids.add("breath");
  const override = seriesAdvisoryOverride(model);
  if (override?.replaceScenarios) return [...override.scenarios];
  for (const id of override?.scenarios ?? []) ids.add(id);
  return [...ids];
}

function sizeTier(size) {
  if (size >= 4 * 1024 ** 3) return "超大";
  if (size >= 1024 ** 3) return "大";
  if (size >= 512 * 1024 ** 2) return "中";
  return "小";
}

function riskText(model) {
  const tier = sizeTier(model.size_bytes);
  if (tier === "超大") return "超大模型，优先用于质量压倒速度的场景，显存压力高。";
  if (tier === "大") return "大模型，质量优先，建议 GPU 空闲时使用。";
  if (tier === "中") return "中等体积，质量和速度相对均衡。";
  return "轻量模型，适合快速试跑和低成本处理。";
}

function autoNote(model, scenarioIds) {
  const override = seriesAdvisoryOverride(model);
  if (override) return [override.ability, override.usage];
  if (model.name.startsWith("bs_mega_53stem_")) {
    const stem = model.name.replace("bs_mega_53stem_", "").replace("_mvsep.ckpt", "");
    return [`53分轨`, `单独提取 ${stem}，适合需要精细乐器 stem 的场景。`];
  }
  const category = model.secondary_category_cn || model.primary_category_cn || "通用分离";
  const target = model.target_stem || model.config_target_instrument || model.config_instruments || "";
  const targetText = target ? `输出目标：${target}。` : "";
  const confidenceText = model.classification_confidence === "low" ? "分类置信度较低，建议先短音频试跑。" : "";
  const basis = model.classification_basis ? `依据：${model.classification_basis}` : "";
  return [category, `${targetText}${confidenceText || basis}`.trim() || `${model.architecture} 架构，适合 ${category} 场景。`];
}

function recommendationLevel(model) {
  return seriesAdvisoryOverride(model)?.level ?? "none";
}

function priority(model, scenarioIds, manual, level) {
  let score = 0;
  if (level === "primary") score += 3000;
  if (level === "featured") score += 2000;
  if (manual) score += 300;
  if (model.classification_confidence === "high") score += 150;
  if (model.classification_confidence === "medium") score += 70;
  score += scenarioIds.length * 20;
  if (model.size_bytes < 512 * 1024 ** 2) score += 20;
  if (model.size_bytes > 4 * 1024 ** 3) score -= 30;
  if (model.name.startsWith("bs_mega_53stem_")) score += 60;
  return score;
}

function normalizeText(model, note, scenarioIds) {
  return [
    model.name,
    ...(model.aliases || []),
    model.model_type,
    model.architecture,
    model.primary_category,
    model.primary_category_cn,
    model.secondary_category,
    model.secondary_category_cn,
    model.target_stem,
    model.config_instruments,
    model.config_target_instrument,
    model.classification_basis,
    note.ability,
    note.usage,
    ...scenarioIds,
  ].filter(Boolean).join(" ").toLowerCase();
}

const entries = models.map((model) => {
  const scenarios = scenarioIdsFor(model);
  const [ability, usage] = autoNote(model, scenarios);
  const level = recommendationLevel(model);
  const manual = level !== "none";
  const note = { ability, usage, sourceRepresentative: manual ? model.name : "model_catalog.json" };
  const scenarioRanks = scenarioRanksFor(model, scenarios);
  return {
    id: model.name,
    primaryCategoryCn: model.primary_category_cn,
    secondaryCategoryCn: model.secondary_category_cn,
    modelType: model.model_type || "",
    architecture: model.architecture || "",
    targetStem: model.target_stem || "",
    configInstruments: model.config_instruments || "",
    configTargetInstrument: model.config_target_instrument || "",
    classificationConfidence: model.classification_confidence || "",
    classificationBasis: model.classification_basis || "",
    scenarios,
    scenarioRanks,
    note,
    recommendationLevel: level,
    manualNote: manual,
    sizeTier: sizeTier(model.size_bytes),
    risk: riskText(model),
    priority: priority(model, scenarios, manual, level),
    searchText: normalizeText(model, note, scenarios),
  };
});

const content = `// Generated by scripts/generate-model-advisory-index.mjs from pymss/resources/model_catalog.json.\n` +
`// Do not edit individual entries by hand; update the generator or source catalog.\n\n` +
`export type AdvisoryScenarioId = ${scenarioDefs.map((s) => JSON.stringify(s.id)).join(" | ")};\n\n` +
`export type RecommendationLevel = "primary" | "featured" | "none";\n\n` +
`export interface AdvisoryScenario {\n  id: AdvisoryScenarioId;\n  label: string;\n  description: string;\n  outputHint: string;\n}\n\n` +
`export interface ModelAdvisory {\n  id: string;\n  primaryCategoryCn: string;\n  secondaryCategoryCn: string;\n  modelType: string;\n  architecture: string;\n  targetStem: string;\n  configInstruments: string;\n  configTargetInstrument: string;\n  classificationConfidence: string;\n  classificationBasis: string;\n  scenarios: AdvisoryScenarioId[];\n  scenarioRanks: Partial<Record<AdvisoryScenarioId, number>>;\n  note: { ability: string; usage: string; sourceRepresentative: string };\n  recommendationLevel: RecommendationLevel;\n  manualNote: boolean;\n  sizeTier: string;\n  risk: string;\n  priority: number;\n  searchText: string;\n}\n\n` +
`export const advisoryScenarios = ${JSON.stringify(scenarioDefs, null, 2)} as const satisfies readonly AdvisoryScenario[];\n\n` +
`export const modelAdvisoryIndex = ${JSON.stringify(entries, null, 2)} as const satisfies readonly ModelAdvisory[];\n\n` +
`export const modelAdvisoryById: Record<string, ModelAdvisory> = Object.fromEntries(\n  modelAdvisoryIndex.map((entry) => [entry.id, entry]),\n);\n`;

fs.writeFileSync(outputPath, content);
console.log(`wrote ${entries.length} entries to ${outputPath}`);

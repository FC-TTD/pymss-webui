import {vocalModelIds,instrumentalModelIds,type StudioModel} from './models';
// Task-specific editorial ordering, checked 2026-10-25. Never sort by release/curation year.
// Public benchmark measurements and community listening advice are references, not local quality scores.
export const qualityOrder:Record<string,string[]> = {
 duo:['melband_roformer_instvox_duality_v2.ckpt','model_bs_roformer_ep_368_sdr_12.9628.ckpt','bs_leap_xe_voc.ckpt','becruily_deux.ckpt','bs_roformer_voc_hyperacev2.ckpt','bs_roformer_inst_hyperacev2.ckpt','bs_leap_xe_inst.ckpt','BS-Roformer-Resurrection.ckpt','BS-Roformer-Resurrection-Inst.ckpt','mel_band_roformer_vocals_becruily.ckpt','mel_band_roformer_instrumental_becruily.ckpt','kimmel_unwa_ft2_bleedless.ckpt','mel_band_roformer_instrumental_bleedless_v2_gabox.ckpt','Kim_MelBandRoformer.ckpt','bs_roformer_vocals_gabox.ckpt'],
 vocal:vocalModelIds,
 instrumental:instrumentalModelIds,
 dme:['speech_bs_roformer_AliceN_sdr_20.4440.ckpt','speech_mel_roformer_AliceN_sdr_16.5716.ckpt',...vocalModelIds,'bandit_v2_multi.ckpt','checkpoint-cmn_state_dict.ckpt','model_bandit_plus_dnr_sdr_11.47.ckpt','DBS-TIGER-DnR'],
 karaoke:['bs_roformer_karaoke_anvuew.ckpt','mel_band_roformer_karaoke_becruily.ckpt'],
 cleanup:['denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt','denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt','mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt','dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt','aspiration_mel_band_roformer_sdr_18.9845.ckpt','aspiration_mel_band_roformer_less_aggr_sdr_18.1201.ckpt'],
 dereverb:['dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt'],
 stems:['BS-Roformer-SW.ckpt','mel_band_roformer_4stems_xl_ver1.ckpt','HTDemucs4_6stems.th','HTDemucs4.th','gilliaan_drumsV1.ckpt','becruily_guitar.ckpt','bs_mega_53stem_piano_mvsep.ckpt','bs_mega_53stem_bass_mvsep.ckpt','gilliaan_bowedstrings_bs_v1.ckpt'],
 four:['mel_band_roformer_4stems_xl_ver1.ckpt','HTDemucs4.th'],
 six:['BS-Roformer-SW.ckpt','HTDemucs4_6stems.th'],
 denoise:['denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt','denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt'],
 crowd:['mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt'],
 breath:['aspiration_mel_band_roformer_sdr_18.9845.ckpt','aspiration_mel_band_roformer_less_aggr_sdr_18.1201.ckpt'],
};
export const qualityReferences=[
 {title:'MVSEP · Leap XE公开评测',url:'https://sg.mvsep.com/quality_checker/entry/10846'},
 {title:'MVSEP · HyperACE v2人声评测',url:'https://mvsep.com/quality_checker/entry/9470'},
 {title:'MVSEP · HyperACE v2伴奏评测',url:'https://mvsep.com/quality_checker/entry/9475'},
 {title:'MSST社区 · 模型选用建议',url:'https://msst-bible.pages.dev/tldr'},
 {title:'MVSEP · 影视三轨模型说明',url:'https://mvsep.com/en/algorithms?page=2'},
];
export function qualityRank(model:StudioModel,scenario:string):number {
 const own=qualityOrder[scenario] || qualityOrder[model.scenarios[0]] || [];
 const rank=own.indexOf(model.id);const tasks=['duo','dme','karaoke','cleanup','dereverb','breath','stems'];return rank<0?1000:rank+(scenario==='all'?Math.max(0,tasks.indexOf(model.scenarios[0]))*100:0);
}
export function compareQuality(a:StudioModel,b:StudioModel,scenario:string,pins:string[]=[]):number {
 return Number(pins.includes(b.id))-Number(pins.includes(a.id)) || qualityRank(a,scenario)-qualityRank(b,scenario) || a.title.localeCompare(b.title,'zh-CN');
}

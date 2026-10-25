import snapshot from './catalog-snapshot.json';
import originalDescriptions from './original-descriptions.json';
import { getAdvisory } from '../model-selection';
import { stemChineseLabel } from '../stem-labels';

export interface Stem { id: string; label: string }
export interface StudioModel {
  id: string; title: string; description: string; originalDescription?: string; classic?: boolean; scenarios: string[];
  tag: string; state: 'ready' | 'downloaded' | 'missing' | 'planned'; stems: Stem[];
  source: string; caution: string; size: number; curated: boolean;
}
export const scenarios = [
  { id: 'duo', label: '人声与伴奏', description: '把歌曲拆成人声与伴奏，方便翻唱、混音和配乐。' },
  { id: 'vocal', label: '人声分离', description: '优先选择擅长提取人声的模型，同时保留其余声音。' },
  { id: 'instrumental', label: '伴奏分离', description: '优先选择擅长保留伴奏细节、抑制人声残留的模型。' },
  { id: 'dme', label: '影视分离 DME', description: '支持对白/其余声音双轨，以及对白/配乐/音效三轨，按实际模型输出。' },
  { id: 'karaoke', label: '主唱与和声', description: '进一步分离主唱与伴唱，建议先对短片段试听。' },
  { id: 'cleanup', label: '对白清理', description: '按素材需要选择降噪、去人群声、气声或去混响。' },
  { id: 'dereverb', label: '去混响', description: '减少空间混响，提取干声并保留残差。' },
  { id: 'breath', label: '呼吸声', description: '分离气声与其余声音，不保证去除喷麦或口水音。' },
  { id: 'stems', label: '乐器分轨', description: '按模型能力输出多条乐器轨或指定乐器。' },
  { id: 'denoise', label: '降噪', description: '降低持续底噪，比较细节保留与噪声抑制。' },
  { id: 'crowd', label: '人群声', description: '分离人群喧哗与其余声音，方便独立调整群杂声。' },
  { id: 'four', label: '四轨分离', description: '输出人声、鼓、贝斯与其他乐器。' },
  { id: 'six', label: '六轨分离', description: '进一步独立输出吉他与钢琴，适合多轨混音。' },
  { id: 'drums', label: '鼓', description: '提取鼓组，便于单独调整节奏层。' },
  { id: 'bass', label: '贝斯', description: '提取贝斯声部，便于检查低频演奏。' },
  { id: 'guitar', label: '吉他', description: '提取吉他声部，便于独立精修。' },
  { id: 'piano', label: '钢琴', description: '提取钢琴声部，便于对照演奏细节。' },
  { id: 'strings', label: '弦乐', description: '提取弓弦乐声部，便于独立调整层次。' },
];
const stems = (...items: string[]): Stem[] => items.map(item => {
  const [id, label] = item.split(':'); return { id, label: label || stemChineseLabel(id) };
});
const two = stems('Vocals:人声', 'Instrumental:伴奏');
type Curated = Omit<Partial<StudioModel>, 'id'> & { id: string; title: string; description: string; scenarios: string[] };
const curated: Curated[] = [
  { id: 'becruily_deux.ckpt', title: 'Deux 双轨', scenarios: ['duo'], description: '兼顾人声与伴奏的完整度，适合两条音轨都要保留的混音。', stems: two, source: 'https://huggingface.co/becruily/mel-band-roformer-deux', caution: '作者权重许可为 CC BY-NC 4.0；商用前需确认授权。' },
  { id: 'bs_leap_xe_voc.ckpt', title: 'Leap XE 人声', scenarios: ['duo'], description: '侧重减少伴奏串入，适合提取清晰、独立的人声。', stems: stems('vocals:人声', 'other:其余声音'), state: 'planned', tag: '2026 新收录', source: 'https://huggingface.co/pcunwa/BS-Roformer-Leap/tree/main/Xe' },
  { id: 'bs_roformer_voc_hyperacev2.ckpt', title: 'HyperACE v2 人声', scenarios: ['duo'], description: '兼顾人声厚度与串音抑制，适合保留演唱层次和细节。', stems: stems('vocals:人声', 'other:其余声音'), source: 'https://huggingface.co/pcunwa/BS-Roformer-HyperACE' },
  { id: 'bs_leap_xe_inst.ckpt', title: 'Leap XE 伴奏', scenarios: ['duo'], description: '侧重人声残留清理，适合制作较干净的翻唱伴奏。', state: 'planned', tag: '2026 新收录', stems: stems('instrumental:伴奏', 'other:其余声音'), source: 'https://huggingface.co/pcunwa/BS-Roformer-Leap/tree/main/Xe' },
  { id: 'bs_roformer_inst_hyperacev2.ckpt', title: 'HyperACE v2 伴奏', scenarios: ['duo'], description: '侧重保留乐器厚度与细节，适合复杂编曲的伴奏提取。', stems: stems('instrumental:伴奏', 'other:其余声音'), source: 'https://huggingface.co/pcunwa/BS-Roformer-HyperACE' },
  { id: 'BS-Roformer-Resurrection.ckpt', classic:true, tag:'经典精选', title: 'Resurrection 人声', scenarios: ['duo'], description: '适合保留人声的中低频质感，可用于细节与伪影的对照试听。', stems: stems('vocals:人声', 'other:其余声音'), source: 'https://huggingface.co/pcunwa/BS-Roformer-Resurrection', caution: '名称不表示具有音质修复能力；有损音源表现需实测。' },
  { id: 'BS-Roformer-Resurrection-Inst.ckpt', classic:true, tag:'经典精选', title: 'Resurrection 伴奏', scenarios: ['duo'], description: '适合钢琴与吉他等中低频较丰富的伴奏，可检查乐器质感。', stems: stems('vocals:人声', 'other:伴奏残差'), source: 'https://huggingface.co/pcunwa/BS-Roformer-Resurrection' },
  { id: 'bandit_v2_multi.ckpt', title: 'BandIt v2 多语种', scenarios: ['dme'], description: '面向多语种影视混音，独立输出对白、配乐与音效立体声轨。', tag:'2026 新收录', stems: stems('speech:对白','music:配乐','sfx:音效'), source:'https://zenodo.org/records/12701995' },
  { id: 'checkpoint-cmn_state_dict.ckpt', classic:true, tag:'经典精选', title: 'BandIt v2 中文', scenarios: ['dme'], description: '针对中文影视对白训练，适合中文配音前的对白与国际声拆分。', stems: stems('speech:对白', 'music:配乐', 'effects:音效'), source: 'https://github.com/kwatcharasupat/bandit-v2', caution: '保留现有中文权重；多语种版需确认可用权重和兼容配置。' },
  { id: 'model_bandit_plus_dnr_sdr_11.47.ckpt', classic:true, tag:'经典精选', title: 'BandIt Plus', scenarios: ['dme'], description: '适合常规影视混音三轨拆分，便于独立调整对白、配乐与环境音。', stems: stems('Speech:对白', 'Music:配乐', 'Effects:音效'), source: 'https://github.com/kwatcharasupat/bandit' },
  { id: 'DBS-TIGER-DnR', title: 'DBS-TIGER DnR', scenarios: ['dme'], description: '面向复杂重叠的对白、配乐与音效，适合单声道影视混音拆分。', state: 'planned', tag: '2026 新模型', stems: stems('speech:对白', 'music:配乐', 'sfx:音效'), source: 'https://huggingface.co/JusperLee/DBS-TIGER-DnR', caution: '原生 44.1 kHz 单声道，输出为单声道 WAV。' },
  { id: 'mel_band_roformer_karaoke_becruily.ckpt', classic:true, tag:'经典精选', title: 'Becruily 主唱 / 和声', scenarios: ['karaoke'], description: '侧重区分多层人声，适合主唱、叠唱与和声的精修。', stems: stems('Vocals:主唱目标', 'Instrumental:其余声音'), source: 'https://huggingface.co/becruily/mel-band-roformer-karaoke' },
  { id: 'bs_roformer_karaoke_anvuew.ckpt', classic:true, tag:'经典精选', title: 'Anvuew Karaoke', scenarios: ['karaoke'], description: '侧重提取叠录和声，适合制作可独立处理的伴唱轨。', stems: [], source: 'https://huggingface.co/anvuew/karaoke_bs_roformer' },
  { id: 'denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt', classic:true, tag:'经典精选', title: 'DeNoise 标准', scenarios: ['cleanup','denoise'], description: '在降低底噪时兼顾声音细节，适合对白与人声的日常精修。', stems: stems('dry:清理后声音', 'other:其余声音'), source: 'https://huggingface.co/jarredou/aufr33_MelBand_Denoise' },
  { id: 'denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt', classic:true, tag:'经典精选', title: 'DeNoise 强力', scenarios: ['cleanup','denoise'], description: '加强持续底噪与串音清理，适合噪声较重的人声素材。', stems: stems('dry:清理后声音', 'other:其余声音'), source: 'https://huggingface.co/jarredou/aufr33_MelBand_Denoise', caution: '高 SDR 不代表零底噪；强力处理可能损失细节。' },
  { id: 'mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt', classic:true, tag:'经典精选', title: 'Crowd 人群声', scenarios: ['cleanup','crowd'], description: '分离背景人群喧哗，适合外景与综艺对白的群杂声清理。', stems: stems('crowd:人群声', 'other:其余声音'), source: 'https://github.com/ZFTurbo/Music-Source-Separation-Training' },
  { id: 'dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt', classic:true, tag:'经典精选', title: 'Anvuew 去混响', scenarios: ['cleanup', 'dereverb'], description: '分离干声与混响尾音，适合对白抽干和重新匹配空间。', stems: [], source: 'https://huggingface.co/anvuew/dereverb_bs_roformer', caution: '输出声轨按模型实际配置显示。' },
  { id: 'aspiration_mel_band_roformer_sdr_18.9845.ckpt', classic:true, tag:'经典精选', title: 'Aspiration 气声', scenarios: ['cleanup', 'breath'], description: '独立提取呼吸气声，便于保留演唱细节并精确调整气口。', stems: stems('aspiration:呼吸气声', 'other:其余声音'), source: 'https://huggingface.co/Sucial/Aspiration_Mel_Band_Roformer', caution: '作者按歌曲气声训练；不保证去除喷麦、齿音或口水音。CC BY-NC-SA 4.0。' },
  { id: 'aspiration_mel_band_roformer_less_aggr_sdr_18.1201.ckpt', classic:true, tag:'经典精选', title: 'Aspiration 温和版', scenarios: ['breath'], description: '温和分离呼吸气声，适合希望保留更多人声细节的素材。', stems: stems('aspiration:呼吸气声', 'other:其余声音'), source: 'https://huggingface.co/Sucial/Aspiration_Mel_Band_Roformer' },
];
const legacy: Curated[] = [
  {id:'mel_band_roformer_vocals_becruily.ckpt',title:'Becruily 经典人声',scenarios:['duo'],description:'提取歌曲人声，适合与双轨模型比较演唱细节。'},
  {id:'mel_band_roformer_instrumental_becruily.ckpt',title:'Becruily 经典伴奏',scenarios:['duo'],description:'提取独立伴奏，适合检查乐器完整度与人声残留。'},
  {id:'melband_roformer_instvox_duality_v2.ckpt',title:'InstVox Duality v2',scenarios:['duo'],description:'同时分离人声与伴奏，适合两条音轨一起精修。'},
  {id:'kimmel_unwa_ft2_bleedless.ckpt',title:'Kim Mel FT2 Bleedless',scenarios:['duo','cleanup'],description:'侧重减少串音，适合进一步清理人声或伴奏残留。'},
  {id:'mel_band_roformer_instrumental_bleedless_v2_gabox.ckpt',title:'Gabox Bleedless v2 伴奏',scenarios:['duo','cleanup'],description:'侧重抑制伴奏中的人声串入，适合制作翻唱底轨。'},
  {id:'Kim_MelBandRoformer.ckpt',title:'Kim MelBand 人声',scenarios:['duo'],description:'经典人声提取方案，适合与新模型对照细节和伪影。'},
  {id:'bs_roformer_vocals_gabox.ckpt',title:'Gabox BS 人声',scenarios:['duo'],description:'提取独立演唱轨，适合比较人声质感与伴奏串音。'},
  {id:'model_bs_roformer_ep_368_sdr_12.9628.ckpt',title:'BS Roformer 12.97',scenarios:['duo'],description:'保留经典人声分离方案，适合同素材精修对照。'},
].map(model=>({...model,classic:true,tag:'经典精选',source:'https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md'}));
const instrumentModels:Curated[] = [
  {id:'HTDemucs4.th',title:'HTDemucs 四轨',scenarios:['stems','four'],description:'经典四轨分离，独立调整鼓、贝斯、人声与其他乐器。'},
  {id:'HTDemucs4_6stems.th',title:'HTDemucs 六轨',scenarios:['stems','six'],description:'在四轨之外独立提取吉他与钢琴，适合多轨精修。'},
  {id:'BS-Roformer-SW.ckpt',title:'BS Roformer SW 六轨',scenarios:['stems','six'],description:'同时输出六类声部，适合独立处理吉他与钢琴。'},
  {id:'mel_band_roformer_4stems_xl_ver1.ckpt',title:'MelBand XL 四轨',scenarios:['stems','four'],description:'分离鼓、贝斯、人声与其他乐器，适合细致混音。'},
  {id:'gilliaan_drumsV1.ckpt',title:'Gilliaan 鼓组',scenarios:['stems','drums'],description:'独立提取鼓组和其余声音，适合节奏层精修。'},
  {id:'becruily_guitar.ckpt',title:'Becruily 吉他',scenarios:['stems','guitar'],description:'针对吉他声部提取，适合独立处理吉他细节。'},
  {id:'gilliaan_bowedstrings_bs_v1.ckpt',title:'Gilliaan 弦乐',scenarios:['stems','strings'],description:'提取弓弦乐声部，适合独立调整弦乐层次。'},
  {id:'bs_mega_53stem_piano_mvsep.ckpt',title:'MVSEP 钢琴',scenarios:['stems','piano'],description:'针对钢琴声部提取，适合检查钢琴演奏细节。'},
  {id:'bs_mega_53stem_bass_mvsep.ckpt',title:'MVSEP 贝斯',scenarios:['stems','bass'],description:'针对贝斯声部提取，适合检查低频线条与演奏。'},
].map(model=>({...model,classic:true,tag:'经典模型',source:'https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md'}));
const speechModels:Curated[] = [
 {id:'speech_bs_roformer_AliceN_sdr_20.4440.ckpt',title:'AliceN BS 对白',classic:true,tag:'对白双轨',scenarios:['dme','cleanup'],description:'针对语音提取，分离对白与其余声音，适合影视对白精修。'},
 {id:'speech_mel_roformer_AliceN_sdr_16.5716.ckpt',title:'AliceN Mel 对白',classic:true,tag:'对白双轨',scenarios:['dme','cleanup'],description:'针对对白与背景声音拆分，适合同素材对照试听。'},
];
export const vocalModelIds=['bs_leap_xe_voc.ckpt','becruily_deux.ckpt','bs_roformer_voc_hyperacev2.ckpt','BS-Roformer-Resurrection.ckpt','mel_band_roformer_vocals_becruily.ckpt','kimmel_unwa_ft2_bleedless.ckpt','Kim_MelBandRoformer.ckpt','bs_roformer_vocals_gabox.ckpt','model_bs_roformer_ep_368_sdr_12.9628.ckpt','melband_roformer_instvox_duality_v2.ckpt'];
export const instrumentalModelIds=['becruily_deux.ckpt','bs_roformer_inst_hyperacev2.ckpt','bs_leap_xe_inst.ckpt','BS-Roformer-Resurrection-Inst.ckpt','mel_band_roformer_instrumental_becruily.ckpt','melband_roformer_instvox_duality_v2.ckpt','kimmel_unwa_ft2_bleedless.ckpt','mel_band_roformer_instrumental_bleedless_v2_gabox.ckpt'];
const cinemaDualIds=new Set([...vocalModelIds,...speechModels.map(m=>m.id)]);
function modelScenarios(id:string,base:string[]):string[]{
 const original=getAdvisory(id)?.scenarios || [];
 return [...new Set([...base,...((base.includes('duo') && original.includes('vocal'))||vocalModelIds.includes(id)?['vocal']:[]),...((base.includes('duo') && original.includes('instrumental'))||instrumentalModelIds.includes(id)?['instrumental']:[]),...(cinemaDualIds.has(id)?['dme']:[])])];
}
const curatedMap = new Map([...curated,...legacy,...instrumentModels,...speechModels].map(model => [model.id, model]));

export const instrumentScenarios = ['four','six','drums','bass','guitar','piano','strings'];

function fallbackScenarios(id: string): string[] {
  const a = getAdvisory(id);
  const categories = a?.scenarios ?? [];
  const target=(a?.targetStem || '').toLowerCase();
  const expanded=categories.flatMap(s=>{
    if(s==='four_stem')return ['stems','four'];
    if(s==='six_stem')return ['stems','six'];
    if(s==='drums')return ['stems','drums'];
    if(['mega_53','single_instrument','choir'].includes(s))return ['stems',...['guitar','piano','bass','strings'].filter(key=>target.includes(key))];
    if(s==='denoise')return ['cleanup',target.includes('crowd')?'crowd':'denoise'];
    if(['vocal','instrumental'].includes(s))return ['duo',s];
    if(['speech','restoration','spatial'].includes(s))return ['cleanup'];
    return [s];
  });
  return [...new Set(expanded)];
}
function declaredStems(target:string):Stem[] {
  return [...new Set(target.split(/[\/,|+]/).map(s=>s.trim()).filter(s=>s && !['unknown','none','null'].includes(s.toLowerCase())))].map(id=>({id,label:stemChineseLabel(id)}));
}
export function outputStems(model:StudioModel,purpose?:string):Stem[]{
 return purpose==='dme' && cinemaDualIds.has(model.id) ? model.stems.map(stem=>['other','instrument','instrumental'].includes(stem.id.toLowerCase())?{...stem,label:'其余声音'}:stem) : model.stems;
}
export function capabilityText(model:StudioModel,purpose?:string):string {
 const actual=outputStems(model,purpose);return actual.length ? actual.map(stem=>stem.label).join(' · ') : '接入后确认';
}
const baseModels: StudioModel[] = snapshot.data.map(item => {
  const c = curatedMap.get(item.id); const a = getAdvisory(item.id);
  return { id: item.id, classic:c?.classic || false, title: c?.title || item.id.replace(/\.(ckpt|pth|th)$/i, '').replace(/_/g, ' '),
    description: c?.description || (a?.note.usage?.split(/[。！？]/)[0] || '按模型目标提取对应音轨，适合专项分离与对照试听')+'。',
    originalDescription: a?.note.usage || originalDescriptions[item.id as keyof typeof originalDescriptions] || '',
    scenarios: modelScenarios(item.id,c?.scenarios || fallbackScenarios(item.id)), tag: c?.tag || (c ? '2026 精选' : ''),
    state: c?.state || (item.pymss.local.complete ? 'downloaded' : 'missing'),
    stems: c?.stems?.length ? c.stems : declaredStems(item.pymss.target_stem), source: c?.source || 'https://github.com/pymss-project/pymss',
    caution: c?.caution || '', size: item.pymss.size_bytes, curated: !!c };
});
const plannedModels: StudioModel[] = curated.filter(c => !baseModels.some(m => m.id === c.id)).map(c => ({
  id: c.id, title: c.title, description: c.description, originalDescription: originalDescriptions[c.id as keyof typeof originalDescriptions] || '', scenarios: modelScenarios(c.id,c.scenarios),
  tag: c.tag || '2026 新收录', state: 'planned', stems: c.stems || [], source: c.source || '',
  caution: c.caution || '', size: 0, curated: true,
}));
export const models = [...baseModels, ...plannedModels].sort((a,b) => {
  const ai = curated.findIndex(c => c.id === a.id), bi = curated.findIndex(c => c.id === b.id);
  return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi) || a.title.localeCompare(b.title);
});
export const statusLabel = (model: StudioModel) => ({ ready:'可使用', downloaded: '已下载', missing: '未安装', planned: '尚未接入' }[model.state]);
export function matchesModel(model: StudioModel, query: string, scenario = 'all', filter = 'all'): boolean {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return (scenario === 'all' || model.scenarios.includes(scenario)) &&
    (filter === 'all' || filter==='pinned' || (filter === 'curated' ? model.curated : filter==='downloaded' ? ['downloaded','ready'].includes(model.state) : filter === model.state)) &&
    words.every(word => [model.title, model.id, model.description, model.originalDescription || '', model.tag, model.source, ...model.scenarios.map(s=> scenarios.find(x=>x.id===s)?.label || s)].join(' ').toLowerCase().includes(word));
}
export function fileSize(bytes: number): string { return bytes ? bytes>=1024**3 ? `${(bytes/1024**3).toFixed(2)} GB` : `${(bytes/1024/1024).toFixed(0)} MB` : '大小待确认'; }

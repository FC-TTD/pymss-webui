import type { Stem } from './models';
export interface RuntimeModel {id:string;available:boolean;downloaded:boolean;stems:Stem[];size:number;reason?:string}
export interface TrackOutput {stem:string;label:string;url:string;waveform_url?:string;bytes?:number;frames?:number;sample_rate?:number;channels?:number}
export interface Job {id:string;model:string;filename:string;purpose?:string;status:string;error?:string;message?:string;stems?:string[];outputs:TrackOutput[];input_asset_id?:string;input_bytes?:number;input_duration?:number;input_url?:string}
export interface Batch {id:string;model:string;purpose:string;stems:string[];status:string;error?:string;jobs:Job[];completed:number;bytes:number}
export class StudioRequestError extends Error {constructor(message:string,public retryable=false){super(message);}}
async function request(url:string,init?:RequestInit) {
 let res:Response;
 try {res=await fetch(url,init);} catch {throw new StudioRequestError('连接暂时中断，已提交的任务和结果仍会保留。',true);}
 let raw:string;
 try {raw=await res.text();} catch {throw new StudioRequestError('连接暂时中断，已提交的任务和结果仍会保留。',true);}
 let data;
 try {data=JSON.parse(raw);} catch {throw new StudioRequestError('服务暂时无法响应，正在尝试恢复连接。',true);}
 if(!res.ok)throw new StudioRequestError(data.detail || data.error?.message || '请求失败，请稍后重试。',res.status>=500);
 return data;
}
export const externalModel=(id:string)=>id.startsWith('cv:') || id.startsWith('ym:');
const baseFor=(id:string)=>id.startsWith('ym-') || id.startsWith('ym:')?'/api/ym':id.startsWith('cv-') || id.startsWith('cv:')?'/api/speech':'/api/studio';
export async function getModels():Promise<RuntimeModel[]> {
 async function optional(url:string,ids:string[],name:string){const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),6000);try{return (await request(url,{cache:'no-store',signal:controller.signal})).models;}catch{return ids.map(id=>({id,available:false,downloaded:false,stems:[],size:0,reason:name+'服务暂不可用'}));}finally{clearTimeout(timeout);}}
 const [primary,speech,ying]=await Promise.all([request('/api/studio/models',{cache:'no-store'}),optional('/api/speech/models',['MossFormer2_SS_16K','MossFormer2_SR_48K','MossFormer2_SE_48K','FRCRN_SE_16K','MossFormerGAN_SE_16K'].map(n=>'cv:'+n),'ClearVoice'),optional('/api/ym/models',['ym:yingmusic_bs_roformer'],'YingMusic')]);
 return [...primary.models,...speech,...ying];
}
export interface InputOrigin {job_id:string;model:string;stem:string;label:string;filename:string}
export interface DerivedInput {pool_batch:string;asset_id:string;filename:string;bytes:number;duration:number;input_url:string;parent:InputOrigin;sha256:string}
export async function deriveInput(job_id:string,stem:string):Promise<DerivedInput>{return request('/api/chain/inputs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_id,stem})});}
export async function inputOrigin(asset:string):Promise<DerivedInput|null>{try{return await request('/api/chain/assets/'+encodeURIComponent(asset),{cache:'no-store'});}catch{return null;}}
export async function submitJob(file:File,model:string,stems:string[],purpose='duo'):Promise<string> {const query=new URLSearchParams({model,filename:file.name,stems:JSON.stringify(stems),purpose});return (await request(`/api/studio/jobs?${query}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file})).id;}
export async function readJob(id:string):Promise<Job> {return request(`${baseFor(id)}/jobs/${encodeURIComponent(id)}`,{cache:'no-store'});}
export async function createBatch(model:string,stems:string[],purpose:string):Promise<Batch> {return request(`${baseFor(model)}/batches?${new URLSearchParams({model,stems:JSON.stringify(stems),purpose})}`,{method:'POST'});}
export async function uploadBatch(id:string,file:File):Promise<Batch> {return request(`${baseFor(id)}/batches/${id}/inputs?${new URLSearchParams({filename:file.name})}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});}
export async function reuseBatch(id:string,asset:string):Promise<Batch> {return request(`${baseFor(id)}/batches/${id}/reuse?${new URLSearchParams({asset_id:asset})}`,{method:'POST'});}
export async function startBatch(id:string):Promise<Batch> {return request(`${baseFor(id)}/batches/${id}/start`,{method:'POST'});}
export async function readBatch(id:string):Promise<Batch> {return request(`${baseFor(id)}/batches/${id}`,{cache:'no-store'});}
export async function exportTracks(tracks:{job_id:string;stem:string}[]):Promise<{url:string;filename:string;bytes:number}> {const base=baseFor(tracks[0]?.job_id || '');if(tracks.some(t=>baseFor(t.job_id)!==base))throw new StudioRequestError('请分别导出不同处理批次的音轨。');return request(base+'/exports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tracks})});}

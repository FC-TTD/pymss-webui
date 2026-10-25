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
export async function getModels():Promise<RuntimeModel[]> {return (await request('/api/studio/models',{cache:'no-store'})).models;}
export async function submitJob(file:File,model:string,stems:string[],purpose='duo'):Promise<string> {const query=new URLSearchParams({model,filename:file.name,stems:JSON.stringify(stems),purpose});return (await request(`/api/studio/jobs?${query}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file})).id;}
export async function readJob(id:string):Promise<Job> {return request(`/api/studio/jobs/${encodeURIComponent(id)}`,{cache:'no-store'});}
export async function createBatch(model:string,stems:string[],purpose:string):Promise<Batch> {return request(`/api/studio/batches?${new URLSearchParams({model,stems:JSON.stringify(stems),purpose})}`,{method:'POST'});}
export async function uploadBatch(id:string,file:File):Promise<Batch> {return request(`/api/studio/batches/${id}/inputs?${new URLSearchParams({filename:file.name})}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});}
export async function reuseBatch(id:string,asset:string):Promise<Batch> {return request(`/api/studio/batches/${id}/reuse?${new URLSearchParams({asset_id:asset})}`,{method:'POST'});}
export async function startBatch(id:string):Promise<Batch> {return request(`/api/studio/batches/${id}/start`,{method:'POST'});}
export async function readBatch(id:string):Promise<Batch> {return request(`/api/studio/batches/${id}`,{cache:'no-store'});}
export async function exportTracks(tracks:{job_id:string;stem:string}[]):Promise<{url:string;filename:string;bytes:number}> {return request('/api/studio/exports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tracks})});}

import { matchesModel, scenarios, type StudioModel } from './models';
import { compareQuality } from './quality';

type LibraryModel = StudioModel & {available:boolean};
// Overlapping abilities remain searchable; each card has one place in the expanded library.
function groupId(model:StudioModel):string {
  if(model.scenarios.includes('breath'))return 'breath';
  if(model.scenarios.includes('dereverb'))return 'dereverb';
  for(const specific of ['four','six','drums','bass','guitar','piano','strings','denoise','crowd'])if(model.scenarios.includes(specific))return specific;
  if(model.scenarios[0]==='duo'){const vocal=model.scenarios.includes('vocal'),instrumental=model.scenarios.includes('instrumental');if(vocal && !instrumental)return 'vocal';if(instrumental && !vocal)return 'instrumental';}
  return scenarios.find(group=>model.scenarios.includes(group.id))?.id || 'other';
}
export function groupLibraryModels<T extends LibraryModel>(models:T[],query:string,filter:string,pins:string[]) {
  const visible=models.filter(model=>matchesModel(model,query,'all',filter) && (filter!=='pinned' || pins.includes(model.id)));
  return [...scenarios,{id:'other',label:'其他模型'}].map(group=>({
    id:group.id,label:group.label,
    models:visible.filter(model=>groupId(model)===group.id).sort((a,b)=>Number(b.available)-Number(a.available) || compareQuality(a,b,group.id,pins)),
  })).filter(group=>group.models.length);
}

import type { StudioModel } from './models';

// Selection must never change positions or evict a previously revealed card.
export function baseModelCards<T extends StudioModel>(ordered:T[],purpose?:string):T[] {
  if(purpose==='dme'){const ids=new Set([...ordered.filter(m=>m.stems.length===2).slice(0,3),...ordered.filter(m=>m.stems.length>=3).slice(0,3)].map(m=>m.id));return ordered.filter(m=>ids.has(m.id));}
  const ids=new Set([...ordered.filter(m=>!m.classic).slice(0,2),...ordered.filter(m=>m.classic).slice(0,3)].map(m=>m.id));
  return ordered.filter(m=>ids.has(m.id));
}
export function stableModelCards<T extends StudioModel>(ordered:T[],revealed:string[],purpose?:string):T[] {
  const base=baseModelCards(ordered,purpose);const ids=new Set(base.map(m=>m.id));
  const result=[...base];for(const id of revealed){const model=ordered.find(m=>m.id===id);if(model && !ids.has(id)){result.push(model);ids.add(id);}}return result;
}

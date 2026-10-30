export function timeLabel(seconds:number):string { const s=Math.max(0,Math.floor(seconds));return `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`; }
export function saveBlob(blob:Blob,name:string) {const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}

export function downloadURL(url:string,name:string) {const a=document.createElement("a");a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();}

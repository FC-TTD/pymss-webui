<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { Workflow, Library, Settings, CloudUpload, Music2, X, Search, CheckCircle2, Info, AudioLines, ChevronDown, Download, Loader2, ArrowLeft, Sun, Moon, CircleAlert, RotateCcw, Headphones, Pin, PinOff } from '@lucide/svelte';
  import { Button } from '../components/ui/button';
  import { Checkbox } from '../components/ui/checkbox';
  import { Input } from '../components/ui/input';
  import { models, scenarios, instrumentScenarios, speechDetailScenarios, matchesModel, fileSize, capabilityText, modelDescription, outputStems, type StudioModel } from './models';
  import { timeLabel, downloadURL } from './audio-utils';
  import { compareQuality, qualityReferences } from './quality';
  import { groupLibraryModels } from './library';
  import {baseModelCards,stableModelCards} from './presentation';
  import WaveformTrack from './WaveformTrack.svelte';
  import { getModels, submitJob, readJob, type RuntimeModel, type TrackOutput, type Batch, type Job, createBatch, uploadBatch, reuseBatch, startBatch, readBatch, exportTracks, StudioRequestError, externalModel, deriveInput, inputOrigin, type InputOrigin } from './studio-api';
  import './studio.css';

  let view = $state<'workbench'|'library'|'settings'>('workbench');
  let scenario = $state('duo');
  let selectedId = $state('melband_roformer_instvox_duality_v2.ckpt');
  let query = $state('');
  let filter = $state('all');
  let showFilenames = $state(false);
  let theme = $state<'light'|'dark'>('light');
  let inputEl = $state<HTMLInputElement>();
  type InputAudio={id:string;file:File|null;name:string;size:number;url:string;duration:number;assetId?:string;parent?:InputOrigin};
  let inputs=$state<InputAudio[]>([]);let selectedInput=$state('');let readingFiles=$state(false);
  const activeInput=$derived(inputs.find(f=>f.id===selectedInput) || inputs[0]);
  const file=$derived(activeInput?.file || null);const fileUrl=$derived(activeInput?.url || '');const duration=$derived(activeInput?.duration || 0);
  let batch=$state<Batch|null>(null);let exportSelection=$state<string[]>([]);let exporting=$state(false);let exportFormat=$state('zip');let exportMessage=$state('');
  let deriving=$state('');let chainNotice=$state('');
  let expandedResults=$state<string[]>([]);const seenExports=new Set<string>();
  let preparedExport=$state<{url:string;filename:string;bytes:number}|null>(null);

  let runtime = $state<RuntimeModel[]>([]);
  let connected = $state(false);
  let pinned = $state<string[]>([]);
  let pickQuery = $state('');
  let showPicker = $state(false);
  let showInstruments=$state(false);let showSpeechDetails=$state(false);let revealedModelIds=$state<string[]>([]);
  let pickerUp=$state(false);let pickerMaxHeight=$state(420);
  let currentJob = $state('');
  let connectionLost = $state(false);
  let restored = $state(false);
  let dragging = $state(false);
  let selectedStems = $state<string[]>(['Vocals','Instrumental']);
  let message = $state('');
  let progress = $state('');
  let busy = $state(false);

  let fileSequence=0, runSequence=0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let result = $state<{model: string; fileName: string; created: string; outputs: TrackOutput[]} | null>(null);
  let resultSection = $state<HTMLElement>();
  const resultJobs=$derived(batch?.jobs.some(j=>j.status==='succeeded') ? batch.jobs.filter(j=>j.status==='succeeded') : result ? [{id:currentJob,model:result.model,filename:result.fileName,outputs:result.outputs,status:'succeeded'}] : []);
  const exportEntries=$derived(resultJobs.flatMap(job=>job.outputs.map(output=>({key:job.id+'|'+output.stem,job_id:job.id,filename:job.filename,output}))));
  const selectedExports=$derived(exportEntries.filter(e=>exportSelection.includes(e.key)));
  const catalog = $derived(models.map(m=>{const r=runtime.find(r=>r.id===m.id);return {...m,available:!!r?.available,state:r?.available?'ready' as const:r?.downloaded?'downloaded' as const:'missing' as const,stems:r?.stems?.length?r.stems:m.stems,reason:r?.reason || (r?'':'未接入'),size:r?.size || m.size};}));
  const selected = $derived(catalog.find(m=>m.id===selectedId)!);
  const currentScenario = $derived(scenarios.find(s=>s.id===scenario)!);
  const speechProcessing=$derived(['denoise','superres','speakers'].includes(scenario));
  const actionLabel=$derived(scenario==='denoise'?'开始降噪':scenario==='superres'?'开始提升音质':'开始分离');
  const orderedModels = $derived(catalog.filter(m=>!m.hidden && m.available && m.scenarios.includes(scenario)).sort((a,b)=>compareQuality(a,b,scenario,pinned)));
  const featuredModels = $derived(stableModelCards(orderedModels,revealedModelIds,scenario));
  const selectedMatchesScenario = $derived(!selected.hidden && selected.available && selected.scenarios.includes(scenario));
  const pickerModels = $derived(orderedModels.filter(m=>!featuredModels.some(f=>f.id===m.id) && matchesModel(m,pickQuery)));
  const libraryGroups = $derived(groupLibraryModels(catalog,query,filter,pinned));
  const visibleModelCount = $derived(libraryGroups.reduce((total,group)=>total+group.models.length,0));
  const currentStep = $derived(resultJobs.length ? 3 : inputs.length ? 2 : 1);

  onMount(() => {
    try { const data=JSON.parse(localStorage.getItem('pymss-pinned-models') || '[]'); if(Array.isArray(data)) pinned=data.filter(id=>typeof id==='string' && models.some(m=>m.id===id)); } catch {}
    void initialise();
  });
  async function initialise() {
    await refreshModels();
    // The shared entry starts empty. Only an explicit current-task URL resumes work.
    try{localStorage.removeItem('pymss-last-batch');localStorage.removeItem('pymss-last-job');}catch{}
    const params=new URLSearchParams(location.search);const batchId=params.get('batch') || '';
    if(/^(cv-|ym-)?[a-f0-9]{32}$/.test(batchId)){busy=true;progress='正在恢复批次…';void monitorBatch(batchId,++runSequence,true);return;}
    const id=params.get('job') || '';
    if(/^(cv-|ym-)?[a-f0-9]{32}$/.test(id)) { currentJob=id;restored=true;busy=true;progress='正在恢复上次任务…';void monitorJob(id,++runSequence); }
  }
  async function refreshModels() {
    try {
      runtime=await getModels();connected=true;
      const next=models.filter(m=>runtime.some(r=>r.id===m.id && r.available) && m.scenarios.includes(scenario)).sort((a,b)=>compareQuality(a,b,scenario,pinned))[0];
      if(!runtime.find(m=>m.id===selectedId)?.available && next)selectedId=next.id;
      const actual=runtime.find(m=>m.id===selectedId);if(actual?.stems.length)selectedStems=actual.stems.map(s=>s.id);
    } catch {connected=false;message='暂时无法连接服务，可稍后重新连接。';}
  }
  function togglePin(id:string) { pinned=pinned.includes(id)?pinned.filter(p=>p!==id):[...pinned,id]; try { localStorage.setItem('pymss-pinned-models',JSON.stringify(pinned)); } catch {message='浏览器未允许保存置顶偏好。';} }

  onDestroy(() => { fileSequence++; runSequence++; clearTimeout(timer); for(const input of inputs)URL.revokeObjectURL(input.url); releaseResult(); });

  function releaseResult() { result=null; }
  function clearResult() {releaseResult();batch=null;currentJob='';progress='';restored=false;exportSelection=[];seenExports.clear();exportMessage='';preparedExport=null;try{localStorage.removeItem('pymss-last-job');localStorage.removeItem('pymss-last-batch');}catch{} const url=new URL(location.href);url.searchParams.delete('job');url.searchParams.delete('batch');history.replaceState(null,'',url);} 
  function persistJob(id:string) {const url=new URL(location.href);url.searchParams.delete('batch');url.searchParams.set('job',id);history.replaceState(null,'',url);}
  async function monitorJob(id:string,seq:number,failures=0) {
    if(seq!==runSequence)return;
    try {
      const job=decorateJob(await readJob(id));if(seq!==runSequence)return;if(!connected)void refreshModels();
      connectionLost=false;message='';
      if(restored){restoreInputs([job]);const model=catalog.find(m=>m.id===job.model);if(model){selectedId=model.id;scenario=job.purpose && model.scenarios.includes(job.purpose)?job.purpose:model.scenarios.includes(scenario)?scenario:model.scenarios[0];revealModel(model.id);selectedStems=job.stems || model.stems.map(s=>s.id);}}
      if(job.status==='failed'){busy=false;progress='';message=job.error || '分离未完成，请重试。';return;}
      if(job.status!=='succeeded'){progress=job.message || '正在分离音轨…';timer=setTimeout(()=>void monitorJob(id,seq),1500);return;}
      // Stream the immutable result URL; never fetch complete tracks into parallel browser Blobs.
      result={model:job.model,fileName:job.filename,created:restored?'已恢复':new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'}),outputs:job.outputs};
      persistJob(id);selectNewExports();busy=false;progress='分离完成';await tick();resultSection?.scrollIntoView({behavior:'smooth',block:'nearest'});
    } catch(e) {
      if(seq!==runSequence)return;
      if(e instanceof StudioRequestError && e.retryable){connectionLost=true;progress='连接暂时中断，正在恢复任务…';timer=setTimeout(()=>void monitorJob(id,seq,failures+1),Math.min(1500*2**failures,10000));return;}
      busy=false;progress='';message=e instanceof Error?e.message:'无法读取任务，请重试连接。';
    }
  }
  function reconnect() {if(batch){busy=true;void monitorBatch(batch.id,++runSequence);return;}if(!currentJob){void refreshModels();return;}clearTimeout(timer);busy=true;message='';progress='正在重新连接任务…';void monitorJob(currentJob,++runSequence);}
  function cardKey(e:KeyboardEvent) {
    if(!['ArrowDown','ArrowUp','ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
    e.preventDefault();const root=(e.currentTarget as HTMLElement).closest('.featured-models');const nodes=Array.from(root?.querySelectorAll<HTMLButtonElement>('[role="radio"]:not(:disabled)') || []);const at=nodes.indexOf(e.currentTarget as HTMLButtonElement);
    const index=e.key==='Home'?0:e.key==='End'?nodes.length-1:['ArrowDown','ArrowRight'].includes(e.key)?(at+1)%nodes.length:(at-1+nodes.length)%nodes.length;nodes[index]?.click();nodes[index]?.focus();
  }
  function setModel(model: StudioModel,allowBusy=false) {
    if((busy && !allowBusy) || !runtime.find(m=>m.id===model.id)?.available) return;
    const viewportY=window.scrollY;revealModel(model.id);selectedId=model.id; selectedStems=model.stems.map(s=>s.id); message='';
    showPicker=false; pickQuery='';void tick().then(()=>window.scrollTo({top:viewportY,behavior:'instant'}));
  }
  function revealModel(id:string){if(!baseModelCards(orderedModels,scenario).some(m=>m.id===id) && !revealedModelIds.includes(id))revealedModelIds=[...revealedModelIds,id];}
  function setScenario(id: string) {
    if(busy) return;
    if(scenario!==id)revealedModelIds=[];scenario=id;showInstruments=false;showSpeechDetails=false;showPicker=false;
    const next=catalog.filter(m=>!m.hidden && m.available && m.scenarios.includes(id)).sort((a,b)=>compareQuality(a,b,id,pinned))[0];
    if(next) setModel(next);
  }
  async function openLibrary() { view='library'; query=''; filter='all';await tick();window.scrollTo({top:0,behavior:'auto'}); }
  function togglePicker(event:MouseEvent){
    if(!showPicker){const r=(event.currentTarget as HTMLElement).getBoundingClientRect();const below=innerHeight-r.bottom-12,above=r.top-12;pickerUp=below<300 && above>below;pickerMaxHeight=Math.max(110,Math.min(600,(pickerUp?above:below)-86));}
    showPicker=!showPicker;
  }
  function toggleInstruments(){const open=!showInstruments;if(open && scenario!=='stems' && !instrumentScenarios.includes(scenario))setScenario('stems');showInstruments=open;}

  async function chooseLibrary(model:StudioModel,groupId:string) {
    if(!runtime.some(item=>item.id===model.id && item.available))return;
    const targetScenario=model.scenarios.includes(groupId)?groupId:model.scenarios.includes(scenario)?scenario:model.scenarios[0];
    if(targetScenario && scenarios.some(s=>s.id===targetScenario)){if(scenario!==targetScenario)revealedModelIds=[];scenario=targetScenario;}
    restored=false;setModel(model,true);view='workbench';
    await tick();window.scrollTo({top:0,behavior:'auto'});
  }
  function removeInput(id:string){const input=inputs.find(f=>f.id===id);if(input)URL.revokeObjectURL(input.url);inputs=inputs.filter(f=>f.id!==id);if(selectedInput===id)selectedInput=inputs[0]?.id || '';}
  function resetFile(){fileSequence++;for(const input of inputs)URL.revokeObjectURL(input.url);inputs=[];selectedInput='';if(inputEl)inputEl.value='';}
  async function acceptFiles(files:FileList|File[]|undefined){
    if(!files || busy || readingFiles)return;
    const next=Array.from(files);if(!next.length)return;
    if(inputs.length+next.length>20){message='每批最多20个文件，请减少选择。';return;}
    if(inputs.reduce((n,i)=>n+i.size,0)+next.reduce((n,f)=>n+f.size,0)>2*1024**3){message='每批文件合计不能超过2 GB。';return;}
    const seq=++fileSequence;readingFiles=true;const errors:string[]=[];
    try{for(const candidate of next){
      if(seq!==fileSequence)break;
      if(inputs.some(i=>i.name===candidate.name && i.size===candidate.size && i.file?.lastModified===candidate.lastModified))continue;
      if(!/\.(wav|flac|mp3|m4a|ogg|aac)$/i.test(candidate.name) || candidate.size>512*1024**2){errors.push(candidate.name+'：格式不支持或超过512 MB');continue;}
      const url=URL.createObjectURL(candidate);const media=new Audio();media.preload='metadata';
      const length=await new Promise<number>(resolve=>{let settled=false;const finish=(duration:number)=>{if(settled)return;settled=true;clearTimeout(timeout);media.removeAttribute('src');media.load();resolve(duration);};const timeout=setTimeout(()=>finish(0),12000);media.onloadedmetadata=()=>finish(media.duration);media.onerror=()=>finish(0);media.src=url;});
      if(seq!==fileSequence || !Number.isFinite(length) || length<=0 || length>600){URL.revokeObjectURL(url);if(seq===fileSequence)errors.push(candidate.name+'：无法读取或超过10分钟');continue;}
      const id=crypto.randomUUID?.() || String(Date.now())+'-'+Math.random();inputs=[...inputs,{id,file:candidate,name:candidate.name,size:candidate.size,url,duration:length}];if(!selectedInput)selectedInput=id;
    }}finally{readingFiles=false;if(inputEl)inputEl.value='';message=errors.join('；');}
  }
  function restoreInputs(jobs:Job[]){
    if(inputs.length)return;
    const seen=new Set<string>();const restoredInputs:InputAudio[]=[];
    for(const job of jobs){if(!job.input_asset_id || !job.input_url || seen.has(job.input_asset_id))continue;seen.add(job.input_asset_id);restoredInputs.push({id:job.input_asset_id,file:null,name:job.filename,size:job.input_bytes || 0,duration:job.input_duration || 0,url:job.input_url,assetId:job.input_asset_id});}
    inputs=restoredInputs;selectedInput=inputs[0]?.id || '';
    for(const input of restoredInputs)void inputOrigin(input.assetId!).then(origin=>{if(origin)inputs=inputs.map(i=>i.id===input.id?{...i,parent:origin.parent}:i);});
  }
  function persistBatch(id:string){const url=new URL(location.href);url.searchParams.delete('job');url.searchParams.set('batch',id);history.replaceState(null,'',url);}
  function selectNewExports(){for(const entry of exportEntries)if(!seenExports.has(entry.key)){seenExports.add(entry.key);exportSelection=[...exportSelection,entry.key];}if(!expandedResults.some(id=>resultJobs.some(j=>j.id===id)) && resultJobs.length)expandedResults=[resultJobs[0].id];}
  function toggleExport(key:string,checked:boolean){exportSelection=checked?[...new Set([...exportSelection,key])]:exportSelection.filter(k=>k!==key);}
  function decorateJob(job:Job,purpose=job.purpose):Job{const model=catalog.find(m=>m.id===job.model);if(!model || purpose!=='dme')return job;const stems=outputStems(model,purpose);return {...job,outputs:job.outputs.map(o=>({...o,label:stems.find(s=>s.id.toLowerCase()===o.stem.toLowerCase())?.label || o.label}))};}
  async function monitorBatch(id:string,seq:number,restore=false,failures=0){
    if(seq!==runSequence)return;
    try{const state=await readBatch(id);if(seq!==runSequence)return;state.jobs=state.jobs.map(j=>decorateJob(j,state.purpose));batch=state;persistBatch(id);connectionLost=false;
      if(restore){restoreInputs(state.jobs);const model=catalog.find(m=>m.id===state.model);if(model){scenario=model.scenarios.includes(state.purpose)?state.purpose:model.scenarios[0];selectedId=model.id;selectedStems=state.stems;revealModel(model.id);}}
      selectNewExports();busy=state.status==='running';
      const running=state.jobs.find(j=>['running','queued','waiting'].includes(j.status));progress=busy?`已完成 ${state.completed}/${state.jobs.length} · ${running?.filename || '准备处理'}${running?.message?' · '+running.message:''}`:state.status==='preparing'?'上传已保留，可开始已上传文件':state.status==='succeeded'?(externalModel(state.model)?'全部处理完成':'全部分离完成'):state.error || '部分文件未完成';
      if(busy)timer=setTimeout(()=>void monitorBatch(id,seq,false),1500);else{message='';await tick();if(!restore)resultSection?.scrollIntoView({behavior:'smooth',block:'nearest'});}
    }catch(e){if(seq!==runSequence)return;if(e instanceof StudioRequestError && e.retryable){connectionLost=true;progress='连接暂时中断，正在恢复批次…';timer=setTimeout(()=>void monitorBatch(id,seq,restore,failures+1),Math.min(1500*2**failures,10000));return;}busy=false;message=e instanceof Error?e.message:'无法读取批次。';}
  }
  async function continueBatch(){if(!batch || busy)return;busy=true;message='';try{batch=await startBatch(batch.id);void monitorBatch(batch.id,++runSequence);}catch(e){busy=false;message=e instanceof Error?e.message:'无法开始批次。';}}
  async function downloadSelected(){
    if(!selectedExports.length || exporting)return;exporting=true;exportMessage='';
    try{if(exportFormat==='zip'){preparedExport=await exportTracks(selectedExports.map(e=>({job_id:e.job_id,stem:e.output.stem})));exportMessage=`已打包 ${selectedExports.length} 条音轨，点击“下载 ZIP”保存。`;}
      else{for(const entry of selectedExports){downloadURL(entry.output.url+'?download=true',entry.filename.replace(/\.[^.]+$/,'')+'-'+entry.output.label+'.wav');await new Promise(r=>setTimeout(r,350));}exportMessage='已请求逐个下载，请查看浏览器下载列表。';}
    }catch(e){exportMessage=e instanceof Error?e.message:'导出未完成，请重试。';}finally{exporting=false;}
  }
  async function continueTrack(jobId:string,output:TrackOutput,purpose:string){
    if(busy || deriving)return;deriving=jobId+'|'+output.stem;chainNotice='正在准备服务器音轨，无需下载或重新上传…';message='';
    try{const derived=await deriveInput(jobId,output.stem);resetFile();inputs=[{id:derived.asset_id,file:null,name:derived.filename,size:derived.bytes,duration:derived.duration,url:derived.input_url,assetId:derived.asset_id,parent:derived.parent}];selectedInput=derived.asset_id;persistBatch(derived.pool_batch);
      setScenario(purpose==='choose'?scenario:purpose);
      if(purpose==='dme'){const target=orderedModels.find(m=>m.stems.length>=3);if(target){setModel(target);selectedStems=target.stems.filter(s=>['music','sfx','effects'].includes(s.id.toLowerCase())).map(s=>s.id);if(!selectedStems.length)selectedStems=target.stems.map(s=>s.id);}}
      if(selectedMatchesScenario){let prepared=await createBatch(selected.id,[...selectedStems],scenario);prepared=await reuseBatch(prepared.id,derived.asset_id);batch=prepared;persistBatch(prepared.id);expandedResults=[];}
      restored=false;progress='';chainNotice='已将“'+output.label+'”作为下一轮输入，选择模型后点击开始；上一轮结果已保留。';await tick();window.scrollTo({top:0,behavior:'smooth'});
    }catch(e){chainNotice=e instanceof Error?e.message:'音轨暂时无法继续处理，原结果已保留。';}finally{deriving='';}
  }
  function soloPlayback(event:Event) {for(const audio of document.querySelectorAll<HTMLAudioElement>('.studio audio'))if(audio!==event.currentTarget)audio.pause();}
  function toggleStem(id:string, checked:boolean) {
    selectedStems=checked ? [...new Set([...selectedStems,id])] : selectedStems.filter(s=>s!==id);
  }
  async function start(){
    message='';if(deriving)return;if(!inputs.length){message='请先选择音频。';return;}if(!selectedMatchesScenario){message='请先选择可用模型。';return;}if(!selectedStems.length){message='请至少选择一条输出音轨。';return;}
    const snapshot=[...inputs];const seq=++runSequence;busy=true;restored=false;connectionLost=false;exportMessage='';preparedExport=null;
    try{
      if(batch?.status==='preparing' && batch.model===selected.id && batch.purpose===scenario && JSON.stringify(batch.stems)===JSON.stringify(selectedStems) && batch.jobs.length===snapshot.length && snapshot.every(input=>input.assetId && batch!.jobs.some(j=>j.input_asset_id===input.assetId))){batch=await startBatch(batch.id);void monitorBatch(batch.id,seq);return;}
      // First-time external-provider inputs join the immutable source pool.
      // Bind the asset immediately, so a provider failure never loses an upload.
      if(externalModel(selected.id) && snapshot.some(input=>!input.assetId)){
        const pool=await createBatch('melband_roformer_instvox_duality_v2.ckpt',['Vocals','Instrumental'],'duo');batch=pool;persistBatch(pool.id);
        for(let i=0;i<snapshot.length;i++){
          const input=snapshot[i];if(input.assetId)continue;if(!input.file)throw new Error('原始音频不可用，请重新选择文件。');
          progress=`正在导入 ${i+1}/${snapshot.length} · ${input.name}`;
          const uploaded=await uploadBatch(pool.id,input.file);batch=uploaded;const asset=uploaded.jobs[uploaded.jobs.length-1]?.input_asset_id;
          if(!asset)throw new Error('导入未完成，请稍后重试。');input.assetId=asset;inputs=inputs.map(item=>item.id===input.id?{...item,assetId:asset}:item);
        }
      }
      batch=await createBatch(selected.id,[...selectedStems],scenario);persistBatch(batch.id);expandedResults=[];
      for(let i=0;i<snapshot.length;i++){
        const input=snapshot[i];progress=`${input.assetId?'复用已上传音频':'正在上传'} ${i+1}/${snapshot.length} · ${input.name}`;
        if(input.assetId)batch=await reuseBatch(batch.id,input.assetId);
        else if(input.file){batch=await uploadBatch(batch.id,input.file);const asset=batch.jobs[batch.jobs.length-1]?.input_asset_id;if(asset)inputs=inputs.map(item=>item.id===input.id?{...item,assetId:asset}:item);}
        else throw new Error('已上传音频不可用，请重新选择文件。');
      }
      batch=await startBatch(batch.id);progress='正在处理音频…';void monitorBatch(batch.id,seq);
    }catch(e){busy=false;progress='';message=e instanceof Error?e.message:'上传失败，请重试。';if(batch)message+=' 已上传文件已保留，可开始处理。';}
  }

</script>

<svelte:window onclick={(e)=>{if(showPicker && (!(e.target instanceof Element) || !e.target.closest('.model-picker')))showPicker=false;if(showInstruments && (!(e.target instanceof Element) || !e.target.closest('.instrument-parent')))showInstruments=false;if(showSpeechDetails && (!(e.target instanceof Element) || !e.target.closest('.speech-parent')))showSpeechDetails=false;}} onkeydown={(e)=>{if(e.key==='Escape'){showPicker=false;showInstruments=false;showSpeechDetails=false;}}}/>
<svelte:head><meta name="description" content="PYMSS 音轨分离工作台。" /></svelte:head>

<div class="studio" data-theme={theme} aria-busy={busy}>
  <aside class="studio-sidebar">
    <a class="studio-brand" href="#workbench" onclick={(e)=>{e.preventDefault();view='workbench';}}>PYMSS Studio</a>
    <nav aria-label="主导航">
      <button class:active={view==='workbench'} aria-current={view==='workbench'?'page':undefined} onclick={()=>view='workbench'}><Workflow size={19}/> <span>分离工作台</span></button>
      <button class:active={view==='library'} aria-current={view==='library'?'page':undefined} onclick={openLibrary}><Library size={19}/> <span>模型库</span></button>
      <button class:active={view==='settings'} aria-current={view==='settings'?'page':undefined} onclick={()=>view='settings'}><Settings size={19}/> <span>设置</span></button>
    </nav>
    <div class="sidebar-foot"><Headphones size={18}/><span><small>{connected?'模型服务已连接':'正在连接模型服务'}</small></span></div>
  </aside>
  <main class="studio-main">
    <header class="studio-header">
      <div><h1>{view==='workbench'?(speechProcessing?currentScenario.label:'音轨分离'):view==='library'?'模型库':'工作台设置'}</h1><p>{view==='workbench'?(speechProcessing?'选择模型，处理对白与人声并试听结果。':'从一段混音，获得可用的独立音轨。'):view==='library'?'按用途选择，了解每个模型的适用范围。':'调整显示偏好，随时回到分离工作台。'}</p></div>
    </header>

    {#if view==='workbench'}
      <ol class="studio-steps" aria-label="分离步骤">
        {#each ['选择用途','导入音频','处理与试听'] as label,i}<li class:done={currentStep>i+1} class:current={currentStep===i+1}><span>{i+1}</span>{label}</li>{/each}
      </ol>
      <div class="studio-taskbar" aria-label="分离用途">
        {#each scenarios.filter(s=>!instrumentScenarios.includes(s.id) && !speechDetailScenarios.includes(s.id)) as item}
          {#if item.id==='stems'}<div class="instrument-parent"><button aria-label="乐器分轨" aria-haspopup="menu" aria-expanded={showInstruments} aria-controls="instrument-types-menu" class:active={scenario==='stems'||instrumentScenarios.includes(scenario)} disabled={busy} onclick={toggleInstruments}>乐器分轨<ChevronDown size={15}/></button>
            {#if showInstruments}<div id="instrument-types-menu" class="instrument-menu" role="menu" aria-label="乐器类型"><button role="menuitemradio" aria-checked={scenario==='stems'} onclick={()=>setScenario('stems')}>全部乐器模型</button>{#each scenarios.filter(s=>instrumentScenarios.includes(s.id)) as child}<button role="menuitemradio" aria-checked={scenario===child.id} onclick={()=>setScenario(child.id)}>{child.label}</button>{/each}</div>{/if}
          </div>{:else}<button aria-pressed={scenario===item.id} class:active={scenario===item.id} disabled={busy} onclick={()=>setScenario(item.id)}>{item.label}</button>{/if}
        {/each}
      <div class="speech-detail-options"><div class="instrument-parent speech-parent"><button aria-label="更多人声处理" aria-haspopup="menu" aria-expanded={showSpeechDetails} class:active={speechDetailScenarios.includes(scenario)} disabled={busy} onclick={()=>showSpeechDetails=!showSpeechDetails}>{speechDetailScenarios.includes(scenario)?currentScenario.label:'更多人声处理'}<ChevronDown size={15}/></button>
        {#if showSpeechDetails}<div class="instrument-menu" role="menu" aria-label="人声细节处理">{#each scenarios.filter(s=>speechDetailScenarios.includes(s.id)) as child}<button role="menuitemradio" aria-checked={scenario===child.id} onclick={()=>setScenario(child.id)}>{child.label}</button>{/each}</div>{/if}
      </div></div>
      </div>
      {#if scenario!=='duo'}<p class="scenario-description"><Info size={16}/>{currentScenario.label} · {currentScenario.description}</p>{/if}
      {#if scenario==='dme'}<p class="scenario-description">国际声是去人声后的背景估计，仍可能有人声残留或细节损失，请对照原音试听。</p>{/if}
      <div class="studio-workspace">
        <section class="studio-panel upload-panel" aria-labelledby="upload-title">
          <div class="panel-heading"><h2 id="upload-title">上传音频</h2><span class="section-hint">每个最长10分钟 · 512 MB</span></div>
          <div class:dragging class="drop-wrap" ondragover={(e)=>{e.preventDefault();if(!busy)dragging=true;}} ondragleave={()=>dragging=false} ondrop={(e)=>{e.preventDefault();dragging=false;void acceptFiles(e.dataTransfer?.files);}} role="region" aria-label="拖入音频区域">
            <button class="studio-drop" disabled={busy || readingFiles} onclick={()=>inputEl?.click()}><CloudUpload size={36} strokeWidth={1.5}/><strong>拖入多个音频，或点击选择</strong><span>WAV / FLAC / MP3 / M4A · 每批最多20个，合计2 GB</span></button>
            <input type="file" multiple class="sr-only" tabindex="-1" aria-label="选择音频文件" accept=".wav,.flac,.mp3,.m4a,.ogg,.aac,audio/*" bind:this={inputEl} onchange={(e)=>void acceptFiles(e.currentTarget.files || undefined)}/>
          </div>
          {#if inputs.length}
            <div class="input-list-heading"><span>已导入 {inputs.length} 个音频</span><button class="text-action" disabled={busy || readingFiles} onclick={resetFile}>清空导入</button></div>
            <div class="input-list">{#each inputs as input (input.id)}<div class="studio-file" class:active={activeInput?.id===input.id}><button class="file-preview" aria-pressed={activeInput?.id===input.id} onclick={()=>selectedInput=input.id}><Music2 size={18}/><span class="file-info"><strong title={input.name}>{input.name}</strong><span>{input.duration?timeLabel(input.duration):'已上传'} · {fileSize(input.size)}{input.assetId?' · 已上传，可直接复用':''}</span></span></button><button class="icon-action" aria-label={`移除${input.name}`} disabled={busy || readingFiles} onclick={()=>removeInput(input.id)}><X size={17}/></button></div>{/each}</div>
            <audio onplay={soloPlayback} class="source-player" aria-label="原始音频试听" src={fileUrl} controls preload="metadata"></audio>
          {:else}<div class="file-empty">可一次选择或拖入多个文件，依次完成分离。</div>{/if}
          {#if readingFiles}<p class="progress-text" role="status">正在读取音频信息…</p>{/if}
          <div class="studio-output-options">{#if activeInput?.parent}<p class="input-origin">来源：{activeInput.parent.label} · <a href={'?job='+activeInput.parent.job_id}>查看上一轮结果</a></p>{/if}<h2>输出音轨</h2><p>选择本次需要输出的音轨。（至少选择一项）</p>
            {#if selectedMatchesScenario && selected.stems.length}
              <div class="stem-line"><div class="stem-choices">{#each outputStems(selected,scenario) as stem}<label><Checkbox checked={selectedStems.includes(stem.id)} disabled={busy} onCheckedChange={(value)=>toggleStem(stem.id,value===true)} aria-label={stem.label}/><span>{stem.label}</span></label>{/each}</div><span class="format-note">输出格式：WAV · 48 kHz · 24 bit</span></div>
            {:else}<div class="metadata-note"><Info size={18}/>此类型暂时没有可使用的模型，可前往模型库查看目录。</div>{/if}
          </div>
          {#if message}<div class="inline-message" role="alert"><CircleAlert size={18}/>{message}</div>{/if}
          <Button class="start-button" disabled={busy || readingFiles || !inputs.length || !connected || !selectedMatchesScenario} onclick={()=>void start()}>{#if busy}<Loader2 class="size-5 animate-spin"/>{batch?.jobs.some(j=>j.status==='waiting')?'等待显卡资源…':progress.split(' · ')[0]}{:else}<AudioLines class="size-5"/>{inputs.length>1?`${actionLabel}（${inputs.length}个文件）`:actionLabel}{/if}</Button>
          {#if progress}<p class="progress-text" role="status">{progress}</p>{/if}{#if batch && ['preparing','partial','interrupted'].includes(batch.status) && !busy}<Button variant="outline" class="continue-batch" onclick={()=>void continueBatch()}>处理已上传文件 / 重试未完成</Button>{/if}{#if batch}<ul class="batch-status" aria-label="批量处理状态">{#each batch.jobs as job (job.id)}<li><span>{job.filename}</span><span class:job-failed={job.status==='failed'}>{job.status==='succeeded'?'已完成':job.status==='failed'?job.error || '未完成':['running','waiting'].includes(job.status)?job.message || '等待处理':'等待处理'}</span></li>{/each}</ul>{/if}{#if connectionLost || !connected}<button class="text-action reconnect-action" onclick={reconnect}>重新连接任务</button>{/if}
        </section>
        <section class="studio-panel model-panel" aria-labelledby="model-title">
          <div class="panel-heading"><h2 id="model-title">{['denoise','superres'].includes(scenario)?'处理模型':'分离模型'}</h2><button class="text-action" disabled={busy} onclick={openLibrary}>查看模型库</button></div>
          <p class="panel-description quality-hint">{scenario==='dme'?'国际声优先；双轨保留整体背景，三轨可单独取配乐与音效。':['speakers','superres'].includes(scenario)?'按当前用途显示模型，已导入音频可直接复用。':'新旧优质模型一起展示，置顶模型优先。'}</p>
          <div class="featured-models" role="radiogroup" aria-label="推荐分离模型">
            {#each featuredModels as model (model.id)}
              <article class="quality-model-card" class:selected={model.id===selectedId} data-testid={model.id===selectedId?'current-model':undefined}>
                <button class="quality-model-main" role="radio" aria-checked={model.id===selectedId} tabindex={model.id===selectedId?0:-1} aria-label={model.title} disabled={busy} onclick={()=>setModel(model)} onkeydown={cardKey}>
                  <span class="quality-model-title">{model.title}{#if model.tag}<span class="model-tag">{model.tag}</span>{/if}<span class="quality-ready">可使用</span></span>
                  <p>{modelDescription(model,scenario)}</p>
                  <span class="card-meta"><span class="card-capabilities">可导出：{capabilityText(model,scenario)}</span><span class="card-size">文件大小：{fileSize(model.size)}</span></span>
                  {#if showFilenames}<span class="model-filename">{model.id}</span>{/if}
                </button>
                <button class="icon-action card-pin" aria-label={`${pinned.includes(model.id)?'取消置顶':'置顶'}${model.title}`} aria-pressed={pinned.includes(model.id)} disabled={busy} onclick={()=>togglePin(model.id)}>{#if pinned.includes(model.id)}<PinOff size={15}/>{:else}<Pin size={15}/>{/if}</button>
              </article>
            {:else}<p class="model-unavailable">当前用途暂时没有可用模型，已导入音频会保留。<button class="text-action" onclick={()=>void refreshModels()}>重新连接模型服务</button></p>{/each}
          </div>
          {#if orderedModels.length>featuredModels.length}<div class="model-picker">
            <button class="picker-trigger" disabled={busy || orderedModels.length<=featuredModels.length} aria-expanded={showPicker} aria-controls="model-picker-menu" onclick={togglePicker}><span>更多可用模型{#if pickerModels.length}（{pickerModels.length}）{/if}</span><ChevronDown size={16}/></button>
            {#if showPicker}<div class="picker-menu" class:picker-up={pickerUp} id="model-picker-menu">
              <div class="picker-search"><Search size={16}/><input bind:value={pickQuery} placeholder="搜索当前用途的模型" aria-label="搜索下拉模型"/></div>
              <p class="picker-scroll-hint">按质量排序 · 滚动查看更多，可拖动右下角调整高度</p>
              <div class="picker-options" style:height={`${Math.min(420,pickerMaxHeight)}px`} style:max-height={`${pickerMaxHeight}px`} role="listbox" aria-label="可选分离模型" tabindex="-1" onkeydown={(e)=>{if(e.key==='Escape'){showPicker=false;return;} if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){e.preventDefault();const nodes=Array.from(e.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'));const at=nodes.indexOf(document.activeElement as HTMLButtonElement);const index=e.key==='Home'?0:e.key==='End'?nodes.length-1:e.key==='ArrowDown'?(at+1)%nodes.length:(at-1+nodes.length)%nodes.length;nodes[index]?.focus();}}}>
                {#each pickerModels as model (model.id)}<button role="option" aria-selected={selectedId===model.id} disabled={!model.available} onclick={()=>setModel(model)}><span>{#if pinned.includes(model.id)}<Pin size={13}/>{/if}{model.title}<small>{model.tag}{model.available?' · 可使用':' · '+(model.reason || '未安装')}</small><small class="picker-description">{modelDescription(model,scenario)}</small><small>{fileSize(model.size)} · {capabilityText(model,scenario)}</small></span>{#if selectedId===model.id}<CheckCircle2 size={16}/>{/if}</button>{:else}<p class="picker-empty">没有匹配的可用模型，可前往模型库查看。</p>{/each}
              </div>
            </div>{/if}
          </div>{/if}
          <details class="quality-sources"><summary>推荐参考</summary><p>综合同用途公开评测、社区试听反馈与输出适配，不同素材可切换比较。</p>{#each qualityReferences as reference}<a href={reference.url} target="_blank" rel="noreferrer">{reference.title}</a>{/each}</details>
        </section>
      </div>
      <section class="studio-panel results-panel" bind:this={resultSection} aria-labelledby="results-title">
        <div class="panel-heading"><h2 id="results-title">试听与导出</h2></div>
        {#if chainNotice}<p class="export-message" role="status">{chainNotice}</p>{/if}
        {#if resultJobs.length}
          <div class="export-toolbar"><span>共 {resultJobs.length} 个文件 · 已选 {selectedExports.length} 条音轨</span><div class="export-actions"><button class="text-action" onclick={()=>exportSelection=exportEntries.map(e=>e.key)}>全选</button><button class="text-action" onclick={()=>exportSelection=[]}>取消全选</button><label>导出方式<select bind:value={exportFormat} aria-label="导出方式"><option value="zip">ZIP 打包</option><option value="files">逐个 WAV</option></select></label><Button variant="outline" disabled={!selectedExports.length || exporting} onclick={()=>void downloadSelected()}><Download size={15}/>{exporting?'正在准备…':'导出所选音轨'}</Button><button class="text-action" disabled={busy} onclick={clearResult}>清空结果</button></div></div>
          {#if exportMessage}<p class="export-message" role="status">{exportMessage}</p>{/if}
          {#if preparedExport}<div class="prepared-export"><Button variant="outline" href={preparedExport.url} download={preparedExport.filename}><Download size={15}/>下载 ZIP（{fileSize(preparedExport.bytes)}）</Button><span>已生成的压缩包保留打包时所选音轨；更改选择后可重新导出。</span></div>{/if}
          <div class="result-files">{#each resultJobs as job (job.id)}
            <section class="result-file"><div class="result-file-heading"><button class="result-toggle" aria-expanded={expandedResults.includes(job.id)} onclick={()=>expandedResults=expandedResults.includes(job.id)?expandedResults.filter(id=>id!==job.id):[...expandedResults,job.id]}><ChevronDown size={16}/><strong>{job.filename}</strong><span>{catalog.find(m=>m.id===job.model)?.title || job.model} · {job.outputs.length}轨</span></button><label><Checkbox checked={job.outputs.every(o=>exportSelection.includes(job.id+'|'+o.stem))} onCheckedChange={(value)=>{for(const o of job.outputs)toggleExport(job.id+'|'+o.stem,value===true);}} aria-label={`选择${job.filename}全部音轨`}/>选择此文件全部音轨</label></div>
              {#if expandedResults.includes(job.id)}<div class="result-tracks">{#each job.outputs as output (output.url)}<div class="export-track"><label class="export-track-choice"><Checkbox checked={exportSelection.includes(job.id+'|'+output.stem)} onCheckedChange={(value)=>toggleExport(job.id+'|'+output.stem,value===true)} aria-label={`导出${job.filename}的${output.label}`}/>导出{output.label}</label><WaveformTrack {output} onplay={soloPlayback}/><details class="continue-track"><summary>{deriving===job.id+'|'+output.stem?'正在准备音轨…':'继续处理这条音轨'}</summary><div class="continue-options"><button disabled={busy || !!deriving} onclick={()=>void continueTrack(job.id,output,'karaoke')}>分离主唱与和声</button><button disabled={busy || !!deriving} onclick={()=>void continueTrack(job.id,output,'dme')}>分离音乐与音效</button><button disabled={busy || !!deriving} onclick={()=>void continueTrack(job.id,output,'denoise')}>人声降噪</button><button disabled={busy || !!deriving} onclick={()=>void continueTrack(job.id,output,'choose')}>作为输入，选择其他用途</button></div></details></div>{/each}</div>{/if}
            </section>
          {/each}</div>
        {:else}<div class="results-empty"><Music2 size={38}/><strong>处理完成后，在这里试听和下载每条音轨。</strong><span>可选择多条音轨逐个导出，或打包为 ZIP。</span></div>{/if}
      </section>
    {:else if view==='library'}
      <button class="back-action" onclick={()=>view='workbench'}><ArrowLeft size={17}/>返回工作台</button>
      <section class="studio-panel full-library"><div class="panel-heading"><h2>按用途浏览模型</h2><span class="library-count">{visibleModelCount} / {models.filter(m=>!m.hidden).length}</span></div>{@render libraryControls()}{@render modelList()}</section>
    {:else}
      <button class="back-action" onclick={()=>view='workbench'}><ArrowLeft size={17}/>返回工作台</button>
      <section class="studio-panel settings-panel"><h2>显示偏好</h2><div class="settings-row"><div><h3>显示模型文件名</h3><p>在中文用途名下保留完整文件名，便于核对。</p></div><Checkbox bind:checked={showFilenames} aria-label="显示模型文件名"/></div><div class="settings-row"><div><h3>界面主题</h3><p>选择适合当前工作环境的明暗模式。</p></div><Button variant="outline" onclick={()=>theme=theme==='light'?'dark':'light'}>{#if theme==='light'}<Moon class="size-4"/>切换深色{:else}<Sun class="size-4"/>切换浅色{/if}</Button></div><div class="settings-row"><div><h3>分离结果</h3><p>清空本次浏览器内的分离音轨，保留输入文件。</p></div><Button variant="outline" disabled={!resultJobs.length || busy} onclick={clearResult}><RotateCcw class="size-4"/>清空结果</Button></div><div class="settings-about"><h3>关于工作台</h3><p>支持多文件依次分离、逐轨试听及ZIP批量导出。已就绪模型可以直接选择；置顶保存在当前浏览器，刷新后保留。</p><p>默认按用途与分离质量推荐，年份只作标签；上次任务和结果可在刷新后恢复。</p></div></section>
    {/if}
  </main>
</div>

{#snippet libraryControls()}
  <div class="library-tools grouped-library-tools"><div class="library-search"><Search size={18}/><Input bind:value={query} placeholder="搜索模型名称、原有说明或用途" aria-label="搜索模型、作者或用途"/></div><label class="library-select">范围<select bind:value={filter} aria-label="筛选范围"><option value="all">全部模型</option><option value="ready">可使用</option><option value="curated">重点推荐</option><option value="downloaded">已下载</option><option value="missing">待下载</option><option value="pinned">已置顶</option></select></label></div>
  <p class="library-note">全部用途按组展开，组内可使用与置顶模型优先，再按分离质量推荐；保留原名、完整文件名与原有说明。</p>
  <nav class="library-group-links" aria-label="模型用途分组">{#each libraryGroups as group}<a href={`#library-group-${group.id}`}>{group.label}<span>{group.models.length}</span></a>{/each}</nav>
  <p class="library-note">SCNet XL DNR：所给官方来源未找到对应权重，暂未收录为可用模型。<a href="https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md" target="_blank" rel="noreferrer">查看官方清单</a></p>
{/snippet}
{#snippet modelList()}
  <div class="studio-library-list grouped-library" aria-label="模型搜索结果">
    {#each libraryGroups as group (group.id)}
      <section class="library-group" id={`library-group-${group.id}`} aria-labelledby={`library-group-title-${group.id}`}>
        <div class="library-group-heading"><h3 id={`library-group-title-${group.id}`}>{group.label}</h3><span>{group.models.length} 款 · {group.models.filter(m=>m.available).length} 款可使用</span></div>
        <div class="library-group-grid">
          {#each group.models as model (model.id)}
            <article class="library-model" data-model-id={model.id}>
              <div class="library-model-main"><div class="library-model-title"><strong>{model.title}</strong>{#if model.tag}<span class="model-tag">{model.tag}</span>{/if}<span class="model-state" class:downloaded={model.available}>{model.available?'可使用':model.reason || '未接入'}</span></div><code>{model.id}</code>
                <p>{modelDescription(model,group.id)}</p>
                {#if model.originalDescription && model.originalDescription!==model.description}<p class="original-description"><span>原有说明：</span>{model.originalDescription}</p>{/if}
                <div class="library-model-meta"><span class="library-size">文件大小：{fileSize(model.size)}</span><span class="library-capabilities">{model.available?'可导出':'目录目标'}：{capabilityText(model,group.id)}</span></div>{#if model.caution && !model.caution.includes('商用')}<p class="library-caution">{model.caution.replace(/CC BY[^。]*。?/g,'')}</p>{/if}
              </div>
              <div class="library-model-actions"><button class="icon-action" aria-label={`${pinned.includes(model.id)?'取消置顶':'置顶'}${model.title}`} aria-pressed={pinned.includes(model.id)} onclick={()=>togglePin(model.id)}>{#if pinned.includes(model.id)}<PinOff size={16}/>{:else}<Pin size={16}/>{/if}</button><Button variant="outline" disabled={!model.available} onclick={()=>void chooseLibrary(model,group.id)}>使用此模型处理</Button></div>
            </article>
          {/each}
        </div>
      </section>
    {:else}<div class="library-empty"><Search size={32}/><strong>没有找到符合条件的模型</strong><p>试试更短的关键词，或把范围切换到全部模型。</p><Button variant="outline" onclick={()=>{query='';filter='all';}}>清除筛选</Button></div>{/each}
  </div>
{/snippet}

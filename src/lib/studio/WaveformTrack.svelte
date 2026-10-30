<script lang="ts">
  import { onMount,onDestroy } from 'svelte';
  import { Download,Loader2 } from '@lucide/svelte';
  import { Button } from '../components/ui/button';
  import { timeLabel,downloadURL } from './audio-utils';
  import { fileSize } from './models';
  import type { TrackOutput } from './studio-api';
  let {output,onplay}:{output:TrackOutput;onplay:(event:Event)=>void}=$props();
  let audio=$state<HTMLAudioElement>();let peaks=$state<number[]>([]);let loading=$state(true);let error=$state('');
  let time=$state(0);let duration=$state(0);
  const clipId=$derived('wave-'+output.url.replace(/[^a-z0-9]/gi,''));
  const waveform=$derived(peaks.map((p,i)=>{const height=Math.max(.25,Math.min(1,p)*32);return `M${i+.5},${36-height}v${height*2}`;}).join(''));
  const percent=$derived(duration?Math.max(0,Math.min(100,time/duration*100)):0);
  let controller:AbortController | undefined;
  async function loadWaveform(){
    controller?.abort();controller=new AbortController();const active=controller;let timedOut=false;const timeout=setTimeout(()=>{timedOut=true;active.abort();},20000);loading=true;error='';
    try{const response=await fetch(output.waveform_url || output.url+'/waveform',{signal:controller.signal});if(!response.ok)throw new Error();const data=await response.json();if(!Array.isArray(data.peaks)||!data.peaks.length)throw new Error();peaks=data.peaks;duration=data.duration;}
    catch(e){if(timedOut)error='波形加载超时，请重试';else if(!(e instanceof DOMException && e.name==='AbortError'))error='波形暂时无法加载';}
    finally{clearTimeout(timeout);if(controller===active)loading=false;}
  }
  function seek(event:Event){if(audio){audio.currentTime=Number((event.currentTarget as HTMLInputElement).value);time=audio.currentTime;}}
  onMount(()=>{duration=output.frames && output.sample_rate?output.frames/output.sample_rate:0;void loadWaveform();});onDestroy(()=>controller?.abort());
</script>

<article class="result-track waveform-track">
  <div class="waveform-title"><strong>{output.label}</strong><span>{#if output.bytes}{fileSize(output.bytes)} · {/if}{timeLabel(duration)} · WAV · 48 kHz · 24 bit</span></div>
  <div class="waveform-view" class:waveform-loading={loading}>
    {#if peaks.length}
      <svg viewBox={`0 0 ${peaks.length} 72`} preserveAspectRatio="none" aria-hidden="true"><defs><clipPath id={clipId}><rect width={`${percent}%`} height="72"/></clipPath></defs><path d={waveform} stroke="#a9bfdc" stroke-width=".65"/><path d={waveform} stroke="#286bb5" stroke-width=".65" clip-path={`url(#${clipId})`}/></svg>
      <span class="waveform-playhead" style:left={`${percent}%`}></span>
    {:else}<div class="waveform-status">{#if loading}<Loader2 size={16} class="animate-spin"/>读取真实音频波形…{:else}{error}<button onclick={()=>void loadWaveform()}>重试</button>{/if}</div>{/if}
    <input type="range" min="0" max={duration || 1} step="0.01" value={time} disabled={!duration} oninput={seek} aria-label={`${output.label}波形定位`} aria-valuetext={`${timeLabel(time)} / ${timeLabel(duration)}`}/>
  </div>
  <div class="waveform-controls"><audio bind:this={audio} src={output.url} aria-label={`${output.label}试听`} controls preload="metadata" onplay={onplay} ontimeupdate={()=>time=audio?.currentTime || 0} onloadedmetadata={()=>duration=audio?.duration || duration}></audio><Button variant="outline" onclick={()=>downloadURL(`${output.url}?download=1`,`${output.label}.wav`)} aria-label={`下载${output.label}音频`}><Download class="size-4"/>下载 WAV</Button></div>
</article>

<style>
  .waveform-track{display:block!important;padding:15px 0!important;min-width:0;}
  .waveform-title{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:7px;}
  .waveform-title strong{font-size:14px;color:var(--st-text);}.waveform-title>span{font-size:12px;color:var(--st-muted);}
  .waveform-view{height:78px;position:relative;border-bottom:1px solid var(--st-line);background:var(--st-surface);overflow:hidden;}
  .waveform-view:focus-within{outline:2px solid var(--st-blue);outline-offset:2px;border-radius:3px;}
  svg{height:72px;width:100%;display:block;}
  .waveform-playhead{position:absolute;top:3px;bottom:0;width:1px;background:#2563eb;pointer-events:none;}
  .waveform-view input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:crosshair;}
  .waveform-status{height:100%;display:flex;align-items:center;justify-content:center;gap:8px;color:var(--st-muted);font-size:12px;}
  .waveform-status button{position:relative;z-index:2;color:var(--st-blue);padding:4px;}
  .waveform-controls{display:flex;gap:12px;align-items:center;margin-top:8px;}.waveform-controls audio{flex:1;width:0;height:36px;min-width:0;}
  @media(max-width:580px){.waveform-controls{flex-wrap:wrap;gap:7px;}.waveform-controls audio{flex-basis:100%;width:100%;}.waveform-title>span{font-size:12px;}.waveform-view{height:70px;}svg{height:64px;}}
</style>

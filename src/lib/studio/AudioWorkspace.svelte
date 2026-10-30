<script lang="ts">
  import {onMount} from 'svelte';
  import Studio from './Studio.svelte';
  import {AudioLines,ExternalLink} from '@lucide/svelte';
  let tool=$state<'pymss'|'msst'>('pymss');
  let msstOpened=$state(false);
  const msstURL='http://msst/?native=msst';
  onMount(()=>{if(new URLSearchParams(location.search).get('tool')==='msst'){tool='msst';msstOpened=true;}});
  function choose(next:'pymss'|'msst'){
    tool=next;if(next==='msst')msstOpened=true;
    const url=new URL(location.href);if(next==='msst')url.searchParams.set('tool','msst');else url.searchParams.delete('tool');history.replaceState(null,'',url);
  }
</script>

<svelte:head><title>音频分离 · {tool==='pymss'?'PYMSS':'MSST'}</title></svelte:head>
<div class="audio-workspace">
  <header class="audio-workspace-bar">
    <div class="audio-workspace-brand"><AudioLines size={24}/><div><strong>音频分离</strong><span>MSST 和 PYMSS</span></div></div>
    <nav aria-label="分离工具"><button class:active={tool==='pymss'} aria-pressed={tool==='pymss'} onclick={()=>choose('pymss')}>PYMSS</button><button class:active={tool==='msst'} aria-pressed={tool==='msst'} onclick={()=>choose('msst')}>MSST</button></nav>
  </header>
  <div hidden={tool!=='pymss'} class="pymss-workspace"><Studio/></div>
  {#if msstOpened}<section hidden={tool!=='msst'} class="msst-workspace" aria-label="MSST 工作台"><div class="msst-workspace-heading"><span>MSST 工作台</span><a href={msstURL} target="_blank" rel="noreferrer">独立窗口打开<ExternalLink size={14}/></a></div><iframe title="MSST 音频分离工作台" src={msstURL} allow="autoplay; clipboard-write"></iframe></section>{/if}
</div>

<style>
  .audio-workspace{font-family:system-ui,'PingFang SC','Microsoft YaHei',sans-serif;color:#142238;background:#f5f7fa;min-height:100vh;}
  .audio-workspace-bar{height:64px;position:sticky;top:0;z-index:100;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 24px;background:#fff;border-bottom:1px solid #dce4ef;}
  .audio-workspace-brand{display:flex;align-items:center;gap:10px;color:#235fe7;}.audio-workspace-brand>div{display:flex;flex-direction:column;}
  .audio-workspace-brand strong{font-size:18px;line-height:1.4;color:#142238;}.audio-workspace-brand span{font-size:12px;color:#586b8c;}
  nav{display:flex;gap:4px;padding:4px;border-radius:8px;background:#eef2f8;border:1px solid #dce4ef;}
  nav button{font:600 14px/1.4 system-ui,sans-serif;border:1px solid transparent;min-width:116px;height:36px;border-radius:5px;background:transparent;color:#536783;cursor:pointer;}
  nav button.active{background:#2463eb;color:white;border-color:#2463eb;box-shadow:0 1px 3px #24457824;}
  nav button:focus-visible,a:focus-visible{outline:3px solid #8cafff;outline-offset:3px;}
  .pymss-workspace[hidden],.msst-workspace[hidden]{display:none;}
  :global(.audio-workspace .studio){min-height:calc(100vh - 64px);}
  :global(.audio-workspace .studio-sidebar){top:64px;}
  .msst-workspace-heading{height:40px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;font-size:13px;color:#586b8c;background:#f5f7fa;}
  .msst-workspace-heading a{display:inline-flex;align-items:center;gap:5px;color:#2463eb;font-size:12px;text-decoration:none;}
  iframe{display:block;width:100%;height:calc(100vh - 104px);min-height:540px;border:0;background:white;}
  @media(max-width:580px){.audio-workspace-bar{padding:0 14px;gap:8px;}.audio-workspace-brand{gap:6px;}.audio-workspace-brand>:global(svg){display:none;}.audio-workspace-brand strong{font-size:16px;}.audio-workspace-brand span{font-size:12px;}nav button{min-width:72px;height:34px;font-size:14px;}nav{padding:3px;}:global(.audio-workspace .studio-sidebar){top:auto;}.msst-workspace-heading{padding:0 14px;}iframe{min-height:540px;}}
</style>

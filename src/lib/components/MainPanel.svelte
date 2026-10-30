<script lang="ts">
  import Alerts from "./Alerts.svelte";
  import CatalogView from "./CatalogView.svelte";
  import DashboardView from "./DashboardView.svelte";
  import LoadedView from "./LoadedView.svelte";
  import SeparationView from "./SeparationView.svelte";
  import SettingsView from "./SettingsView.svelte";
  import WorkbenchView from "./WorkbenchView.svelte";
  import type {
    CatalogListResponse,
    CatalogModel,
    CatalogQuery,
    DownloadSource,
    DownloadSourceName,
    HealthResponse,
    LoadedModel,
    OutputAudioFormat,
    SeparationJsonResult,
    SeparationResponseFormat,
    ServerInfo,
    Theme,
    View,
  } from "../types";

  interface MainPanelState {
    activeView: View;
    errorMessage: string;
    noticeMessage: string;
    health: HealthResponse | null;
    serverInfo: ServerInfo | null;
    downloadSource: DownloadSource | null;
    loadedModel: LoadedModel | null;
    catalog: CatalogListResponse | null;
    selectedCatalog: CatalogModel | null;
    selectedDownloadModels: string[];
    busyAction: string | null;
    selectedStems: string[];
    resultUrl: string | null;
    resultName: string;
    jsonResult: SeparationJsonResult | null;
    token: string;
  }

  interface MainPanelActions {
    onSelectView: (view: View) => void;
    onDismissError: () => void;
    onDismissNotice: () => void;
    onApplyCatalogFilters: () => void;
    onShowCatalogDetail: (model: string) => void;
    onDownload: (model: string) => void;
    onDownloadSelected: () => void;
    onToggleDownloadSelection: (model: string, checked: boolean) => void;
    onSetDownloadSelection: (models: string[]) => void;
    onSetLoadTarget: (model: string) => void;
    onLoadModel: (model: string) => void;
    onCloseDetail: () => void;
    onLoad: () => void;
    onToggleStem: (stem: string, checked: boolean) => void;
    onSeparate: () => void;
    onDownloadJsonOutput: (output: SeparationJsonResult["outputs"][number]) => void;
    onSaveDownloadSource: () => void;
    onOpenToken: () => void;
    onClearToken: () => void;
    onThemeChange: (theme: Theme) => void;
  }

  export let state: MainPanelState;
  export let actions: MainPanelActions;
  export let catalogQuery: CatalogQuery;
  export let loadModelName: string;
  export let loadSourceOverride: DownloadSourceName | "";
  export let loadEndpointOverride: string;
  export let inferenceParamsText: string;
  export let audioFile: File | null;
  export let responseFormat: SeparationResponseFormat;
  export let outputAudioFormat: OutputAudioFormat;
  export let theme: Theme;
  export let downloadSourceForm: DownloadSourceName;
  export let downloadEndpointForm: string;
</script>

<section class={`w-full space-y-10 px-4 py-8 sm:px-6 lg:py-12 ${state.activeView === "workbench" ? "" : "mx-auto max-w-5xl"}`}>
  <Alerts
    errorMessage={state.errorMessage}
    noticeMessage={state.noticeMessage}
    onDismissError={actions.onDismissError}
    onDismissNotice={actions.onDismissNotice}
  />

  {#if state.activeView === "workbench"}
    <WorkbenchView
      catalog={state.catalog}
      loadedModel={state.loadedModel}
      selectedDownloadModels={state.selectedDownloadModels}
      busyAction={state.busyAction}
      selectedStems={state.selectedStems}
      resultUrl={state.resultUrl}
      resultName={state.resultName}
      jsonResult={state.jsonResult}
      bind:catalogQuery
      bind:audioFile
      bind:responseFormat
      bind:outputAudioFormat
      onApplyFilters={actions.onApplyCatalogFilters}
      onDownload={actions.onDownload}
      onDownloadSelected={actions.onDownloadSelected}
      onToggleDownloadSelection={actions.onToggleDownloadSelection}
      onSetDownloadSelection={actions.onSetDownloadSelection}
      onLoadModel={actions.onLoadModel}
      onToggleStem={actions.onToggleStem}
      onSeparate={actions.onSeparate}
      onDownloadJsonOutput={actions.onDownloadJsonOutput}
    />
  {:else if state.activeView === "dashboard"}
    <DashboardView
      health={state.health}
      serverInfo={state.serverInfo}
      downloadSource={state.downloadSource}
      loadedModel={state.loadedModel}
      onSelectView={actions.onSelectView}
    />
  {:else if state.activeView === "catalog"}
    <CatalogView
      catalog={state.catalog}
      selectedCatalog={state.selectedCatalog}
      selectedDownloadModels={state.selectedDownloadModels}
      bind:catalogQuery
      busyAction={state.busyAction}
      onApplyFilters={actions.onApplyCatalogFilters}
      onShowDetail={actions.onShowCatalogDetail}
      onDownload={actions.onDownload}
      onDownloadSelected={actions.onDownloadSelected}
      onToggleDownloadSelection={actions.onToggleDownloadSelection}
      onSetDownloadSelection={actions.onSetDownloadSelection}
      onSetLoadTarget={actions.onSetLoadTarget}
      onCloseDetail={actions.onCloseDetail}
    />
  {:else if state.activeView === "loaded"}
    <LoadedView
      loadedModel={state.loadedModel}
      busyAction={state.busyAction}
      bind:loadModelName
      bind:loadSourceOverride
      bind:loadEndpointOverride
      bind:inferenceParamsText
      onLoad={actions.onLoad}
    />
  {:else if state.activeView === "separate"}
    <SeparationView
      loadedModel={state.loadedModel}
      busyAction={state.busyAction}
      bind:audioFile
      selectedStems={state.selectedStems}
      bind:responseFormat
      bind:outputAudioFormat
      resultUrl={state.resultUrl}
      resultName={state.resultName}
      jsonResult={state.jsonResult}
      onToggleStem={actions.onToggleStem}
      onSeparate={actions.onSeparate}
      onDownloadJsonOutput={actions.onDownloadJsonOutput}
    />
  {:else if state.activeView === "settings"}
    <SettingsView
      serverInfo={state.serverInfo}
      busyAction={state.busyAction}
      token={state.token}
      bind:theme
      bind:downloadSourceForm
      bind:downloadEndpointForm
      onSaveDownloadSource={actions.onSaveDownloadSource}
      onOpenToken={actions.onOpenToken}
      onClearToken={actions.onClearToken}
      onThemeChange={actions.onThemeChange}
    />
  {/if}
</section>

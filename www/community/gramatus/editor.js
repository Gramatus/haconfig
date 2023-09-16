import {
  LitElement,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@2/core/lit-core.min.js";

// TODO: editor not created yet...
class PlaylistPickerEditor extends LitElement {
  _config;
  setConfig(config) {
    this._config = config;
  }

  configChanged(newConfig) {
    const event = new Event("config-changed", {
      bubbles: true,
      composed: true,
    });
    event.detail = { config: newConfig };
    this.dispatchEvent(event);
  }
  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      <div class="card-config">
        <div class="toolbar">
          <mwc-tab-bar
            .activeIndex=${this._selectedTab}
            @MDCTabBar:activated=${this._handleSwitchTab}
          >
            <mwc-tab .label=${"Layout"}></mwc-tab>
            <mwc-tab .label=${"Cards"}></mwc-tab>
          </mwc-tab-bar>
        </div>
        <div id="editor"></div>
      </div>
    `;
  }
}

customElements.define("playlist-picker-editor", PlaylistPickerEditor);

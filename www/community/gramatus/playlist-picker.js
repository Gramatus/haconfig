import {
  LitElement,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@2/core/lit-core.min.js";

class PlaylistPicker extends LitElement {
  /** See https://lit.dev/docs/components/properties/ */
  static get properties() {
    return {
      hass: {},
      _config: {},
      _cards: {},
    };
  }
  constructor() {
    super();
    this._card = {};
    this._config = {};
  }
  // The user supplied configuration. Throw an exception and Lovelace will render an error card.
  setConfig(config) {
    // if (!config.entity) {
    //   throw new Error('You need to define an entity');
    // }
    this._config = { ...config };
  }

  render() {
    return html` <div id="root" style="height: 100%;"></div> `;
    // return html` <div id="root"></div>
    //   ${this._render_fab()}`;
  }
  _createCard(baseConfig, cardHelpers) {
    // this object is the javascript version of the yaml config for a card
    const cardConfig = {
      type: "button",
      entity: "media_player.spotify_gramatus",
      show_name: true,
      show_icon: true,
      name: baseConfig.displayName,
      tap_action: {
        action: "call-service",
        service: "pyscript.set_wakeup_playlist",
        service_data: {
          playlist: baseConfig.name,
        },
      },
      card_mod: {
        style: {
          // Styling the outermost shadowroot through the "." property
          ".": `ha-card[role=button] > span {
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
            max-width: 100%;
            }`,
          // Styling deeper shadow roots by using more advanced selectors
          "ha-state-icon$ha-icon$": `:host ha-svg-icon::before {
content: "";
height: var(--mdc-icon-size, 24px);
width: var(--mdc-icon-size, 24px);
position: absolute;
background-image: url('${baseConfig.imageUrl}');
background-size: contain;
border-radius: 50%;
}\n`,
        },
      },
    };
    const el = cardHelpers.createCardElement(cardConfig);
    el.addEventListener("ll-rebuild", (ev) => {
      ev.stopPropagation();
      this._rebuildCard(el, cardConfig);
    });
    el.hass = this.hass;
    return el;
  }

  async updated(changedProperties) {
    super.updated(changedProperties);

    if (changedProperties.has("_config")) {
      const cardHelpers = await window.loadCardHelpers();
      this._card = this._createCard(
        {
          name: this._config.name,
          displayName: this._config.displayName ?? this._config.name,
          imageUrl: this._config.imageUrl,
        },
        cardHelpers
      );
      const root = this.shadowRoot.querySelector("#root");
      while (root?.firstChild) root.removeChild(root.firstChild);
      root.appendChild(this._card);
    }
    if (changedProperties.has("hass")) {
      // Whenever the state changes, a new `hass` object is set. Use this to update your content.
      this._card.hass = this.hass;
    }
  }

  getCardSize() {
    return 3;
  }
  /** Used for graphical configuration */
  // static getConfigElement() {
  //   return document.createElement("playlist-picker-editor");
  // }
  static getStubConfig() {
    return {
      layout_type: "masonry",
      layout: {},
      cards: [{ name: "2000s Country" }],
    };
  }
}

customElements.define("playlist-picker", PlaylistPicker);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "playlist-picker",
  name: "Gramatus Playlist Picker",
  preview: false, // Optional - defaults to false
  description: "A custom card made by me!", // Optional
});

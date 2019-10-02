import { customElement, TemplateResult, html, css, property } from 'lit-element';
import { getUrl } from '../utils';
import axios, { AxiosResponse, CancelTokenSource, AxiosStatic } from 'axios';
import '../options/Options';
import RapidElement, { EventHandler } from '../RapidElement';
import { CustomEventType } from '../interfaces';
import TextInput from '../textinput/TextInput';

import flru from 'flru';

const LOOK_AHEAD = 20;

@customElement("rp-select")
export default class Select extends RapidElement {

  static get styles() {
    return css`
      :host {
        transition: all ease-in-out 200ms;
      }

      input::placeholder {
        color: rgba(0,0,0,.15);
      }



      .remove-item {
        cursor: pointer;
        display: inline-block;
        padding: 3px 6px;
        border-right: 1px solid rgba(100, 100, 100, .2);
        margin: 0;
        background: rgba(100, 100, 100, .05);
      }

      .selected-item.multi .remove-item {
        display: none;
      }

      .remove-item:hover {
        background: rgba(100, 100, 100, .1);
      }


      
      input:focus {
        outline: none;
        box-shadow: none;
        cursor: text;
      }

      .arrow {
        --icon-color: #ccc;
        transition: all linear 150ms;
        padding-right: 8px;
      }

      .arrow:hover {
        --icon-color: #666;
      }

      .arrow.open {
        --icon-color: #666;
      }

      .rotated {
        transform: rotate(180deg);
      }

      rp-textinput {
        --color-widget-shadow-focused: #fff;
      }

      rp-icon {
        cursor: pointer;
      }

      

      .select-container {
        display: flex;
        flex-direction: row;
        align-items: center;

        box-shadow: var(--color-widget-shadow-focused) 0 1px 1px 0px inset;
        border-radius: var(--curvature-widget);
        background: var(--color-widget-bg);
        border: 1px solid var(--color-widget-border);

        transition: all ease-in-out 200ms;
        cursor: pointer;
      }

      .select-container:focus-within {
        border-color: var(--color-focus);
        background: var(--color-widget-bg-focused);
        box-shadow: var(--color-widget-shadow-focused) 0px 0px 3px 0px;
      }

      .left {
        width: 100%;
      }

      .selected {
        padding: 4px;
        display: flex;
        flex-direction: row;
        align-items: stretch;
        flex-wrap: wrap;
      }

      .selected.multi .selected-item {
        white-space: nowrap;
        margin: 2px;
        vertical-align: middle;
        background: rgba(100, 100, 100, .1);
        user-select: none; 
        border-radius: 2px;
        vertical-align: middle;
        
      }

      .selected-item .name {
        padding: 3px 8px;
        font-size: 90%;
        margin: 0;
        display: inline-block;
      }

      .selected.multi .selected-item.focused {
        background: rgba(100, 100, 100, .3);
      }

      input {
        cursor: pointer;
        padding: 4px 4px;
        font-size: 13px;
        background: none;
        color: var(--color-text);
        resize: none;
        box-shadow: none;
        margin: none;
        flex-grow: 1;
        width: 50px;
        border: none;
      }
    `
  }

  @property({type: Boolean})
  multi: boolean = false;

  @property({type: Boolean})
  searchOnFocus: boolean = false;

  @property({type: Array})
  selected: any[] = [];

  @property()
  placeholder: string = '';

  @property()
  endpoint: string;

  @property({type: String})
  input: string = '';

  @property({type: Array})
  options: any[] = [];

  @property({type: Number})
  quietMillis: number = 200;

  @property({type: Boolean})
  fetching: boolean;

  @property({type: Boolean})
  cache: boolean = true;

  @property({attribute: false})
  selectedIndex: number = -1;

  @property({attribute: false})
  cursorIndex: number;

  @property({attribute: false})
  anchorElement: HTMLElement;

  @property({attribute: false})
  renderOption: (option: any, selected: boolean) => void;

  @property({attribute: false})
  renderOptionName: (option: any, selected: boolean) => void;

  @property({attribute: false})
  renderOptionDetail: (option: any, selected: boolean) => void = ()=>{};

  @property({attribute: false})
  getOptions: (response: AxiosResponse) => any[] = this.getOptionsDefault;

  @property({attribute: false})
  isComplete: (newestOptions: any[], response: AxiosResponse) => boolean = this.isCompleteDefault;

  private lastQuery: number;
  private cancelToken: CancelTokenSource;
  private complete: boolean;
  private page: number;
  private query: string;

  private lruCache = flru(20);

  public constructor() {
    super();
  }

  public updated(changedProperties: Map<string, any>) {
    super.updated(changedProperties);

    if (changedProperties.has("selected")) {
      this.input = "";
      /* if (!this.multi) {
        (this.shadowRoot.querySelector("input") as HTMLInputElement).blur();
      }*/
    }

    if (changedProperties.has("input") && !changedProperties.has("selected")) {

      if (this.lastQuery) {
        window.clearTimeout(this.lastQuery);
      }
      this.lastQuery = window.setTimeout(()=>{
        this.fetchOptions(this.input);
      }, this.quietMillis);
    }

       // if our cursor changed, lets make sure our scrollbox is showing it
    if(changedProperties.has("cursorIndex")) {
      if (this.options.length > 0 && 
          this.query && 
          !this.complete && 
          this.cursorIndex > this.options.length - LOOK_AHEAD) {
        this.fetchOptions(this.query, this.page + 1);
      }
    }
  }

  private handleOptionSelection(event: CustomEvent) {
    const selected = event.detail.selected;
    
    if (this.multi) {
      this.selected.push(selected);
    } else {
      this.selected = [selected];
    }

    this.requestUpdate("selected");
    this.options = [];
    this.input = '';
    this.selectedIndex = -1;

    // event.stopPropagation();
    // event.preventDefault();

  }

  private getOptionsDefault(response: AxiosResponse): any[] {
    return response.data['results'];
  }

  private isCompleteDefault(newestOptions: any[], response: AxiosResponse): boolean {
    return !response.data['more'];
  }

  private removeSelection(selectionToRemove: any): void {
    this.selected = this.selected.filter((selection: any) => selection !== selectionToRemove)
    this.options = [];
  }

  private setOptions(options: any[]) {
    // filter out any options already selected by id
    // TODO: should maybe be doing a deep equals here with option to optimize
    if (this.selected.length > 0) {
      if (this.selected[0].id) {
        this.options = options.filter(option=>!this.selected.find(selected=>selected.id === option.id));
        return;
      }
    }

    this.options = options;
  }

  public fetchOptions(query: string, page: number = 0) {

    const cacheKey = `${query}_$page`;

    if (this.cache && this.lruCache.has(cacheKey)) {
      const {options, complete} = this.lruCache.get(cacheKey);
      this.setOptions(options);
      this.complete = complete;
      this.query = query;
      return;
    }
    
    if (!this.fetching) {
      // make sure we cancel any previous request
      if (this.cancelToken) {
        this.cancelToken.cancel();
      }

      const CancelToken = axios.CancelToken;
      this.cancelToken = CancelToken.source();

      let url = this.endpoint + encodeURIComponent(query);
      if (page){
        url += "&page=" + page;
      }

      this.fetching = true;
      getUrl(url, this.cancelToken.token).then((response: AxiosResponse) => {
        if (page === 0) {
          this.setOptions(this.getOptions(response));
          this.cursorIndex = 0;
          this.query = query;
          this.complete = this.isComplete(this.options, response);          
        } else {
          const newResults = this.getOptions(response);
          if (newResults.length > 0) {
            this.setOptions([ ...this.options, ...newResults]);
          }
          this.complete = this.isComplete(newResults, response);
        }

        if (this.cache) {
          this.lruCache.set(cacheKey, {options: this.options, complete: this.complete });
        }

        this.fetching = false;
        this.page = page;
      }).catch((reason: any)=>{
        // cancelled
      });
    }
  }

  private handleBlur() {
    // we don't do this immediately so we can handle click events outside of our input
    window.setTimeout(()=>{this.options = []}, 300);
  }

  private handleFocus(): void {
    /* if (this.searchOnFocus) {
      this.requestUpdate("input");
    }*/
  }

  private handleClick(): void {
    this.selectedIndex = -1;
    this.requestUpdate("input");
  }

  private handleKeyDown(evt: KeyboardEvent) {

    // see if we should open our options on a key event
    if(evt.key === 'Enter' || evt.key === 'ArrowDown' || (evt.key === 'n' && evt.ctrlKey)) {
      if (this.options.length === 0) {
        this.requestUpdate('input');
        return;
      }
    }

    // focus our last item on delete
    if (this.multi && evt.key === 'Backspace' && !this.input) {

      if (this.options.length > 0) {
        this.options = [];
        return;
      }

      if (this.selectedIndex === -1) {
        this.selectedIndex = this.selected.length - 1;
        this.options = [];
      } else {
        this.selected.pop();
        this.requestUpdate("selected");
        this.selectedIndex = -1;
      }
    } else {
      this.selectedIndex = -1;
    }

  }

  private handleKeyUp(evt: KeyboardEvent) {
    const ele = evt.currentTarget as HTMLInputElement;
    this.input = ele.value;
  }

  private handleCancel() {
    this.options = [];
  }

  private handleCursorChanged(event: CustomEvent) {
    this.cursorIndex = event.detail.index;
  }

  private handleContainerClick(event: MouseEvent) {
    const input = this.shadowRoot.querySelector('input');
    input.focus();
    input.click();
  }
  public getEventHandlers(): EventHandler[] {
    return [
      { event: CustomEventType.Canceled, method: this.handleCancel },
      { event: CustomEventType.CursorChanged, method: this.handleCursorChanged },
      // { event: CustomEventType.Selection, method: this.handleOptionSelection },
    ];
  }

  public firstUpdated(changedProperties: any) {
    this.anchorElement = this.shadowRoot.querySelector(".select-container");
  }

  private handleArrowClick(event: MouseEvent): void {
    if (this.options.length > 0) {
      this.options = [];
      event.preventDefault();
      event.stopPropagation();
    }
  }

  public render(): TemplateResult {

    return html`
      <div class="select-container" @click=${this.handleContainerClick}>
        <div class="left">
          <div class="selected ${this.multi ? 'multi' : 'single'}">
            ${this.selected.map((selected: any, index: number)=>html`
              <div  class="selected-item ${index===this.selectedIndex ? 'focused' : ''}">
                <div class="remove-item" @click=${(evt: MouseEvent)=>{ 
                  evt.preventDefault(); 
                  evt.stopPropagation(); 
                  this.removeSelection(selected)
                }}><rp-icon name="x" size="8"></rp-icon></div>
                <div class="name">${selected.name}</div>    
              </div>`)
            }
            <input 
              @keyup=${this.handleKeyUp}
              @keydown=${this.handleKeyDown}
              @blur=${this.handleBlur} 
              @focus=${this.handleFocus} 
              @click=${this.handleClick}
              type="text" 
              placeholder=${this.selected.length === 0 ? this.placeholder : ""} 
              .value=${this.input} />
          </div>
        </div>
        
        <div class="right" @click=${this.handleArrowClick}>
          <rp-icon 
            size="12"
            name="arrow-down-bold" 
            class="arrow ${this.options.length > 0 ? 'open' : ''}"></rp-icon>
        </div>
      </div>

      <rp-options
        cursorIndex=${this.cursorIndex}
        @rp-selection=${this.handleOptionSelection}
        .renderOptionDetail=${this.renderOptionDetail}
        .renderOptionName=${this.renderOptionName}
        .renderOption=${this.renderOption}
        .anchorTo=${this.anchorElement}
        .options=${this.options}
        ?visible=${this.options.length > 0}
      ></rp-options>`
  
  /*return html`
      <rp-textinput
        @keyup=${this.handleKeyUp}
        @keydown=${this.handleKeyDown}
        @blur=${this.handleBlur} 
        @focus=${this.handleFocus} 
        @click=${this.handleClick}
        .value=${this.input}  
        placeholder=${this.placeholder}
      >
        <div slot="left" class="selected ${this.multi ? 'multi' : 'single'}">
          ${this.selected.map((selected: any, index: number)=>html`
            <div  class="selected-item ${index===this.selectedIndex ? 'focused' : ''}">
              <div class="remove-item" @click=${(evt: MouseEvent)=>{ 
                evt.preventDefault(); 
                evt.stopPropagation(); 
                this.removeSelection(selected)
              }}><rp-icon name="x" size="8"></rp-icon></div>
              <div class="name">${selected.name}</div>
              
            </div>`)}
            
        </div>
        <div slot="right" @click=${this.handleArrowClick} class="arrow-slot">
          <rp-icon 
            size="12"
            name="arrow-down-bold" 
            class="arrow ${this.options.length > 0 ? 'open' : ''}"></rp-icon>
        </div>
    </rp-textinput>
      <rp-options
        cursorIndex=${this.cursorIndex}
        @rp-selection=${this.handleOptionSelection}
        .renderOptionDetail=${this.renderOptionDetail}
        .renderOptionName=${this.renderOptionName}
        .renderOption=${this.renderOption}
        .anchorTo=${this.anchorElement}
        .options=${this.options}
        ?visible=${this.options.length > 0}
      ></rp-options>
    `*/
  }
}
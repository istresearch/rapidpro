import { customElement, property } from 'lit-element/lib/decorators';
import { TemplateResult, html, css } from 'lit-element';
import RapidElement from '../RapidElement';
import { getUrl, serialize, postUrl } from '../utils';
import axios, { AxiosResponse, CancelTokenSource } from 'axios';
import { unsafeHTML } from 'lit-html/directives/unsafe-html';
import TextInput from '../textinput/TextInput';
import { throws } from 'assert';

@customElement("rp-modax")
export default class Modax extends RapidElement {
  
  static get styles() {
    return css`
      fieldset {
        border: none;
        margin: 0;
        padding: 0;
      }

      .control-group {
        margin-bottom: 15px;
      }

      .form-actions {
        display: none;
      }

      .body {
        padding: 20px;
      }

      rp-loading {
        margin: 0 auto;
        display: block;
        width: 150px;
      }

    `;
  }

  @property({type: String})
  header: string = "";

  @property({type: String})
  endpoint: string;

  @property({type: Boolean, reflect: true})
  open: boolean;

  @property({type: Boolean})
  fetching: boolean;

  @property({type: Boolean})
  submitting: boolean;

  @property({type: String})
  primaryName: string;

  @property({type: String})
  body: any = this.getLoading();


  private cancelToken: CancelTokenSource;

  private handleSlotClicked(): void {
    this.open = true;
  }

  private focusFirstInput(): void {
    window.setTimeout(()=>{ 
      const input = this.shadowRoot.querySelector("rp-textinput") as TextInput;
      if (input) {
        input.inputElement.click()
      }
    });
  }

  public updated(changes: Map<string, any>) {
    super.updated(changes);

    if(changes.has("open")) {
      if (this.open) {
        this.fetchForm();
      }
    }

    if (changes.has("body")) {
      this.focusFirstInput();      
    }
  }

  private getLoading() {
    return html`<rp-loading units=6 size=8></rp-loading>`;
  }

  private updatePrimaryButton(): void {
    window.setTimeout(()=>{
      const primaryName = (this.shadowRoot.querySelector("input[type='submit']") as any).value;
      if (primaryName) {
        this.primaryName = primaryName;
      }
      this.submitting = false;
    },0);
  }

  private fetchForm() {
    const CancelToken = axios.CancelToken;
    this.cancelToken = CancelToken.source();
    this.fetching = true;
    getUrl(this.endpoint, this.cancelToken.token, true).then((response: AxiosResponse) => {
      this.body = unsafeHTML(response.data);
      this.updatePrimaryButton();
    });
  }

  private handleDialogClick(evt: CustomEvent) {
    const button = evt.detail.button;
    if (!button.disabled) {
      if (button.name === this.primaryName) {
        this.submitting = true;
        const form = this.shadowRoot.querySelector('form');
        const postData = serialize(form);

        postUrl(this.endpoint, postData, true).then((response: AxiosResponse) => {
          window.setTimeout(()=>{

            const redirect = response.headers['temba-success'];
            if (redirect) {
              this.ownerDocument.location = redirect;
            } else {
              this.body = unsafeHTML(response.data);
              this.updatePrimaryButton();
            }
            
          }, 2000);

        });
      }
    }
    
    if(button.name === "Cancel") {
      this.open = false;
    }
  
  }

  public render(): TemplateResult {
    return html`
      <rp-dialog 
        header=${this.header} 
        .open=${this.open} 
        .primaryButtonName=${this.primaryName}
        .submitting=${this.submitting}
        @rp-button-clicked=${this.handleDialogClick.bind(this)}
      >
        <div class="body">
          ${this.body}
        </div>
      </rp-dialog>
      <slot @click=${this.handleSlotClicked}></slot>
    `;
  }
}
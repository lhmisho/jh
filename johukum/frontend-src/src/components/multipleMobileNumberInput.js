import {Component, html} from 'htm/preact/standalone'
import produce from 'immer'
import linkstate from 'linkstate'
import axios from 'axios'

export default class MulipleMobileNumberInput extends Component {

    componentWillMount() {
        this.setState({
            currentTxt: null,
            items: (this.props.value) ? this.props.value : [],
            message: null
        })
    }

    onChange() {
        if(this.props.onChange) {
            this.props.onChange(this.state.items)
        }
    }

    removeItem(idx) {
        return () => {
            this.setState(produce(this.state, draft => {
                draft.items.splice(idx, 1)
                draft.message = null
            }))
            this.onChange()
        }
    }

    addItem() {
        axios.get('/api/v2/mobile_number/verify/', {
            params: {
                mobile_number: this.state.currentTxt
            }
        }).then( resp => {
            if (resp.data.valid) {
                this.setState(produce(this.state, draft => {
                    draft.items.push(this.state.currentTxt)
                    draft.currentTxt = ''
                    draft.message = null
                }))
            } else {
                this.setState({
                    message: resp.data.message
                })
            }
            this.onChange()
        })
    }

    render() {
        let items = this.state.items.map((item, idx) => {
            return html`
                <a class="list-group-item clearfix">
                    ${item}
                    <span class="pull-right">
                        <span class="btn btn-xs btn-danger" onclick=${this.removeItem(idx).bind(this)}>
                            <i class="fa fa-times"></i>
                        </span>
                    </span>
                </a>
            `
        })
        const onKeyPress = (e) => {
            if (e.key === 'Enter') {
              this.addItem()
            }
        }
        return html`
            <div class="form-group">
                <label>Mobile Numbers</label>
                
                <div class="input-group">
                    <input type="text" class="form-control" 
                        onKeyPress=${onKeyPress} 
                        value=${this.state.currentTxt} 
                        oninput=${linkstate(this, 'currentTxt')} />
                    <span class="input-group-btn">
                        <button class="btn btn-info" onclick=${this.addItem.bind(this)}>
                            <i class="fa fa-plus-circle"></i> Add
                        </button>
                    </span>
                </div>
                ${this.state.message != null && html`<span class="text-danger">${this.state.message}</span>`}
                <div class="list-group" style="margin-top: 10px">
                    ${items}
                </div>
            </div>
        `
    }
}
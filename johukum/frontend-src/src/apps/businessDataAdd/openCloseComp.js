import {Component, html} from 'htm/preact/standalone'
import linkstate from 'linkstate'
import produce from 'immer'
import Select from 'react-select'

const OPEN_24_OPTIONS = [
    { value: true, label: 'Yes' },
    { value: false, label: 'No' }
]
class OpenCloseComp extends Component {

    componentWillMount() {
        this.setState(this.props.value)
    }

    isChanged(newState) {
        return ['open_from', 'open_till', 'leisure_start', 'leisure_end', 'open_24h']
            .map(item => this.state[item] != newState[item])
            .reduce((prev, nx) => prev || nx)
    }

    componentWillUpdate(nextProps, nextState) {
        if(this.props.onChange && this.isChanged(nextState)) {
            this.props.onChange(produce(nextState, draft => {}))
        }
    }

    render() {
        const defaultValue = this.state.open_24h ? OPEN_24_OPTIONS[0] : OPEN_24_OPTIONS[1]
        return html`
            <div class="openCloseWrap">
                <div class="form-group">
                    <label>Open 24 Hour?</label>
                    <${Select} options=${OPEN_24_OPTIONS} defaultValue=${defaultValue} onChange=${i => this.setState({ open_24h: i.value })} />
                </div>
                ${!this.state.open_24h && html`
                    <div class="row">
                        <div class="form-group col-md-3">
                            <label>Open From</label>
                            <input type="time" oninput=${linkstate(this, 'open_from')} value=${this.state.open_from} class="form-control" />
                        </div>
                        <div class="form-group col-md-3">
                            <label>Open Till</label>
                            <input type="time" oninput=${linkstate(this, 'open_till')} value=${this.state.open_till} class="form-control" />
                        </div>
                        <div class="form-group col-md-3">
                            <label>Leisure Start</label>
                            <input type="time" oninput=${linkstate(this, 'leisure_start')} value=${this.state.leisure_start} class="form-control" />
                        </div>
                        <div class="form-group col-md-3">
                            <label>Leisure End</label>
                            <input type="time" oninput=${linkstate(this, 'leisure_end')} value=${this.state.leisure_end} class="form-control" />
                        </div>
                    </div>
                `}
            </div>
        `
    }
}

export default OpenCloseComp
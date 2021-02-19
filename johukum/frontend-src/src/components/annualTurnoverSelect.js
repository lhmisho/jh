import {html, Component} from 'htm/preact/standalone'
import ArraySelect from "./arraySelect";

const OPTIONS = [
    'N/A',
    '1-500000',
    '500001-1000000',
    '1000001-5000000',
    '5000001-20000000',
    '20000001-50000000',
    '50000001+'
]

export default class AnnualTurnoverSelect extends Component {

    onChange(val) {
        if(this.props.onChange) {
            this.props.onChange(val)
        }
    }

    render() {
        return html`
            <${ArraySelect} options=${OPTIONS} defaultValue=${this.props.defaultValue} onChange=${this.onChange.bind(this)} />
        `
    }
}
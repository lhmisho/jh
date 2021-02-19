import {html, Component} from 'htm/preact/standalone'
import ArraySelect from "./arraySelect";

const OPTIONS = [
    '1-5',
    '6-20',
    '21-50',
    '51-100',
    '101-500',
    '500+'
]
export default class NumberOfEmployeeSelect extends Component {

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
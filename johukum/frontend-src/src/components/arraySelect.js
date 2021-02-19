import {html, Component} from 'htm/preact/standalone'
import Select from 'react-select'

export default class ArraySelect extends Component {

    onChange(val) {
        if(this.props.onChange) {
            if(Array.isArray(val)) {
                this.props.onChange(val.map(x => x.value))
            } else {
                this.props.onChange(val.value)
            }
        }
    }

    render() {
        const items = this.props.options.map(item => {
            return { value:item, label: item }
        })

        let defaultValue = null
        if (this.props.defaultValue) {
            const selected = items.filter(item => {
                return this.props.defaultValue == item.value
            })
            if(selected.length > 0) {
                defaultValue = selected[0]
            }
        }


        return html`
            <${Select} options=${items} defaultValue=${defaultValue} onChange=${this.onChange.bind(this)} />
        `
    }
}
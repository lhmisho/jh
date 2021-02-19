import AsyncSelect from 'react-select/lib/Async'
import {Component, html} from 'htm/preact/standalone'
import axios from 'axios'
import produce from "immer/dist/immer";

export default class CategorySelect extends Component {

    componentWillMount() {
        this.setState({
            defaultValue: []
        })
        this.getDefaultValue(this.props.defaultValue)
    }

    componentWillRecieveProps(nextProps) {
        this.getDefaultValue(nextProps.defaultValue)
    }


    loadOptions(inputValue, callback) {
        axios.get('/api/v2/categories/', {
            params: {
                search: inputValue
            }
        }).then(resp => {
            callback(resp.data.results.map(item => {
                return {
                    value: item._id,
                    label: item.display_name
                }
            }))
        })
    }

    onChange(val) {
        this.setState({
            defaultValue:val
        })
        if(this.props.onChange) {
            if(Array.isArray(val)) {
                this.props.onChange(val.map(x => x.value))
            } else {
                this.props.onChange(val.value)
            }
        }
    }

    buildADefaultValue(id) {
        axios.get('/api/v2/categories/' + id + '/').then(resp => {
            this.setState(produce(this.state, draft => {
                draft.defaultValue.push({ value: resp.data._id, label: resp.data.name})
            }))
        })
    }

    getDefaultValue(defaultValue) {
        if(defaultValue) {
            defaultValue.map(item => this.buildADefaultValue(item))
        }
    }

    render() {
        return html`
            <${AsyncSelect} 
                cacheOptions 
                defaultOptions 
                onChange=${this.onChange.bind(this)}
                isMulti=${this.props.isMulti}
                loadOptions=${this.loadOptions}
                 value=${this.state.defaultValue}/>
        `
    }
}
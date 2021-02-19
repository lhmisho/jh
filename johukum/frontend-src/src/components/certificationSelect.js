import AsyncSelect from 'react-select/lib/Async'
import {Component, html} from 'htm/preact/standalone'
import axios from 'axios'
import produce from "immer/dist/immer";

export default class CertificationSelect extends Component {

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
        axios.get('/api/v2/certifications/', {
            params: {
                search: inputValue
            }
        }).then(resp => {
            const data = resp.data.results.map(item => {
                return {
                    value: item._id,
                    label: item.name
                }
            })
            callback(data)
        })
    }

    componentWillReceiveProps(nextProps, nextState) {
        this.setState({
            parent: nextProps.parent,
            location_type: nextProps.location_type
        })
    }

    handleInputChange (newValue) {
        this.setState({
            defaultValue:newValue
        })
        if (this.props.onChange) {
            if(Array.isArray(newValue)) {
                this.props.onChange(newValue.map(x => x.value))
            } else {
                this.props.onChange(newValue.value)
            }
        }
    }

    buildADefaultValue(id) {
        axios.get('/api/v2/certifications/' + id + '/').then(resp => {
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
                isMulti=${this.props.isMulti}
                defaultOptions=${this.props.defaultOptions}
                loadOptions=${this.loadOptions.bind(this)} 
                value=${this.state.defaultValue}
                onChange=${this.handleInputChange.bind(this)} />
        `
    }
}
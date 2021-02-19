import AsyncSelect from 'react-select/lib/Async'
import {Component, html} from 'htm/preact/standalone'
import axios from 'axios'

export default class LocationSelect extends Component {

    componentWillMount() {
        this.setState({
            parent: this.props.parent,
            location_type: this.props.location_type
        })
    }

    loadOptionHelper(params, callback) {
        axios.get('/api/v2/locations/', {
            params: params
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

    loadOptions(inputValue, callback) {
        this.loadOptionHelper({
            search: inputValue,
            location_type: this.state.location_type,
            parent: this.state.parent
        }, callback)
    }

    componentWillReceiveProps(nextProps, nextState) {
        this.setState({
            parent: nextProps.parent,
            location_type: nextProps.location_type
        })
    }

    shouldComponentUpdate() {
        return true
    }


    handleInputChange (newValue) {
        if (this.props.handleChange) {
            this.props.handleChange(newValue.value)
        }
    }

    render() {
        return html`
            <${AsyncSelect} 
                defaultValue=${this.props.defaultValue}
                key=${this.state.parent + "_" + this.state.location_type + this.props.defaultValue}
                defaultOptions=${this.props.defaultOptions}
                isClearable
                loadOptions=${this.loadOptions.bind(this)} 
                onChange=${this.handleInputChange.bind(this)} />
        `
    }
}
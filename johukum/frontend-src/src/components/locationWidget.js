import {Component, html} from 'htm/preact/standalone'
import LocationSelect from './locationSelect'
import axios from 'axios'

export default class LocationWidget extends Component {

    componentWillMount() {
        this.setState({
            division: null,
            city: null,
            thana: null,
            defaultValue: this.props.defaultValue,
            defaultCity: null,
            defaultThana: null,
            defaultDivision: null
        })
        this.loadFromDefaultValue()
    }

    componentWillReceiveProps(nextProps, nextState) {
        this.setState({
            defaultValue: nextProps.defaultValue
        })
        this.loadFromDefaultValue()
    }

    getDetail(id) {
        return axios.get('/api/v2/locations/' + id + '/')
    }

    setItemAndGetParent(id) {
        this.getDetail(id).then(resp => {
            if(resp.data.location_type == 4) {
                this.setState({
                    thana: resp.data._id,
                    defaultThana: {label:resp.data.name, value:resp.data._id}
                })
                this.setItemAndGetParent(resp.data.parent)
            } else if(resp.data.location_type == 2) {
                this.setState({
                    city: resp.data._id,
                    defaultCity: {label:resp.data.name, value:resp.data._id}
                })
                this.setItemAndGetParent(resp.data.parent)
            } else if (resp.data.location_type == 7) {
                this.setState({
                    division: resp.data._id,
                    defaultDivision: {label:resp.data.name, value:resp.data._id}
                })
            }
        })
    }


    loadFromDefaultValue(){
        if(this.state.defaultValue != null) {
            this.setItemAndGetParent(this.state.defaultValue)
        }
    }

    changed(val) {
        if(this.props.onChange) {
            if(this.props.lowestRequired)
                val = this.state.thana

            if (val != null)
                this.props.onChange(val)
        }
    }

    onDivisionChange(val) {
        this.setState({
            division: val,
            city: null,
            thana: null,
            defaultCity: null,
            defaultThana: null,
        })
        this.changed(val)
    }

    onCityChange(val) {
        this.setState({
            city: val,
            thana: null,
            defaultThana: null
        })
        this.changed(val)
    }

    onThanaChange(val) {
        this.setState({
            thana: val
        })
        this.changed(val)
    }

    componentWillRecieveProps(nextProps, nextState) {
        this.setState({ defaultValue: nextProps.defaultOptions })
        this.loadFromDefaultValue()
    }

    render() {
        return html`
            <div class='locationWidget row'>
                <div class="form-group col-md-4">
                    <label>Division</label>
                    <${LocationSelect} defaultValue=${this.state.defaultDivision} defaultOptions handleChange=${this.onDivisionChange.bind(this)} location_type="7" />
                </div>
                <div class="form-group col-md-4">
                    <label>City</label>
                    <${LocationSelect} defaultValue=${this.state.defaultCity} defaultOptions=${this.state.division != null} handleChange=${this.onCityChange.bind(this)} parent=${this.state.division} location_type="2" />
                </div>
                <div class="form-group col-md-4">
                    <label>Thana</label>
                    <${LocationSelect} defaultValue=${this.state.defaultThana} defaultOptions=${this.state.city != null} handleChange=${this.onThanaChange.bind(this)} parent=${this.state.city} location_type="4" />
                </div>
            </div>
        `
    }
}
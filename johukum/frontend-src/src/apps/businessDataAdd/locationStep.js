import {Component, html} from 'htm/preact/standalone'
import LocationWidget from '../../components/locationWidget'
import GeoLocationInput from '../../components/geolocationInput'
import linkstate from 'linkstate'
import produce from 'immer'
import {connect} from 'unistore/preact'
import store from './store'
import StepperComp from './stepper'

class LocationStep extends Component {
    componentWillMount() {
        this.setState({
            data: this.props.data.location,
            message: ''
        })
    }

    componentWillReceiveProps(nextProps, nextState) {
        this.setState({
            data: produce(nextProps.data.location, draft => {})
        })
    }

    isValid() {
        return (this.state.data.business_name != null && this.state.data.plus_code != null && this.state.data.location_id != null)
    }

    geoChange(newVal) {
        this.setState(produce(this.state, draft => {
            draft.data.geo = newVal
        }))
    }

    onNext() {
        if(this.isValid()) {
            this.props.updateLocation(this.state.data)
            this.props.setError(null)
            return true
        } else {
            this.props.setError('Business Name, Division, City, Thana and Pluscode is required')
            return false
        }
    }

    render() {
        this.state
        return html`
            <div class="locationStep">
                ${this.state.message && html`
                    <div class="alert alert-error">
                        <p>${this.state.message}</p>
                    </div>
                `}
                <div class="form-group">
                    <label>Business name *</label>
                    <input type="text" oninput=${linkstate(this, 'data.business_name')} value=${this.state.data.business_name} class="form-control" />
                </div>
                <div class="form-group">
                    <label>Building</label>
                    <input type="text" oninput=${linkstate(this, 'data.building')} value=${this.state.data.building} class="form-control" />
                </div>
                <div class="form-group">
                    <label>Street</label>
                    <input type="text" oninput=${linkstate(this, 'data.street')} value=${this.state.data.street} class="form-control" />
                </div>
                <div class="form-group">
                    <label>Land mark</label>
                    <input type="text" oninput=${linkstate(this, 'data.land_mark')} value=${this.state.data.land_mark} class="form-control" />
                </div>
                <${LocationWidget} lowestRequired onChange=${linkstate(this, 'data.location_id')} defaultValue=${this.state.data.location_id} />
                <div class="row">
                    <div class="form-group col-md-4">
                        <label>Post code</label>
                        <input type="text" oninput=${linkstate(this, 'data.postcode')} value=${this.state.data.postcode} class="form-control" />
                    </div>
                    <div class="form-group col-md-8">
                        <label>Area</label>
                        <input type="text" oninput=${linkstate(this, 'data.area')} value=${this.state.data.area}  class="form-control" />
                    </div>
                </div>
                <div class="row">
                    <div class="form-group col-md-4">
                        <label>Plus Code *</label>
                        <input type="text" oninput=${linkstate(this, 'data.plus_code')} value=${this.state.data.plus_code} class="form-control" />
                    </div>
                    <div class="form-group col-md-8">
                        <label>Geo Location</label>
                        <${GeoLocationInput} value=${this.state.data.geo} onChange=${this.geoChange.bind(this)} />
                    </div>
                </div>
                ${this.props.data._id == null && html`<${StepperComp} onNext=${this.onNext.bind(this)} />`}
                
            </div>
            
        `
    }
}

export default connect('data', store.actions)(LocationStep)
import {Component, html} from 'htm/preact/standalone'
import linkstate from 'linkstate'
import {connect} from 'unistore/preact'
import ArraySelect from '../../components/arraySelect'
import store from './store'
import MulipleMobileNumberInput from '../../components/multipleMobileNumberInput'
import StepperComp from './stepper'
import is from 'is_js'

const TITLE_OPTIONS = [
    'Mr.',
    'Mrs.',
    'Miss.',
    'Dr.'
]
class ContactStep extends Component {

    componentWillMount() {
        this.setState({
            data: this.props.data.contact
        })
    }

    isValid() {
        let message = []

        if(!this.state.data.title || is.empty(this.state.data.title)) message.push('Title is required')

        if(!this.state.data.name || is.empty(this.state.data.name)) message.push('Name is required')

        if(!this.state.data.designation || is.empty(this.state.data.designation)) message.push('Designation is required')

        if(this.state.data.email && !is.empty(this.state.data.email)&& !is.email(this.state.data.email))
            message.push('Please provide a valid email')

        if(this.state.data.website && !is.empty(this.state.data.website) && !is.url(this.state.data.website))
            message.push('Please provide a valid url for website')

        if(this.state.data.social_link && !is.empty(this.state.data.social_link) && !is.url(this.state.data.social_link))
                    message.push('Please provide a valid url for facebook')

        this.props.setError(message.length > 0 ? message.map(item => html`<li>${item}</li>`) : null)

        return message.length == 0
    }

    onNext() {
        if(this.isValid()) {
            this.props.updateContact(this.state.data)
            return true
        } else {
            return false
        }
    }

    render() {
        return html`    
            <div class="contactStep">
                <div class="row">
                    <div class="form-group col-md-4">
                        <label>Title *</label>
                        <${ArraySelect} options=${TITLE_OPTIONS} defaultValue=${this.state.data.title} onChange=${linkstate(this, 'data.title')} />
                    </div>
                    <div class="form-group col-md-8">
                        <label>Name *</label>
                        <input type="text" value=${this.state.data.name} oninput=${linkstate(this, 'data.name')} class="form-control" />
                    </div>
                </div>
                <div class="form-group">
                    <label>Designation *</label>
                    <input type="text" value=${this.state.data.designation} oninput=${linkstate(this, 'data.designation')} class="form-control" />
                </div>
                
                <${MulipleMobileNumberInput} value=${this.state.data.mobile_numbers} onChange=${linkstate(this, 'data.mobile_numbers')} />
                
                <div class="row">
                    <div class="form-group col-md-6">
                        <label>Landline No</label>
                        <input type="text" value=${this.state.data.landline_no} oninput=${linkstate(this, 'data.landline_no')} class="form-control" />
                    </div>
                    <div class="form-group col-md-6">
                        <label>Fax No</label>
                        <input type="text" value=${this.state.data.fax_no} oninput=${linkstate(this, 'data.fax_no')} class="form-control" />
                    </div>
                </div>
                <div class="row">
                    <div class="form-group col-md-6">
                        <label>Email</label>
                        <input type="email" value=${this.state.data.email} oninput=${linkstate(this, 'data.email')} class="form-control" />
                    </div>
                    <div class="form-group col-md-6">
                        <label>Website</label>
                        <input type="url" value=${this.state.data.website} oninput=${linkstate(this, 'data.website')} class="form-control" />
                    </div>
                    <div class="form-group col-md-6">
                        <label>Facebook</label>
                        <input type="url" value=${this.state.data.social_link} oninput=${linkstate(this, 'data.social_link')} class="form-control" />
                    </div>
                </div>
                ${this.props.data._id == null && html`<${StepperComp} onNext=${this.onNext.bind(this)} />`}
            </div>
        `
    }
}


export default connect(['currentStep', 'data'], store.actions)(ContactStep)
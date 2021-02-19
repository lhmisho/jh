import {Component, html} from 'htm/preact/standalone'
import linkstate from 'linkstate'
import produce from 'immer'
import {connect} from 'unistore/preact'
import store from './store'
import PaymentMethodSelect from '../../components/paymentMethodSelect'
import StepperComp from './stepper'


class SupportedPaymentMethodStep extends Component {

    componentWillMount() {
        this.setState({
            accepted_payment_methods: this.props.data.accepted_payment_methods
        })
    }

    onNext() {
        this.props.updatePaymentMethods(this.state.accepted_payment_methods)
        return true
    }

    onChange(val) {
        this.setState({
            accepted_payment_methods: val
        })
        this.props.updatePaymentMethods(this.state.accepted_payment_methods)
    }

    render() {
        return html`
            <div class="openingHoursStep">
                <div class="form-group">
                    <label>Accepted Payment Methods</label>
                    <${PaymentMethodSelect} defaultValue=${this.state.accepted_payment_methods} isMulti onChange=${this.onChange.bind(this)} />
                </div>
                ${this.props.data._id == null && html`<${StepperComp} onNext=${this.onNext.bind(this)} />`}
            </div>
        `
    }
}
export default connect('data', store.actions)(SupportedPaymentMethodStep)
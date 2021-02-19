import {Component, html} from 'htm/preact/standalone'
import {connect} from 'unistore/preact'
import store from './store'
import Loader from 'react-loader-spinner'

class StepperComp extends Component {

    onNext() {
        let toCall = this.props.nextStep
        if(this.props.currentStep == this.props.totalSteps) {
            toCall = () => {
                this.props.setSubmitting(true)
                this.props.submit()
            }
        }
        if(this.props.onNext) {
            if(this.props.onNext()) {
                toCall()
            }
        } else {
            toCall()
        }
    }

    onPrev() {
        if(this.props.onPrev) {
            if(this.props.onPrev()) {
                this.props.prevStep()
            }
        } else {
            this.props.prevStep()
        }
    }

    render({ currentStep, totalSteps, submitting }) {
        if (!submitting) {
            const nextStepBtn = html`
                <button class="btn btn-primary" disabled=${this.props.disabled} onclick=${this.onNext.bind(this)}>
                    Next <i class="fa fa-arrow-right"></i>
                </button>
            `
            const prevStepBtn = html`
                <button class="btn btn-secondary" disabled=${this.props.disabled} onclick=${this.onPrev.bind(this)}>
                    <i class="fa fa-arrow-left"></i> Previous 
                </button>
            `

            return html`
                <div class="stepperWrapper">
                    ${currentStep > 1 && prevStepBtn}
                    ${nextStepBtn} 
                    <button class="btn btn-default pull-right" onclick=${() => this.props.reset()}>Reset</button>
                </div>
            `
        } else {
            return html`
                <div class="stepperWrapper">
                    <${Loader} type="Rings" color="#ddd" height=${80} width=${80} />
                </div>
            `
        }

    }
}

export default connect(['currentStep', 'totalSteps', 'submitting'], store.actions)(StepperComp)



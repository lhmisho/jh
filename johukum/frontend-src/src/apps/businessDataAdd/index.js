import {Component, render, html} from 'htm/preact/standalone'
import { Provider, connect } from 'unistore/preact'
import LocationStep from './locationStep'
import ContactStep from './contactStep'
import OpeningHoursStep from './openingHoursStep'
import SupportedPaymentMethodStep from './supportedPaymentMethodStep'
import AboutCompanyStep from './aboutCompanyStep'
import CategoriesStep from './categoriesStep'
import App from '../core'
import store  from './store'

const STEP_HANDLERS = [
    LocationStep,
    ContactStep,
    OpeningHoursStep,
    SupportedPaymentMethodStep,
    AboutCompanyStep,
    CategoriesStep
]


class BusinessDataAddComp extends Component {

    render({ currentStep, totalSteps, errorMessage }) {
        const debug = false
        return html`
            <div class="row">
                <div class="col-md-8 col-md-offset-2">
                    <div class="box box-info">
                        <div class="box-header">
                            <h3 class="box-title">Step ${currentStep}</h3>
                        </div>
                        <div class="box-body">
                            ${errorMessage != null && html`<div class="alert alert-error">${errorMessage}</div>`}
                            <${STEP_HANDLERS[currentStep-1]} />        
                        </div>
                    </div>
                    ${debug && html`<pre>${JSON.stringify(this.props.data, null, 2)}</pre>`}
                </div>
            </div>
        `
    }
}


export default class BusinessDataAdd extends App {

    renderApp(elem) {
        render(html`
            <${Provider} store=${store.store}>
                <${this.getApp()} isAdmin=${window.config.user.is_admin} />
            <//>`, elem)
    }
    
    getApp() {
        return connect(['currentStep', 'totalSteps', 'errorMessage', 'data'], store.actions)(BusinessDataAddComp)
    }
}
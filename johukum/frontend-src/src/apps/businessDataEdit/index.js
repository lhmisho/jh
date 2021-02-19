import {Component, render, html} from 'htm/preact/standalone'
import { Provider, connect } from 'unistore/preact'
import LocationStep from '../businessDataAdd/locationStep'
import ContactStep from '../businessDataAdd/contactStep'
import OpeningHoursStep from '../businessDataAdd/openingHoursStep'
import SupportedPaymentMethodStep from '../businessDataAdd/supportedPaymentMethodStep'
import AboutCompanyStep from '../businessDataAdd/aboutCompanyStep'
import CategoriesStep from '../businessDataAdd/categoriesStep'
import App from '../core'
import store  from '../businessDataAdd/store'

const TAB_HANDLERS = [
    LocationStep,
    ContactStep,
    OpeningHoursStep,
    SupportedPaymentMethodStep,
    AboutCompanyStep,
    CategoriesStep
]

const TABS = [
    'Location',
    'Contact',
    'Opening Hours',
    'Payment Methods',
    'About Company',
    'Categories'
]


class BusinessDataEditComp extends Component {

    componentWillMount() {
        this.setState({
            currentTab: 0
        })
        this.props.load(this.props.extra.id)
    }

    changeTab(idx) {
        return (e) => {
            if(idx != this.state.currentTab) {
                this.setState({
                    currentTab: idx
                })
            }
        }
    }

    update() {
        this.props.setSuccess(null)
        this.props.submit(true)
    }


    render({ errorMessage, successMessage }) {

        const tab_menu = html`
            <ul class="nav nav-pills nav-stacked">
                ${TABS.map((item, i) => {
                    return html`
                        <li class="${ i == this.state.currentTab && "active"}"><a href="#" onclick=${this.changeTab(i).bind(this)}>${item}</a></li>
                    `
                })}
            </ul>
        `

        const debug = false
        return html`
            <div class="row">
                <div class="col-md-3">
                    ${tab_menu}
                </div>
                <div class="col-md-9">
                    ${successMessage != null && html`<div class="alert alert-success">${successMessage}</div>`}
                    <div class="box box-info">
                        <div class="box-header">
                            <h3 class="box-title">${TABS[this.state.currentTab]}</h3>
                        </div>
                        <div class="box-body">
                            ${errorMessage != null && html`<div class="alert alert-error">${errorMessage}</div>`}
                            <${TAB_HANDLERS[this.state.currentTab]} />
                        </div>
                    </div>
                    <div class="clearfix">
                        <button type="button" class="btn btn-lg btn-primary margin-bottom pull-right" onclick=${this.update.bind(this)}>Update</button>
                        <a class="btn btn-lg margin-bottom margin-r-5 pull-left" href=${"/dashboard/data/" + this.props.extra.id + "/"}>Go Back</a>
                    </div>
                    ${debug && html`<pre>${JSON.stringify(this.props.data, null, 2)}</pre>`}
                </div>
            </div>
        `
    }
}


export default class BusinessDataAdd extends App {

    renderApp(elem, extra) {
        window.store = store.store
        render(html`
            <${Provider} store=${store.store}>
                <${this.getApp()} isAdmin=${window.config.user.is_admin} extra=${extra} />
            <//>`, elem)
    }

    getApp() {
        return connect(['errorMessage', 'successMessage', 'id', 'data'], store.actions)(BusinessDataEditComp)
    }
}
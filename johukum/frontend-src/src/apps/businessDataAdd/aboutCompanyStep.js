import {Component, html} from 'htm/preact/standalone'
import produce from 'immer'
import {connect} from 'unistore/preact'
import Select from 'react-select'
import AnnualTurnoverSelect from '../../components/annualTurnoverSelect'
import NumberOfEmployeeSelect from '../../components/numberOfEmployeeSelect'
import ProfessionalAssociationSelect from '../../components/professionalAssociationSelect'
import CertificationSelect from '../../components/certificationSelect'
import StepperComp from './stepper'
import linkstate from 'linkstate'
import store from './store'

const CURRENT_YEAR = new Date().getFullYear()
const YEAR_SELECT = new Array(CURRENT_YEAR - 1700 + 1).fill().map((d, i) => i + 1700).map(item => {
    return {value: item, label: item}
})

class AboutCompanyStep extends Component {

    componentWillMount() {
        this.setState({
            data: {
                year_of_establishment: this.props.data.year_of_establishment,
                annual_turnover: this.props.data.annual_turnover,
                no_of_employees: this.props.data.no_of_employees,
                professional_associations: this.props.data.professional_associations,
                certifications: this.props.data.certifications,
                description: this.props.data.description
            }
        })
    }

    isValid() {
        return this.state.data.description != null
    }

    getDefaultSelectedYear() {
        let filtered = YEAR_SELECT.filter(item => item.value == this.state.year_of_establishment)
        return filtered.length > 0? filtered[0] : YEAR_SELECT[YEAR_SELECT.length-1]
    }

    onNext() {
        if(this.isValid()) {
            this.props.setError(null)
            this.props.updateCompanyInfo(this.state.data)
            return true
        } else {
            this.props.setError('Description is required')
            return false
        }
    }

    onChange(key) {
        return (val) => {
            let state = {}
            state[key] = val
            this.setState(state)
            this.props.updateCompanyInfo(this.state.data)
        }
    }
    render() {
        let linkstatewrap = (...args) => {
            const ls = linkstate(...args).bind(this)
            return (...params) => {
                ls(...params)
                this.props.updateCompanyInfo(this.state.data)
            }
        }
        return html`
            <div class="openingHoursStep">
                <div class="form-group">
                        <label>Year Of establishment</label>
                        <${Select} onChange=${linkstatewrap(this, 'data.year_of_establishment', 'value')} defaultValue=${this.getDefaultSelectedYear()} options=${YEAR_SELECT} />
                </div>
                <div class="form-group">
                    <label>Annual Turnover</label>
                    <${AnnualTurnoverSelect} defaultValue=${this.state.data.annual_turnover} onChange=${linkstatewrap(this, 'data.annual_turnover')} />
                </div>
                <div class="form-group">
                    <label>No. of Employees</label>
                    <${NumberOfEmployeeSelect} defaultValue=${this.state.data.no_of_employees} onChange=${linkstatewrap(this, 'data.no_of_employees')} />
                </div>
                <div class="form-group">
                    <label>Professional associations</label>
                    <${ProfessionalAssociationSelect} defaultValue=${this.state.data.professional_associations} onChange=${linkstatewrap(this, 'data.professional_associations')} defaultOptions isMulti />    
                </div>
                <div class="form-group">
                    <label>Certifications</label>
                    <${CertificationSelect} defaultValue=${this.state.data.certifications} onChange=${linkstatewrap(this, 'data.certifications')} defaultOptions isMulti />
                </div>
                <div class="form-group">
                    <label>Description *</label>
                    <textarea class="form-control" value=${this.state.data.description} oninput=${linkstatewrap(this, 'data.description')}></textarea>
                </div>
                
                ${this.props.data._id == null && html`<${StepperComp} onNext=${this.onNext.bind(this)} />`}
             
            </div>
        `
    }
}

export default connect('data', store.actions)(AboutCompanyStep)
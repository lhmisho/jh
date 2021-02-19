import {Component, html} from 'htm/preact/standalone'
import linkstate from 'linkstate'
import produce from 'immer'
import {connect} from 'unistore/preact'
import store from './store'
import Select from 'react-select';
import OpenCloseComp from './openCloseComp'
import StepperComp from './stepper'
import { is_equivalent } from '../../helper'

function jsUcfirst(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
const DAYS_CHOICES = DAYS.map(item => {
    return { value: item, label: jsUcfirst(item)}
})

const EDIT_METHOD_CHOICES = [
    { value: 'common', label: 'Same all Workdays'},
    { value: 'separate', label: 'Different for each Workdays'}
]
class OpeningHours extends Component {

    componentWillMount() {
        this.setState({
            data: this.props.data.hours_of_operation,
            weekends: [],
            editMethod: null,
        })
        this.setWeekendsFromProps(this.props.data.hours_of_operation)
        this.setEditMethod() // this should be called after setWeekendsFromProps
    }

    isValid() {
        return true
    }

    setWeekendsFromProps(data) {
        let weekends = []
        DAYS.map(item => {
            if(data[item].close) {
                weekends.push({ value: item, label: jsUcfirst(item)})
            }
        })
        this.setState({
            weekends: weekends.length > 0 ? weekends : []
        })
    }

    getWorkingDays() {
        const weekends = new Set(this.state.weekends.map(item => {
            return item.value
        }))
        return DAYS.filter(item => {
            return !weekends.has(item)
        })
    }

    onOpenCloseChange(day) {
        return (data) => {
            this.setState(produce(this.state, draft => {
                if (day == 'common') {
                    this.getWorkingDays().map(item => {
                        draft.data[item] = data
                    })
                } else {
                    draft.data[day] = data
                }
            }))
            this.updateHop()
        }
    }

    getDayDataKey(day) {
        if(day=='common') {
            const wd = this.getWorkingDays()
            if(wd.length > 0) return wd[0]
            else return 'sunday' // i don't know what to do in this case. hope this does not happen
        }
        else return day
    }
    buildEditorFor(day) {
        return html`
            <div class="box box-default">
                <div class="box-header">
                    <h3 class="box-title">${jsUcfirst(day)}</h3>
                </div>
                <div class="box-body">
                    <${OpenCloseComp} value=${this.state.data[this.getDayDataKey(day)]} onChange=${this.onOpenCloseChange(day).bind(this)}/>
                </div>
            </div>
        `
    }

    updateHop() {
        const wd = this.getWorkingDays()

        if(wd.length > 0) {
            this.setState(produce(this.state, draft => {
                wd.map(item => {
                    draft.data[item].close = false
                })
            }))
        }

        if(this.state.editMethod.value == 'common'){
            if(wd.length > 0) {
                this.setState(produce(this.state, draft => {
                    wd.map(item => {
                        draft.data[item] = this.state.data[wd[0]]
                    })
                }))
            }
        }


        this.setState(produce(this.state, draft => {
            this.state.weekends.map(item => {
                draft.data[item.value].close = true
            })
        }))
        this.props.updateHop(this.state.data)
    }

    onNext() {
        this.updateHop()
        return true
    }

    setEditMethod() {
            const workingDays = this.getWorkingDays()
            console.log(workingDays)
            const isSame = workingDays.reduce((result, item) => {
                if(this.state.data[item].close) return result
                const isEqual = is_equivalent(this.state.data[item], this.state.data[workingDays[0]])
                return isEqual && result
            }, true)
            if(isSame) return this.setState({ editMethod: EDIT_METHOD_CHOICES[0] })
            else return this.setState({ editMethod: EDIT_METHOD_CHOICES[1] })

    }

    componentWillReceiveProps(nextProps) {
        this.setWeekendsFromProps(nextProps.data.hours_of_operation)
        this.setEditMethod()
    }

    render() {
        let workingDays = this.buildEditorFor('common')

        if (this.state.editMethod.value == 'separate') {
            workingDays = this.getWorkingDays().map(item => this.buildEditorFor(item))
        }

        let linkstatewrap = (...args) => {
            const ls = linkstate(...args).bind(this)
            return (...params) => {
                ls(...params)
                this.updateHop(this.state.data)
            }
        }
        console.log(this.state)
        return html`
            <div class="openingHoursStep">
                <div class="form-group">
                    <label>Weekends</label>
                    <${Select} isMulti options=${DAYS_CHOICES} onChange=${linkstatewrap(this, 'weekends')} defaultValue=${this.state.weekends} />
                </div>
                <div class="form-group">
                    <label> Edit Method </label>
                    <${Select} options=${EDIT_METHOD_CHOICES} onChange=${linkstatewrap(this, 'editMethod')} defaultValue=${this.state.editMethod} />
                </div>
             
                ${workingDays}
                
                ${this.props.data._id == null && html`<${StepperComp} onNext=${this.onNext.bind(this)} />`}
                
            </div>
        `
    }
}


export default connect('data', store.actions)(OpeningHours)
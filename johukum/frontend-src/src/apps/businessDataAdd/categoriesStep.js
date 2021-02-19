import {Component, html} from 'htm/preact/standalone'
import {connect} from 'unistore/preact'
import CategorySelect from '../../components/categorySelect'
import linkstate from 'linkstate'
import store from './store'
import StepperComp from './stepper'

class CategoriesStep extends Component {

    componentWillMount() {
        this.setState({
            keywords: this.props.data.keywords
        })
    }

    onNext() {
        this.props.updateKeywords(this.state.keywords)
        return true
    }

    onChange(val) {
        this.setState({ keywords: val })
        this.props.updateKeywords(this.state.keywords)
    }

    render() {
        return html`
            <div class="openingHoursStep">
                <div class="form-group">
                    <label>Categories</label>
                    <${CategorySelect} isMulti defaultValue=${this.state.keywords} onChange=${this.onChange.bind(this)} />
                </div>
                ${this.props.data._id == null && html`<${StepperComp} onNext=${this.onNext.bind(this)} />`}
            </div>
        `
    }
}

export default connect('data', store.actions)(CategoriesStep)
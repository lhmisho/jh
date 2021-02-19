import {Component, html} from 'htm/preact/standalone'
import CategorySelect from '../../components/categorySelect'
import LocationWidget from '../../components/locationWidget'
import AgentSelect from '../../components/agentSelect'
import DateRangePicker from 'react-bootstrap-daterangepicker'
import 'bootstrap-daterangepicker/daterangepicker.css'
import linkstate from 'linkstate'
import Select from 'react-select'

const STATUS_FILTER = [
    {value: 0, label: 'Rejected'},
    {value: 1, label: 'Pending'},
    {value: 2, label: 'Reviewed'},
    {value: 3, label: 'Approved'}
]

export default class BusinessDataFilterWidget extends Component {

    componentWillMount() {
        this.setState({
            location: null,
            category: null,
            status: null,
            business_name: null,
            username: null,
            mobile_numbers: null,
            start_date: null,
            end_date: null,
            area: null,

        })
    }

    filter() {
        if (this.props.onChange) {
            this.props.onChange(this.state)
        }
    }

    statusChanged(item) {
        this.setState({
            status: item.value
        })
    }

    handleEvent(event, item) {
        this.setState({
            start_date: item.startDate,
            end_date: item.endDate
        })
        var start_month = new Date(item.startDate).getMonth();
        var end_month = new Date(item.endDate).getMonth();
        start_month = start_month + 1;
        end_month = end_month + 1;

        var sd = new Date(item.startDate).getDate() + "/" + start_month + "/" + new Date(item.startDate).getFullYear()
        var ed = new Date(item.endDate).getDate() + "/" + end_month + "/" + new Date(item.endDate).getFullYear()
        document.getElementById('inp').value = sd + " - " + ed

    }

    render() {
        return html`
            <div class="box box-info">
                <div class="box-body">
                    <div class="row">
                        <div class="form-group col-md-12">
                            <${LocationWidget} onChange=${linkstate(this, 'location')} />
                        </div>
                        <div class="form-group col-md-4">
                            <label>Category</label>
                            <${CategorySelect} onChange=${linkstate(this, 'keyword')} />
                        </div>
                        <div class="form-group col-md-4">
                            <label>Status</label>
                            <${Select} onChange=${this.statusChanged.bind(this)} options=${STATUS_FILTER} />
                        </div>
                        <div class="form-group col-md-4">
                            <label>Business Name</label>
                            <input type="text" onchange=${linkstate(this, 'business_name')} class="form-control"/>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="form-group col-md-4">
                            <label>Agent Name</label>
                            <${AgentSelect} onChange=${linkstate(this, 'username')} />
                        </div> 
                        <div class="form-group col-md-4">
                            <label>Mobile Number(Without +88)</label>
                            <input type="text" placeholder="Please put number without +88" onchange=${linkstate(this, 'mobile_numbers')} class="form-control"/>
                        </div>  
                        <div class="form-group col-md-4">
                            <label style="display: block">Select Date</label>
                            <${DateRangePicker} onApply=${this.handleEvent.bind(this)} >
                                <input id="inp" class="form-control">Select Date</input>
                            </{DateRangePicker}>
                        </div>
                    </div>
                    <div class="row">
                        <div class="form-group col-md-4">
                            <label>Area</label>
                            <input type="text" onchange=${linkstate(this, 'area')} class="form-control"/>
                        </div> 
                    </div>
                </div>
                <div class="box box-footer">
                    <button type="button" class="btn btn-primary btn-sm pull-right" onclick=${this.filter.bind(this)}>
                        <i class="fa fa-filter"></i> Filter
                    </button>
                </div>
            </div>
        `
    }
}
import {Component, html} from 'htm/preact/standalone'
import axios from 'axios'
import App from '../core'
import produce from 'immer'
import linkstate from 'linkstate'
import ImageUpload from '../../components/imageUpload'

class FileUploadComp extends Component {

    componentWillMount() {
        this.setState({
            data: {
                location: {
                    business_name: null
                }
            }
        })
        this.getDetails(this.props.extra.pk)
    }

    getDetails(pk) {
        axios.get('/api/v2/business_data/' + pk + '/').then(resp => {
            this.setState(produce(this.state, draft => {
                draft.data = resp.data
            }))
        })
    }

    render() {
       return html`
        <div class="row">
            <div class="col-md-8 col-md-offset-2">
                <div class="box box-default">
                    <div class="box-header">
                        <div class="box-title">Files for ${this.state.data.location.business_name}</div>
                    </div>
                    <div class="box-body">
                        <${ImageUpload} defaultValue=${this.state.data.photos} onChange=${linkstate(this, 'data.photos')} />
                    </div>
                </div>
            </div>
        </div>
       `
    }
}

export default class BusinessDataFileUpload extends App {
    getApp() {
        return FileUploadComp
    }
}
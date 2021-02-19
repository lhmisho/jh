import {Component, html} from 'htm/preact/standalone'
import produce from 'immer'
import {connect} from 'unistore/preact'
import StepperComp from './stepper'
import linkstate from 'linkstate'
import store from './store'
import ImageUpload from '../../components/imageUpload'
import axios from "axios/index";
import is from 'is_js'

class FileUploadStep extends Component {

    componentWillMount() {
        this.setState({
            message: null,
            stepperDisabled: false,
            data: {
                photos: this.props.data.photos,
                logo: null,
                cover_photo: null,
                embed_video: null
            }
        })
    }

    stepperDisabled() {
        this.setState({
            stepperDisabled: true
        })
    }

    stepperEnabled() {
        this.setState({
            stepperDisabled: false
        })
    }

    uploadLogoAndCoverPhoto(data) {
        let formData = new FormData()
        formData.append("logo", this.logo.files[0])
        formData.append("cover_photo", this.cover_photo.files[0])
        axios.post('/api/v2/business_data/upload/' + data._id + "/", formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
        }).then(resp => {
            window.location.href = '/dashboard/data/'+ resp.data._id +'/'
        }).catch(error => {
            console.error("Unable to upload data", error)
            window.location.href = '/dashboard/data/'+ resp.data._id +'/'
        })
    }

    submit(data) {
        axios.post('/api/v2/business_data/create/', data)
            .then(resp => {
              this.uploadLogoAndCoverPhoto(resp.data)
            })
            .catch(error => {
                console.error("Unable to save", error)
                console.log(error.response.data)
                if(is.object(error.response.data)) {
                    this.setState({
                        message: Object.entries(error.response.data).map(entry => {
                            return html`
                                <li>${entry[1]}</li>
                            `
                        })
                    })
                } else {
                    this.setState({
                        message: 'Unable to save! Please report this issue'
                    })
                }
                this.stepperEnabled()
            })
    }

    onNext() {
        this.stepperDisabled()
        this.props.updateFiles(this.state.data)
        this.submit(this.props.data)
        this.setState({ message: null })
        return false
    }

    render() {
        return html`
            <div class="openingHoursStep">
                ${this.state.message && html`
                    <div class="alert alert-error">
                        <p>${this.state.message}</p>
                    </div>
                `}
                <div class="form-group">
                    <label>Logo</label>
                    <input type="file" class="form-control" accept="image/*" ref=${ref => {this.logo = ref}} />
                </div>
                <div class="form-group">
                    <label>Cover Photo</label>
                    <input type="file" class="form-control" accept="image/*" ref=${ref => {this.cover_photo = ref}} />
                </div>
                <div class="form-group" style="position: relative; height: auto;">
                    <label>Images</label>
                    <${ImageUpload} onChange=${linkstate(this, 'data.photos')} />
                </div>
                <div class="form-group">
                    <label>Video</label>
                    <input type="url" class="form-control" oninput=${linkstate(this,'data.embed_video')} />
                </div>
                ${this.props.data._id == null && html`<${StepperComp} disabled=${this.state.stepperDisabled} onNext=${this.onNext.bind(this)} />`}
            </div>
        `
    }
}
export default connect('data', store.actions)(FileUploadStep)
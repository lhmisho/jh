import {Component, html} from 'htm/preact/standalone'
import { FilePond, registerPlugin } from "react-filepond";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import FilePondPluginFileValidateType from 'filepond-plugin-file-validate-type';
import FilePondPluginImageResize from 'filepond-plugin-image-resize';

import axios from 'axios'
import produce from 'immer'

// Import FilePond styles
import "filepond/dist/filepond.min.css";
import "filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css";

registerPlugin(
    FilePondPluginImagePreview,
    FilePondPluginFileValidateType,
    FilePondPluginImageResize
)

export default class ImageUpload extends Component {

    constructor(props) {
        super(props);
        this.state = {
            files: [],
            uploadedIDs: []
        }
    }

    componentWillReceiveProps(nextProps, nextState) {
        if(nextProps.defaultValue && this.state.files.length == 0) {
            this.setState(produce(this.state, draft => {
                draft.files = nextProps.defaultValue.map(item => {
                    return {
                        source: item,
                        options: {
                            type: 'local'
                        },
                        file: {
                    name: 'my-file.png',
                    size: 3001025,
                    type: 'image/png'
                }
                    }
                })
            }))
        }

        console.log(this.state)
    }

    uploaded(resp) {
        this.setState(produce(this.state, draft => {
            draft.uploadedIDs.push(resp._id)
        }))
        if(this.props.onChange) {
            this.props.onChange(this.state.uploadedIDs)
        }
    }

    getServerConfig() {
        return {
            load:'/api/v2/upload/image/',
            process:(fieldName, file, metadata, load, error, progress, abort) => {
                    // fieldName is the name of the input field
                // file is the actual file object to send
                const formData = new FormData();
                formData.append('image', file, file.name);

                const request = new XMLHttpRequest();
                // request.setRequestHeader('content-type', 'multipart/form-data')
                request.open('POST', '/api/v2/upload/images/');

                // Should call the progress method to update the progress to 100% before calling load
                // Setting computable to false switches the loading indicator to infinite mode
                request.upload.onprogress = (e) => {
                    progress(e.lengthComputable, e.loaded, e.total);
                };

                // Should call the load method when done and pass the returned server file id
                // this server file id is then used later on when reverting or restoring a file
                // so your server knows which file to return without exposing that info to the client
                request.onload = () => {
                    if (request.status >= 200 && request.status < 300) {
                        // the load method accepts either a string (id) or an object
                        this.uploaded(JSON.parse(request.responseText))
                        load(request.responseText);
                    }
                    else {
                        // Can call the error method if something is wrong, should exit after
                        error('oh no');
                    }
                };

                request.send(formData);

                // Should expose an abort method so the request can be cancelled
                return {
                    abort: () => {
                        // This function is entered if the user has tapped the cancel button
                        request.abort();

                        // Let FilePond know the request has been cancelled
                        abort();
                    }
                };
            }
        }
    }

    onupdatefiles (fileItems) {
        this.setState({
          files: fileItems.map(fileItem => fileItem.file)
        })
        console.log(this.state)
    }

    render() {
        return html`
                <${FilePond}
                  files=${this.state.files}
                  allowMultiple=${true}
                  maxFiles=${10}
                  server=${this.getServerConfig()}
                  instantUpload=${false}
                  onupdatefiles=${this.onupdatefiles.bind(this)},
                  acceptedFileTypes=${['image/png', 'image/jpeg', 'image/jpg']}
                />
        `
    }
}
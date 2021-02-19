import {html} from 'htm/preact/standalone'
import axios from 'axios'
import App from '../core'
import Loader from 'react-loader-spinner'
import { AbstractListComp } from '../core'
import BusinessDataFilterWidget from '../businessDataList/businessDataFilterWidget'

class MobileDataListComp extends AbstractListComp {

    getData() {
        this.setUrl()
        this.loading(true)
        axios.get('/api/v2/mobile_number_data/', {
            params: this.state.hashParams
        }).then(resp => {
            console.log(resp.data)
            this.setState({
                data: resp.data
            })
            this.loading(false)
        }).catch(error => {
            this.loading(false)
            console.error("unable to load data", error)
        })
    }

    buildStatus(status) {
        if(status == 0) {
            return this.buildBadge('REJECTED', 'danger')
        } else if (status == 1) {
            return this.buildBadge('PENDING', 'warning')
        } else if (status == 2) {
            return this.buildBadge('REVIEWED', 'info')
        } else if (status == 3) {
            return this.buildBadge('APPROVED', 'success')
        }
    }

    deleteItem(id) {
        return (e) => {
            e.preventDefault()
            if(confirm('Are you sure you want to delete this?')) {
                window.location.href = '/dashboard/mobile-data-delete/'+ id + '/'
            }
        }
    }

    render({}, {data}) {
        const dataRows = data.results.map(item => {
            return html`
                <tr>
                    <td>${item.store_name}</td>
                    <td>${item.name}</td>
                    <td>${item.added_by && item.added_by.username}</td>
                    <td>${this.buildStatus(item.status)}</td>
                    <td>
                        <div class="btn-group">
                            <a class="btn btn-xs btn-info" href=${'/dashboard/mobile-data/' + item._id + '/'}>View</a>
                            <a class="btn btn-xs btn-primary" href=${'/dashboard/mobile-data-update/'+ item._id + '/'}>Update</a>
                            ${this.props.isAdmin && html`
                                <button onclick=${this.deleteItem(item._id).bind(this)} class="btn btn-xs btn-default text-danger">Delete</button>
                            `}
                        </div>
                    </td>
                </tr>
            `
        })
        return html`
            <div class="row">
                <div class="col-xs-12">
                    <${BusinessDataFilterWidget} onChange=${this.filter.bind(this)} />
                    <div class="box box-default">
                        <div class="box-header">
                            <h3 class="box-title">Mobile Number Data</h3>
                            <div class="box-tools">
                                <a class="btn btn-primary btn-sm" href="/dashboard/mobile-data/create">
                                    <i class="fa fa-plus"></i> Add New
                                </a>
                            </div>
                            <div class="box-body table-responsive no-padding">
                                ${this.state.loading && html`<${Loader}type="Rings" color="#ddd" height=${80}width=${80}/>`}
                                ${!this.state.loading && html`
                                    ${dataRows.length > 0 && html`
                                        <table class="table table-hover">
                                            <thead>
                                                <tr>
                                                    <th scope="col">Organaization Name</th>
                                                    <th scope="col">Name</th>
                                                    <th scope="col">Added By</th>
                                                    <th scope="col">Status</th>
                                                    <th scope="col">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody>${dataRows}</tbody>
                                        </table>
                                    `}
                                    ${dataRows.length == 0 && html`
                                        <p class="text-center">No data found!</p>
                                    `}
                                `}
                            </div>
                            ${!this.state.loading && dataRows.length > 0 && html`
                                <div class="box-footer">
                                    ${this.buildPagination(20, data.count, this.state.hashParams.page)}
                                </div>
                            `}
                            </div>
                        </div>
                    </div>
                </div>`
    }
}

export default class MobileDataList extends App {
    getApp() {
        return MobileDataListComp
    }
}
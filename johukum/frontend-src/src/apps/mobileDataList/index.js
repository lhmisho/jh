import {html} from 'htm/preact/standalone'
import axios from 'axios'
import BusinessDataFilterWidget from '../businessDataList/businessDataFilterWidget'
import Loader from 'react-loader-spinner'
import dayjs from 'dayjs'
import { AbstractListComp } from '../core'
import App from '../core'

class MobileDataListComp extends AbstractListComp {

    getData() {
        this.setUrl()
        this.loading(true)
        axios.get('/api/v2/mobile_number_list/', {
            params: this.state.hashParams
        }).then(resp => {
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
            if(confirm('Are you sure you want to delete?')) {
                window.location.href = '/dashboard/mobile-data-delete/'+ id + '/'
            }
        }
    }

    render({}, {data}) {
        let dataRows = []
        for(let i = 0; i<data.results.length; i++) {
            const modified_date = dayjs(data.results[i].modified_at).format('MMMM DD, YYYY - h:mm A')
            dataRows.push(html`
                <tr>
                    <td>${data.results[i].store_name}</td>
                    <td>${data.results[i].name}</td>
                    <td>${data.results[i].added_by.username}</td>
                    <td>${data.results[i].edit_by.username}</td>
                    <td>${this.buildStatus(data.results[i].status)}</td>
                    <td>${modified_date}</td>
                    <td>
                        <div class="btn-group">
                            <a class="btn btn-xs btn-info" href=${'/dashboard/mobile-data/' + data.results[i]._id + '/'}>View</a>
                            ${this.props.isAdmin && html`
                                <button onclick=${this.deleteItem(data.results[i]._id).bind(this)}class="btn btn-xs btn-default text-danger">Delete</button>
                            `}
                        </div>
                    </td>
                        </tr>
            `)
        }
        return html`
            
            <div class="row">
                
                <div class="col-xs-12">
                    <${BusinessDataFilterWidget} onChange=${this.filter.bind(this)} />
                    <div class="box">
                        <div class="box-header">
                            <h3 class="box-title">Mobile number data</h3>
                            <div class="box-tools">
                                <a href="/dashboard/mobile-data/create" class="btn btn-sm btn-primary">
                                    <i class="fa fa-plus"></i> Add New
                                </a>
                            </div>
                        </div>
                        <div class="box-body table-responsive no-padding">
                            ${this.state.loading && html`<${Loader} type="Rings" color="#ddd" height=${80} width=${80} />`}
                            ${!this.state.loading && html`
                                ${dataRows.length > 0 && html`
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Business Name</th>
                                                <th>Name</th>
                                                <th>Added By</th>
                                                <th>Modified By</th>
                                                <th>Status</th>
                                                <th>Modified At</th>
                                                <th>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${dataRows}
                                        </tbody>
                                    </table>
                                `}
                                ${dataRows.length == 0 && html`
                                    <p class="text-center">No data found!</p>
                                `}
                            `}
                        </div>
                        ${!this.state.loading && dataRows.length > 0 && html`
                            <div class="box-footer">
                                ${this.buildPagination(data.per_page, data.total, data.page)}
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `
    }
}

export default class MobileDataList extends App{
    getApp(){
        return MobileDataListComp
    }
}
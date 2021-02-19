import {render, html, Component} from 'htm/preact/standalone'
import {paginate_helper} from "../helper";
import produce from "immer/dist/immer";
import queryString from 'querystring'

export default class App {

    constructor(elem, extraProps) {
        this.ajaxInterceptor()
        this.renderApp(elem, extraProps)
    }

    getApp() {
        throw new Error("Not implemented")
    }

    renderApp(elem, extraProps) {
        render(html`<${this.getApp()} isAdmin=${window.config.user.is_admin} extra=${extraProps} />`, elem)
    }

    ajaxInterceptor() {
        ((send) => {
            XMLHttpRequest.prototype.send = function(data) {
                this.setRequestHeader('X-CSRFToken', window.config.csrf_token);
                send.call(this, data);
            };
        })(XMLHttpRequest.prototype.send)
    }
}


export class AbstractListComp extends Component{

    componentWillMount() {
        this.setState({
            data: {
                total: 0,
                results: []
            },
            hashParams: {
                page: 1
            },
            loading: false
        })
    }

    paginate(page) {
        return () => {
            this.setState(produce(this.state, draft => {
                draft.hashParams.page = page
            }))
            this.getData()
        }
    }

    buildPagination(perPage, total, currentPage) {
        let pagination = paginate_helper(total, currentPage, perPage)
        let page_links = []
        for(let i = 0; i<pagination.pages.length; i++) {
            page_links.push(html`
                <li class="${currentPage == pagination.pages[i] && "active"}">
                    <a href="javascript:;" onclick=${this.paginate(pagination.pages[i])}>${pagination.pages[i]}</a>
                </li>
            `)
        }
        return html`
            <ul class="pagination pagination-sm no-margin">
                ${page_links.length > 0 && html`
                    <li>
                        <a href="javascript:;" onclick=${this.paginate(1)}>First</a>
                    </li>
                    ${page_links}
                    <li>
                        <a href="javascript:;" onclick=${this.paginate(pagination.totalPages)}>Last</a>
                    </li>
                `}
            </ul>
        `
    }

    componentDidMount() {
        const params = queryString.parse(location.hash.replace('#', ''))
        this.setState(produce(this.state, draft => {
            draft.hashParams = {
                ...this.state.hashParams,
                ...params
            }
        }))
        this.getData()
    }

    loading(isLoading) {
        this.setState({
            loading:isLoading
        })
    }

    setUrl() {
        let params = produce(this.state.hashParams, draft => {})
        window.location.hash = queryString.stringify(params)
    }

    getData() {
        throw new Error('Get data must be implemented')
    }

    buildBadge(text, type) {
        return html`<span class=${"label label-" + type}>${text.toUpperCase()}</span>`
    }

    filter(params) {
        this.setState(produce(this.state, draft => {
            draft.hashParams = {
                ...this.state.hashParams,
                ...params
            }
            draft.hashParams.page = 1
        }))
        this.getData()
    }
}
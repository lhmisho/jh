import createStore from 'unistore'
import produce from 'immer'
import axios from 'axios'
import * as pstore from 'store'
import {html} from "htm/preact/standalone";
import is from 'is_js'

const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
let statesForEachDay = {}
DAYS.map(item => {
    statesForEachDay[item] = {
        open_from: "09:00",
        open_till: "17:00",
        leisure_start: "13:00",
        leisure_end: "14:00",
        open_24h: false,
        close: false
    }
})

const VALIDATION_ERROR_REDIRECT_STEP = {
    'contact': 2
}

const STATE = {
    id: null,
    submitting: false,
    currentStep: 1,
    totalSteps: 6,
    successMessage: null,
    errorMessage: null,
    data: {
        location: {
            business_name: null,
            building: null,
            street: null,
            land_mark: null,
            area: null,
            postcode: null,
            location_id: null,
            plus_code: null,
            geo: null
        },
        contact: {
            title: null,
            name: null,
            designation: null,
            email: null,
            mobile_no: null,
            mobile_numbers: [],
            landline_no: null,
            fax_no: null,
            website: null
        },
        hours_of_operation: {
            display_hours_of_operation: true,
            ...statesForEachDay
        },
        description: null,
        year_of_establishment: null,
        annual_turnover: null,
        no_of_employees: null,
        logo: null,
        cover_photo: null,
        embed_video: "",
        professional_associations: [],
        certifications: [],
        photos: [],
        videos: [],
        accepted_payment_methods: [],
        keywords: []
    }
}

const data = false // pstore.get('state')
let store = createStore(data? data : produce(STATE, draft=>{}))

// store.subscribe(state => {
//     console.log(state)
//     pstore.set('state', state)
// })
// actions

let actions = store => ({

    setSubmitting(state, val) {
        return produce(state, draft => {
            draft.submitting = val
        })
    },
    reset(state) {
        return produce(state, draft => {
            draft = STATE
        })
    },

    setError(state, message) {
        return produce(state, draft => {
            draft.errorMessage = message
        })
    },

    setSuccess(state, message) {
        return produce(state, draft => {
            draft.successMessage = message
        })
    },

    nextStep(state) {
      return { currentStep: state.currentStep + 1 }
    },
    prevStep(state) {
      return { currentStep: state.currentStep - 1 }
    },
    updateLocation(state, location) {
        return produce(state, draft => {
            draft.data.location = location
        })
    },
    updateContact(state, contact) {
        return produce(state, draft => {
            draft.data.contact = contact
        })
    },
    updateHop(state, hours_of_operation) {
        console.log(hours_of_operation)
        return produce(state, draft => {
            draft.data.hours_of_operation = hours_of_operation
        })
    },
    updatePaymentMethods(state, paymentMethods) {
        return produce(state, draft => {
            draft.data.accepted_payment_methods = paymentMethods
        })
    },
    updateKeywords(state, keywords) {
        return produce(state, draft => {
            draft.data.keywords = keywords
        })
    },

    updateCompanyInfo(state, data) {
        return produce(state, draft => {
            draft.data.year_of_establishment = data.year_of_establishment
            draft.data.annual_turnover = data.annual_turnover
            draft.data.no_of_employees = data.no_of_employees
            draft.data.professional_associations = data.professional_associations
            draft.data.certifications = data.certifications
            draft.data.description = data.description
        })
    },

    updateFiles(state, data){
        return produce(state, draft => {
            draft.data.photos = data.photos
            draft.data.logo = data.logo
            draft.data.cover_photo = data.cover_photo
            draft.data.embed_video = data.embed_video
        })
    },

    async submit(state, is_update=false) {

        try {
            let { data } = await axios.post('/api/v2/business_data/create/', state.data)
            if (is_update) {
                return produce(state, draft => {
                    draft.successMessage = 'Successfully Updated'
                })
            }
            else {
                window.location.href='/dashboard/data/edit/?id='+ data._id +'&wizard=files' // hack for now for file upload
            }

        } catch(err) {
            if(is.object(err.response.data)) {
                return produce(state, draft => {
                    draft.submitting = false
                    draft.errorMessage = Object.entries(err.response.data).map(entry => {

                        if (VALIDATION_ERROR_REDIRECT_STEP.hasOwnProperty(entry[0])) {
                            draft.currentStep = VALIDATION_ERROR_REDIRECT_STEP[entry[0]]
                        }

                        return html`
                            <li>${entry[1]}</li>
                        `
                    })
                })
            } else {
                return produce(state, draft => {
                    draft.submitting = false
                    draft.errorMessage = 'Unable to save! Please report this issue'
                })
            }
        }
        return state

    },

    async load(state, id) {
        let {data} = await axios.get('/api/v2/business_data/' + id + '/')
        let new_state = produce(state, draft => {

            if (data.contact.mobile_numbers) {
                data.contact.mobile_numbers = data.contact.mobile_numbers.map(item => { return item.mobile_number })
            }

            if (data.location.geo == "") data.location.geo = null

            state.data = data
        })
        return new_state
    }

})

export default { store, actions }
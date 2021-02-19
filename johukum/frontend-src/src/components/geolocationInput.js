import {Component, html} from 'htm/preact/standalone';
import {geolocated} from 'react-geolocated';

class GeoHelper extends Component {
  render({ isGeolocationAvailable, isGeolocationEnabled, coords}) {
      let message = ''
      if (isGeolocationAvailable) {
          if (isGeolocationEnabled) {
              if(coords) {
                  this.props.onCoordsChange(coords)
                  message = html`
                    <pre>
                        latitude: ${coords.latitude} <br />
                        longitude: ${coords.longitude}
                    </pre>
                  `
              }
          } else {
              message = html`<div>Geolocation is not enabled</div>`
          }
      } else {
          message = html`<div>Your browser does not support Geolocation</div>`
      }
      return html`${message}`
  }
}

const Geo = geolocated({
  positionOptions: {
    enableHighAccuracy: false,
  },
  userDecisionTimeout: 5000,
})(GeoHelper);


export default class GeoLocationInput extends Component {
    componentWillMount() {
        this.setState({
            clicked: false
        })
    }

    loaded(coords) {
        const geojson = {
            "type": "Point",
            "coordinates": [
                coords.longitude,
                coords.latitude
            ]
        }
        if (this.props.onChange) {
            this.props.onChange(geojson)
        }
    }
    componentWillReceiveProps(nextProps, nextState) {
        if (nextProps.value != null) {
            this.setState({
                clicked: false
            })
        }
    }
    render() {
        let oldval = null
        if(this.props.value != null) {
            oldval = html`
                <pre>
                    latitude: ${this.props.value.coordinates[1]} <br />
                    longitude: ${this.props.value.coordinates[0]}
                </pre>
            `
        }
        return html`
            <div class="geoWrapper row">
                <div class="col-md-6">
                    ${this.state.clicked && html`<${Geo} onCoordsChange=${this.loaded.bind(this)} />`} 
                    ${this.state.clicked == false && oldval}
                    </div>
                    <div class="col-md-6">
                        <button class="btn btn-info" onclick=${() => this.setState({ clicked:true })}>Get Current Location</button>
                    </div>
            </div>
        `
    }
}
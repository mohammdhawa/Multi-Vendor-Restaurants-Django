// custom.js - Place this in your static/assets/js/custom.js file

let autocomplete;

function initAutoComplete() {
    // Make sure the element exists before attempting to create the autocomplete
    const addressField = document.getElementById('id_address');

    if (!addressField) {
        console.error('Address field not found. Make sure the element ID is correct.');
        return;
    }

    autocomplete = new google.maps.places.Autocomplete(
        addressField,
        {
            types: ['geocode', 'establishment'],
            // Adjust country restriction as needed - currently set to India
            componentRestrictions: { 'country': ['tr'] },
        }
    );

    // Function to specify what should happen when the prediction is clicked
    autocomplete.addListener('place_changed', onPlaceChanged);
}

function onPlaceChanged() {
    var place = autocomplete.getPlace();

    // User did not select the prediction. Reset the input field
    if (!place.geometry) {
        document.getElementById('id_address').placeholder = "Start typing...";
        return;
    }

    // Log the selected place data
    console.log('place name =>', place.name);
    console.log('place data =>', place);

    // Get the address components and assign them to the fields
    const latitudeField = document.getElementById('id_latitude');
    const longitudeField = document.getElementById('id_longitude');
    const cityField = document.getElementById('id_city');
    const stateField = document.getElementById('id_state');
    const countryField = document.getElementById('id_country');
    const postalCodeField = document.getElementById('id_postal_code');

    // Set coordinates
    if (latitudeField && longitudeField) {
        latitudeField.value = place.geometry.location.lat();
        longitudeField.value = place.geometry.location.lng();
    }

    // Clear all address fields first
    if (cityField) cityField.value = '';
    if (stateField) stateField.value = '';
    if (countryField) countryField.value = '';
    if (postalCodeField) postalCodeField.value = '';

    // Extract address components
    let streetNumber = '';
    let route = '';
    let hasCity = false;
    let stateValue = '';

    for (const component of place.address_components) {
        const componentType = component.types[0];

        switch (componentType) {
            case "street_number":
                streetNumber = component.long_name;
                break;

            case "route":
                route = component.long_name;
                break;

            case "locality":
                if (cityField) {
                    cityField.value = component.long_name;
                    hasCity = true;
                }
                break;

            case "administrative_area_level_1":
                if (stateField) {
                    stateValue = component.long_name;
                    stateField.value = stateValue;
                }
                break;

            case "country":
                if (countryField) countryField.value = component.long_name;
                break;

            case "postal_code":
                if (postalCodeField) postalCodeField.value = component.long_name;
                break;
        }
    }

    // If city is empty, use state value
    if (!hasCity && cityField && stateValue) {
        cityField.value = stateValue;
    }
}

// Check if the Google Maps API has already loaded
if (typeof google === 'undefined') {
    console.warn('Google Maps API not loaded. Make sure the script is included correctly.');
} else {
    // If Google Maps API is already loaded, initialize autocomplete
    initAutoComplete();
}

// For safety, add an event listener for when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // If Google Maps API is loaded after the DOM is ready
    if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
        initAutoComplete();
    }
});



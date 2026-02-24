// Google Maps Places Autocomplete Integration for StackPOS
// Provides address autocomplete with Ireland-specific handling

// Global debug functions (used by eircode-maps-v2.js too)
window.debugLog = console.log.bind(console);
window.debugWarn = console.warn.bind(console);
window.debugError = console.error.bind(console);

window.googleMapsInterop = {
    autocomplete: null,
    map: null,
    marker: null,
    dotNetRef: null,

    /**
     * Initialize Google Places Autocomplete on an input field
     * @param {string} inputId - The ID of the input element
     * @param {object} dotNetRef - .NET object reference for callbacks
     */
    initAutocomplete: function(inputId, dotNetRef) {
        window.debugLog('Initializing Google Maps Autocomplete for:', inputId);

        const input = document.getElementById(inputId);
        if (!input) {
            window.debugError('Input element not found:', inputId);
            return;
        }

        this.dotNetRef = dotNetRef;

        // Initialize autocomplete with Ireland restrictions
        this.autocomplete = new google.maps.places.Autocomplete(input, {
            componentRestrictions: { country: 'ie' },
            types: ['address'],
            fields: ['address_components', 'geometry', 'formatted_address']
        });

        // Listen for place selection
        this.autocomplete.addListener('place_changed', () => {
            const place = this.autocomplete.getPlace();

            if (!place.geometry) {
                window.debugWarn('No geometry data for selected place');
                return;
            }

            // Extract address components
            const addressData = this.extractAddressComponents(place);

            // Send data back to Blazor
            if (this.dotNetRef) {
                this.dotNetRef.invokeMethodAsync('OnPlaceSelected', addressData)
                    .catch(err => window.debugError('Error calling OnPlaceSelected:', err));
            }
        });

        window.debugLog('Autocomplete initialized successfully');
    },

    /**
     * Extract and parse address components from Google Place object
     * @param {object} place - Google Place object
     * @returns {object} Structured address data
     */
    extractAddressComponents: function(place) {
        window.debugLog('Extracting address components from place:', place);

        const components = {};
        let streetNumber = '';
        let route = '';

        // Parse address components
        if (place.address_components) {
            place.address_components.forEach(component => {
                const types = component.types;

                if (types.includes('street_number')) {
                    streetNumber = component.long_name;
                } else if (types.includes('route')) {
                    route = component.long_name;
                } else if (types.includes('sublocality_level_1') || types.includes('sublocality')) {
                    components.address_line2 = component.long_name;
                } else if (types.includes('locality')) {
                    components.city = component.long_name;
                } else if (types.includes('postal_town') && !components.city) {
                    components.city = component.long_name;
                } else if (types.includes('administrative_area_level_1')) {
                    // Remove "County " prefix if present
                    let county = component.long_name;
                    if (county.startsWith('County ')) {
                        county = county.substring(7);
                    }
                    components.county = county;
                } else if (types.includes('postal_code')) {
                    components.eircode = component.long_name;
                } else if (types.includes('country')) {
                    components.country = component.long_name;
                }
            });
        }

        // Combine street number and route for address line 1
        components.address_line1 = (streetNumber + ' ' + route).trim();

        // Get coordinates
        if (place.geometry && place.geometry.location) {
            components.latitude = place.geometry.location.lat();
            components.longitude = place.geometry.location.lng();
        }

        // Store formatted address
        components.formatted_address = place.formatted_address || '';

        // Set defaults for Ireland if not present
        if (!components.city) components.city = 'Drogheda';
        if (!components.county) components.county = 'Louth';
        if (!components.country) components.country = 'Ireland';
        if (!components.address_line2) components.address_line2 = '';
        if (!components.eircode) components.eircode = '';

        window.debugLog('Extracted address data:', components);
        return components;
    },

    /**
     * Initialize a map preview with a marker
     * @param {string} containerId - The ID of the container element
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     */
    initMapPreview: function(containerId, lat, lng) {
        window.debugLog('Initializing map preview:', containerId, lat, lng);

        const container = document.getElementById(containerId);
        if (!container) {
            window.debugError('Map container not found:', containerId);
            return;
        }

        // Default to Drogheda, Ireland if no coordinates provided
        const defaultLat = lat || 53.7170;
        const defaultLng = lng || -6.3571;

        // Create map
        this.map = new google.maps.Map(container, {
            center: { lat: defaultLat, lng: defaultLng },
            zoom: lat ? 15 : 12,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
            zoomControl: true,
            styles: [
                {
                    featureType: 'poi',
                    elementType: 'labels',
                    stylers: [{ visibility: 'off' }]
                }
            ]
        });

        // Create marker if coordinates provided
        if (lat && lng) {
            this.marker = new google.maps.Marker({
                position: { lat: defaultLat, lng: defaultLng },
                map: this.map,
                animation: google.maps.Animation.DROP,
                title: 'Delivery Location'
            });
        }

        window.debugLog('Map preview initialized');
    },

    /**
     * Update map preview with new coordinates
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     */
    updateMapPreview: function(lat, lng) {
        window.debugLog('Updating map preview:', lat, lng);

        if (!this.map) {
            window.debugWarn('Map not initialized, cannot update');
            return;
        }

        const position = { lat: lat, lng: lng };

        // Update or create marker
        if (this.marker) {
            this.marker.setPosition(position);
            this.marker.setAnimation(google.maps.Animation.DROP);
        } else {
            this.marker = new google.maps.Marker({
                position: position,
                map: this.map,
                animation: google.maps.Animation.DROP,
                title: 'Delivery Location'
            });
        }

        // Center and zoom map
        this.map.setCenter(position);
        this.map.setZoom(15);

        window.debugLog('Map preview updated');
    },

    /**
     * Show the map container
     * @param {string} containerId - The ID of the container element
     */
    showMap: function(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.style.display = 'block';
            // Trigger resize to ensure map renders properly
            if (this.map) {
                google.maps.event.trigger(this.map, 'resize');
            }
        }
    },

    /**
     * Hide the map container
     * @param {string} containerId - The ID of the container element
     */
    hideMap: function(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.style.display = 'none';
        }
    },

    /**
     * Clear the autocomplete input
     * @param {string} inputId - The ID of the input element
     */
    clearAutocomplete: function(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = '';
        }

        // Remove marker
        if (this.marker) {
            this.marker.setMap(null);
            this.marker = null;
        }

        // Reset map to default location (Drogheda)
        if (this.map) {
            this.map.setCenter({ lat: 53.7170, lng: -6.3571 });
            this.map.setZoom(12);
        }
    },

    /**
     * Clean up resources
     */
    dispose: function() {
        window.debugLog('Disposing Google Maps resources');

        if (this.autocomplete) {
            google.maps.event.clearInstanceListeners(this.autocomplete);
            this.autocomplete = null;
        }

        if (this.marker) {
            this.marker.setMap(null);
            this.marker = null;
        }

        if (this.map) {
            this.map = null;
        }

        this.dotNetRef = null;

        window.debugLog('Google Maps resources disposed');
    }
};

// Helper function to check if Google Maps API is loaded
window.isGoogleMapsLoaded = function() {
    return typeof google !== 'undefined' && typeof google.maps !== 'undefined';
};

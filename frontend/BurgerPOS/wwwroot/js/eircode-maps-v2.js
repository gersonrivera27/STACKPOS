// frontend/BurgerPOS/wwwroot/js/eircode-maps-v2.js
// NOTE: debugLog, debugWarn, debugError are declared as global functions in google-maps.js

/**
 * Busca una dirección usando el Eircode irlandés
 * Prioriza Google Maps Geocoding API
 */
window.searchAddressByEircode = async function (eircode, dotnetReference) {
    window.debugLog('🔍 Buscando dirección para Eircode:', eircode);

    const cleanEircode = eircode.trim().toUpperCase().replace(/\s+/g, '');

    // Validar que sea un Eircode irlandés válido
    if (!isValidIrishEircode(cleanEircode)) {
        window.debugError('❌ Formato de Eircode inválido:', cleanEircode);
        await dotnetReference.invokeMethodAsync('OnAddressError',
            'Formato de Eircode inválido. Debe ser como: A92 D65P'
        );
        return;
    }

    try {
        // Método 1: Google Places Text Search (MEJOR para Eircodes → direcciones exactas)
        if (typeof google !== 'undefined' && google.maps && google.maps.places) {
            window.debugLog('🏠 Método 1: Usando Google Places Text Search...');
            let placesSuccess = await searchWithPlacesTextSearch(cleanEircode, dotnetReference);
            if (placesSuccess) {
                return;
            }
        }

        // Método 2: Google Maps Geocoding (fallback)
        let googleSuccess = false;
        if (typeof google !== 'undefined' && google.maps && google.maps.Geocoder) {
            window.debugLog('🗺️ Método 2: Usando Google Maps Geocoding API...');
            googleSuccess = await searchWithGoogleMaps(cleanEircode, dotnetReference);
        }

        if (googleSuccess) {
            return;
        }

        window.debugLog('⚠️ Google Maps no disponible o falló. Usando prefijo...');

        // Método 3: Detección por prefijo (último recurso)
        // NOTE: Nominatim free-text search removed - it doesn't support Irish Eircodes
        // and returns completely wrong results (e.g. Dublin for Drogheda Eircodes)
        window.debugLog('📡 Método 3: Usando mapa de prefijos...');

        if (cleanEircode.startsWith('A92')) {
            window.debugLog('✅ Detectado área de Drogheda');
            await dotnetReference.invokeMethodAsync('OnAddressFound',
                'Drogheda Area',
                'Drogheda',
                53.7134,
                -6.3488
            );
            return;
        }

        const eircodeMap = getIrishEircodeCity(cleanEircode);
        if (eircodeMap) {
            window.debugLog('✅ Área detectada por prefijo:', eircodeMap);
            await dotnetReference.invokeMethodAsync('OnAddressFound',
                eircodeMap.area,
                eircodeMap.city,
                eircodeMap.lat,
                eircodeMap.lon
            );
            return;
        }

        // No se encontró
        window.debugWarn('❌ No se pudo encontrar dirección para este Eircode');
        await dotnetReference.invokeMethodAsync('OnAddressError',
            'No se encontró dirección. Por favor ingresa la dirección manualmente.'
        );

    } catch (error) {
        window.debugError('❌ Error buscando dirección:', error);
        await dotnetReference.invokeMethodAsync('OnAddressError',
            'Error al buscar dirección: ' + error.message
        );
    }
};

/**
 * Búsqueda con Google Places Text Search (MEJOR MÉTODO para Eircodes)
 * Places Text Search resuelve Eircodes a direcciones exactas de calle
 */
async function searchWithPlacesTextSearch(eircode, dotnetReference) {
    return new Promise((resolve) => {
        try {
            // PlacesService requires a DOM element (can be a hidden div)
            let serviceDiv = document.getElementById('places-service-div');
            if (!serviceDiv) {
                serviceDiv = document.createElement('div');
                serviceDiv.id = 'places-service-div';
                serviceDiv.style.display = 'none';
                document.body.appendChild(serviceDiv);
            }

            const service = new google.maps.places.PlacesService(serviceDiv);

            // Format eircode with space for better matching: A92D65P -> A92 D65P
            const formattedEircode = eircode.length === 7
                ? eircode.substring(0, 3) + ' ' + eircode.substring(3)
                : eircode;

            window.debugLog('🔍 Places Text Search: Buscando', formattedEircode);

            service.textSearch({
                query: formattedEircode + ', Ireland',
                region: 'ie'
            }, async (results, status) => {
                window.debugLog('📦 Places Text Search Status:', status, 'Results:', results?.length || 0);

                if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {
                    const result = results[0];
                    const location = result.geometry.location;

                    window.debugLog('📦 Places result:', {
                        name: result.name,
                        address: result.formatted_address,
                        placeId: result.place_id
                    });

                    // Get detailed address components using Place Details
                    service.getDetails({
                        placeId: result.place_id,
                        fields: ['address_components', 'formatted_address', 'geometry']
                    }, async (place, detailStatus) => {
                        if (detailStatus === google.maps.places.PlacesServiceStatus.OK && place) {
                            let street = '';
                            let streetNumber = '';
                            let route = '';
                            let city = 'Drogheda';
                            let county = 'Louth';
                            let foundEircode = '';

                            for (const component of place.address_components) {
                                const types = component.types;

                                if (types.includes('street_number')) {
                                    streetNumber = component.long_name;
                                } else if (types.includes('route')) {
                                    route = component.long_name;
                                } else if (types.includes('sublocality') || types.includes('neighborhood')) {
                                    if (!route) route = component.long_name;
                                } else if (types.includes('locality')) {
                                    city = component.long_name;
                                } else if (types.includes('postal_town')) {
                                    if (!city || city === 'Drogheda') city = component.long_name;
                                } else if (types.includes('administrative_area_level_1')) {
                                    county = component.long_name;
                                    if (county.startsWith('County ')) county = county.substring(7);
                                } else if (types.includes('postal_code')) {
                                    foundEircode = component.long_name;
                                }
                            }

                            // Build street address
                            street = (streetNumber + ' ' + route).trim();

                            // If no street from components, use result name or formatted_address
                            if (!street || street === '') {
                                // result.name often contains the specific address/place name
                                if (result.name && result.name !== city && !result.name.includes(eircode)) {
                                    street = result.name;
                                } else {
                                    const parts = place.formatted_address.split(',');
                                    street = parts[0].trim();
                                    if (street === city) {
                                        street = parts.length > 1 ? parts[1].trim() : street;
                                    }
                                }
                            }

                            const lat = location.lat();
                            const lon = location.lng();

                            window.debugLog('✅ Places Text Search - Dirección exacta encontrada:', {
                                street, city, county, lat, lon,
                                formatted: place.formatted_address
                            });

                            await dotnetReference.invokeMethodAsync('OnAddressFound',
                                street, city, lat, lon
                            );
                            resolve(true);
                        } else {
                            // Details failed, use basic info from text search
                            window.debugLog('⚠️ Place details failed, using basic text search result');
                            const parts = result.formatted_address.split(',');
                            const street = parts[0].trim();
                            const city = parts.length > 1 ? parts[1].trim() : 'Drogheda';
                            const lat = location.lat();
                            const lon = location.lng();

                            await dotnetReference.invokeMethodAsync('OnAddressFound',
                                street, city, lat, lon
                            );
                            resolve(true);
                        }
                    });
                } else {
                    window.debugWarn('❌ Places Text Search no encontró resultados para:', formattedEircode);
                    resolve(false);
                }
            });
        } catch (error) {
            window.debugError('❌ Error en Places Text Search:', error);
            resolve(false);
        }
    });
}

/**
 * Búsqueda con Google Maps Geocoding API (MÉTODO PRINCIPAL)
 */
async function searchWithGoogleMaps(eircode, dotnetReference) {
    return new Promise((resolve) => {
        try {
            const geocoder = new google.maps.Geocoder();

            window.debugLog('🔍 Google Maps: Geocodificando Eircode:', eircode);

            geocoder.geocode({
                address: eircode,
                componentRestrictions: {
                    country: 'IE'  // Forzar Irlanda
                }
            }, async (results, status) => {
                window.debugLog('📦 Google Maps Status:', status);

                if (status === 'OK' && results && results.length > 0) {
                    const result = results[0];
                    const location = result.geometry.location;

                    let street = '';
                    let city = 'Drogheda';
                    let county = 'County Louth';

                    // Extraer componentes de dirección
                    for (const component of result.address_components) {
                        const types = component.types;

                        if (types.includes('route')) {
                            street = component.long_name;
                        } else if (types.includes('street_number')) {
                            street = component.long_name + ' ' + street;
                        } else if (types.includes('sublocality') || types.includes('neighborhood')) {
                            if (!street) street = component.long_name;
                        } else if (types.includes('locality')) {
                            city = component.long_name;
                        } else if (types.includes('postal_town')) {
                            if (!city || city === 'Drogheda') city = component.long_name;
                        } else if (types.includes('administrative_area_level_1')) {
                            county = component.long_name;
                        } else if (types.includes('administrative_area_level_2')) {
                            if (!county || county === 'County Louth') county = component.long_name;
                        }
                    }

                    // Si no hay calle específica, usar la primera parte de formatted_address
                    if (!street || street.trim() === '') {
                        const parts = result.formatted_address.split(',');
                        if (parts.length > 0) {
                            street = parts[0].trim();
                            // Evitar que la calle sea igual a la ciudad
                            if (street === city) {
                                street = parts.length > 1 ? parts[1].trim() : street;
                            }
                        }
                    }

                    const lat = location.lat();
                    const lon = location.lng();

                    window.debugLog('✅ Google Maps - Dirección encontrada:', {
                        address: street,
                        city: city,
                        county: county,
                        country: 'Ireland',
                        lat: lat,
                        lon: lon,
                        formatted_address: result.formatted_address
                    });

                    await dotnetReference.invokeMethodAsync('OnAddressFound',
                        street,
                        city,
                        lat,
                        lon
                    );

                    resolve(true); // Success
                } else {
                    window.debugWarn('❌ Google Maps Geocoding falló o fue denegado:', status);
                    // No llamamos a OnAddressError aquí para permitir el fallback
                    resolve(false); // Failed
                }
            });
        } catch (error) {
            window.debugError('❌ Error en Google Maps:', error);
            resolve(false); // Failed
        }
    });
}

/**
 * Validar que sea un Eircode irlandés válido
 */
function isValidIrishEircode(eircode) {
    // Formato irlandés: A65F4E2 (letra + 2 dígitos + 4 alfanuméricos)
    const pattern = /^[A-Z]\d{2}[A-Z0-9]{4}$/;
    return pattern.test(eircode);
}

/**
 * Mapa de prefijos de Eircode a ciudades irlandesas
 * Solo usado como último recurso si Google Maps falla
 */
function getIrishEircodeCity(eircode) {
    const prefix = eircode.substring(0, 3);

    const eircodeMap = {
        // Drogheda - County Louth
        'A92': { city: 'Drogheda', area: 'Drogheda', lat: 53.7134, lon: -6.3488 },

        // Dundalk - County Louth
        'A91': { city: 'Dundalk', area: 'Dundalk', lat: 54.0008, lon: -6.4058 },

        // Dublin
        'D01': { city: 'Dublin', area: 'Dublin 1', lat: 53.3498, lon: -6.2603 },
        'D02': { city: 'Dublin', area: 'Dublin 2', lat: 53.3382, lon: -6.2591 },

        // Cork
        'T12': { city: 'Cork', area: 'Cork City', lat: 51.8985, lon: -8.4756 },
        'T23': { city: 'Cork', area: 'Cork City', lat: 51.8985, lon: -8.4756 },

        // Galway
        'H91': { city: 'Galway', area: 'Galway City', lat: 53.2707, lon: -9.0568 },

        // Limerick
        'V94': { city: 'Limerick', area: 'Limerick City', lat: 52.6638, lon: -8.6267 },

        // Waterford
        'X91': { city: 'Waterford', area: 'Waterford City', lat: 52.2593, lon: -7.1101 }
    };

    return eircodeMap[prefix] || null;
}

window.debugLog('✅ Eircode Search API cargada');
window.debugLog('🗺️ Google Maps API: ' + (typeof google !== 'undefined' ? 'Disponible ✅' : 'No disponible ❌'));

/**
 * Abre Google Maps en una nueva pestaña con el Eircode
 */
window.openInGoogleMaps = function (eircode) {
    if (!eircode) return;
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(eircode)}`;
    window.open(url, '_blank');
};

/**
 * Función auxiliar para consultar Nominatim
 */
async function searchNominatim(query) {
    try {
        const nominatimUrl = `https://nominatim.openstreetmap.org/search?` +
            `postalcode=${encodeURIComponent(query)}` +
            `&country=ie` +
            `&countrycodes=ie` +
            `&format=json` +
            `&addressdetails=1` +
            `&limit=1`;

        const nominatimResponse = await fetch(nominatimUrl, {
            headers: { 'User-Agent': 'BurgerPOS/1.0' }
        });

        if (!nominatimResponse.ok) return null;

        const nominatimData = await nominatimResponse.json();
        if (!nominatimData || nominatimData.length === 0) return null;

        const result = nominatimData[0];
        if (!result.address || result.address.country_code !== 'ie') return null;

        const address = result.address;
        let addressLine = '';

        if (address.house_number && address.road) {
            addressLine = `${address.house_number} ${address.road}`;
        } else if (address.road) {
            addressLine = address.road;
        } else if (address.neighbourhood) {
            addressLine = address.neighbourhood;
        } else if (address.suburb) {
            addressLine = address.suburb;
        } else if (address.village) {
            addressLine = address.village;
        } else {
            const parts = result.display_name.split(',');
            addressLine = parts[0].trim();
        }

        return {
            address: addressLine,
            city: address.town || address.city || address.village || address.county || 'Drogheda',
            county: address.county || 'County Louth',
            lat: parseFloat(result.lat),
            lon: parseFloat(result.lon)
        };
    } catch (e) {
        window.debugWarn('Error en Nominatim search:', e);
        return null;
    }
}

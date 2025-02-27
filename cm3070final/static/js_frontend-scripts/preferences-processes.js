document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        document.getElementById("preferences-modal").classList.remove("hidden");
        document.getElementById("preferences-modal").classList.add("flex");
    }, 1500);

    new TomSelect("#language-select", {
        plugins: ['remove_button'],  // Adds 'X' button for removing selections
        create: false,
        maxItems: 5, 
        placeholder: "Select languages...",
        render: {
            option: function(data, escape) {
                return `<div>${escape(data.text)}</div>`;
            }
        }
    });

    // Ensure Google Places API is loaded before initializing autocomplete
    if (typeof google !== "undefined" && google.maps && google.maps.places) {
        initAutocomplete();
    } else {
        console.warn("Google Places API not loaded yet.");
    }
});

function initAutocomplete() {
    let input = document.getElementById("location-input");
    let autocomplete = new google.maps.places.Autocomplete(input, { types: ["geocode"] });

    autocomplete.addListener("place_changed", function () {
        let place = autocomplete.getPlace();
        if (!place.geometry) {
            console.log("No location details available");
            return;
        }
        let locationData = {
            lat: place.geometry.location.lat(),
            lon: place.geometry.location.lng(),
            city: place.address_components[0].long_name,
            formatted_address: place.formatted_address
        };
        console.log("Selected Location:", locationData);

        // Store data in a hidden input field to submit with form
        document.getElementById("location-hidden").value = JSON.stringify(locationData);
        console.log("Stored Location Data:", document.getElementById("location-hidden").value);
    });
}
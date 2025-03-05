document.addEventListener("DOMContentLoaded", function() {
    // Enable/Disable Location Search
    document.getElementById("enable-location").addEventListener("change", function () {
        let locationInput = document.getElementById("location-input");
        let proximity = document.getElementById("proximity");
        locationInput.disabled = !this.checked;
        locationInput.classList.toggle("bg-gray-200", !this.checked);
        proximity.disabled = !this.checked;
        proximity.classList.toggle("bg-gray-200", !this.checked);
    });

    document.querySelectorAll(".dropdown").forEach(dropdown => {
        const toggle = dropdown.querySelector(".dropdown-toggle");
        const menu = dropdown.querySelector(".dropdown-menu");
        const selectedContainer = dropdown.querySelector(".selected-items");

        toggle.addEventListener("click", function (event) {
            event.stopPropagation();

            // Hide all other dropdowns before opening this one
            document.querySelectorAll(".dropdown-menu").forEach(otherMenu => {
                if (otherMenu !== menu) {
                    otherMenu.classList.add("hidden");
                }
            });

            menu.classList.toggle("hidden");
        });

        menu.addEventListener("change", function () {
            updateSelectedItems(menu, selectedContainer, toggle);
        });

        menu.addEventListener("click", function(event) {
            event.stopPropagation(); // Prevent closing dropdown when clicking inside it
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener("click", function () {
        document.querySelectorAll(".dropdown-menu").forEach(menu => {
            menu.classList.add("hidden");
        });
    });

    const slider = document.getElementById("proximity");
    const sliderValue = document.getElementById("proximity-value");

    slider.addEventListener("input", function() {
        sliderValue.textContent = `${slider.value} km`
    });

    const resetButton = document.getElementById("reset-filters");
    const form = document.getElementById("filter-form");

    resetButton.addEventListener("click", function() {
        form.reset();

        setTimeout(() => {
            document.querySelectorAll(".dropdown-toggle").forEach(dropdown => {
                dropdown.textContent = "Select from dropdown";
            });

            document.querySelectorAll(".selected-items").forEach(container => {
                container.innerHTML = "";
            });
        }, 50);

        const proximitySlider = document.getElementById("proximity");
        const proximityValue = document.getElementById("proximity-value");
        if (proximitySlider && proximityValue) {
            proximityValue.textContent = `${proximitySlider.value} km`;
        }

        const enableLocation = document.getElementById("enable-location");
        const locationInput = document.getElementById("location-input");
        const proximity = document.getElementById("proximity");

        if (!enableLocation.checked) {
            enableLocation.checked = true; // Ensure it's checked
        }

        locationInput.disabled = false;
        proximity.disabled = false;
        locationInput.classList.remove("bg-gray-200");
        proximity.classList.remove("bg-gray-200");
    });
});

// Update the selected items in the dropdown to show the user what they have selected
function updateSelectedItems(menu, selectedContainer, toggle) {
    let selected = Array.from(menu.querySelectorAll("input:checked"))
        .map(checkbox => checkbox.nextElementSibling.textContent.trim());

    // Update the dropdown display text
    toggle.textContent = selected.length > 0 ? "Selections made" : "Select from dropdown";

    // Clear previous selections
    selectedContainer.innerHTML = "";

    // Append selected items below
    selected.forEach(item => {
        let span = document.createElement("span");
        span.classList.add("bg-blue-500", "text-white", "px-2", "py-1", "rounded", "text-xs", "font-semibold");
        span.textContent = item;
        selectedContainer.appendChild(span);
    });
}

document.getElementById("filter-form").addEventListener("submit", function(event) {
    const enableLocation = document.getElementById("enable-location");
    const locationInput = document.getElementById("location-input");
    const hiddenLocation = document.getElementById("location-hidden");
    const proximity = document.getElementById("proximity");

    if (!enableLocation.checked) {
        locationInput.removeAttribute("name");
        hiddenLocation.removeAttribute("name");
        proximity.removeAttribute("name");
    } else {
        locationInput.setAttribute("name", "location_input");
        hiddenLocation.setAttribute("name", "location");
        proximity.setAttribute("name", "proximity");
    }
});
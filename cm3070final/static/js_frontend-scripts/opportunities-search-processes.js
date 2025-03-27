document.addEventListener("DOMContentLoaded", function() {

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

function renderOpportunities(opportunities) {
    const container = document.getElementById("opportunity-results");
    const noResultsPlaceholder = document.getElementById("no-results-placeholder");
    container.innerHTML = "";

    if (opportunities.length === 0) {
        noResultsPlaceholder.classList.remove("hidden");
        return;
    } else {
        noResultsPlaceholder.classList.add("hidden");
        opportunities.forEach(opportunity => {
            const isOngoing = opportunity.ongoing;
            const date = opportunity.opportunity_date || "N/A";
            const timeFrom = opportunity.opportunity_time_from || "N/A";
            const timeTo = opportunity.opportunity_time_to || "N/A";
            const location = opportunity.required_location?.formatted_address || "N/A";
            const daysOfWeek = (opportunity.days_of_week || []).map(d => d.charAt(0).toUpperCase() + d.slice(1)).join(", ");
            const skills = (opportunity.requirements || []).join(", ");
            const org = opportunity.organization?.organization;
            const orgName = org?.organization_name || "Unknown Org";
            const orgProfileUrl = org?.profile_url || "#";
            const workBasis = opportunity.work_basis?.charAt(0).toUpperCase() + opportunity.work_basis?.slice(1);
            const duration = opportunity.duration?.charAt(0).toUpperCase() + opportunity.duration?.slice(1);
            const areaOfWork = opportunity.area_of_work?.charAt(0).toUpperCase() + opportunity.area_of_work?.slice(1);
            const applyAsGroup = opportunity.can_apply_as_group
                ? `Yes${opportunity.slots ? ` (${opportunity.slots} slots available)` : ""}`
                : "No";
    
            container.innerHTML += `
                <div class="bg-gray-50 p-4 rounded-lg shadow-md mt-2 flex items-center justify-between transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg hover:bg-gray-100 cursor-pointer"
                     data-url="/opportunities-engagements/opportunity/${opportunity.volunteer_opportunity_id}/"
                     onclick="window.location.href=this.getAttribute('data-url')">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <h3 class="font-bold text-lg">${opportunity.title}</h3>
                            <p class="text-sm text-gray-700 mb-2">${opportunity.description}</p>
    
                            <p class="text-sm"><strong>Opportunity Type:</strong> ${isOngoing ? "Ongoing" : "One-Time"}</p>
                            ${!isOngoing ? `
                                <p class="text-sm"><strong>Date:</strong> ${date}</p>
                                <p class="text-sm"><strong>From:</strong> ${timeFrom} <strong>To:</strong> ${timeTo}</p>
                            ` : ""}
                            <p class="text-sm"><strong>Location:</strong> ${location}</p>
                        </div>
                        <div class="flex flex-col justify-center">
                            <p class="text-sm"><strong>Work Basis:</strong> ${workBasis}</p>
                            <p class="text-sm"><strong>Duration:</strong> ${duration}</p>
                            <p class="text-sm"><strong>Area of Work:</strong> ${areaOfWork}</p>
                            <p class="text-sm"><strong>Skills Required:</strong> ${skills}</p>
                            ${!isOngoing
                                ? `<p class="text-sm"><strong>Apply as Group:</strong> ${applyAsGroup}</p>`
                                : `<p class="text-sm"><strong>Days of Week:</strong> ${daysOfWeek}</p>`
                            }
                        </div>
                        <div class="col-span-2 text-center">
                            <p class="text-sm">
                              <strong>Organization:</strong>
                              <a href="${orgProfileUrl}" class="text-blue-600 hover:underline">
                                ${orgName}
                              </a>
                            </p>
                        </div>
                    </div>
                </div>
            `;
        });
    }
}

// 1. Prevent HTMX from injecting raw JSON into the target div
document.body.addEventListener("htmx:beforeSwap", function (event) {
    if (event.detail.target.id === "opportunity-results" && event.detail.xhr.getResponseHeader("content-type")?.includes("application/json")) {
        event.detail.shouldSwap = false; // Cancel default HTML swap
    }
});

// 2. After response is loaded, process the JSON manually
document.body.addEventListener("htmx:afterOnLoad", function (event) {
    if (event.detail.target.id === "opportunity-results") {
        try {
            const data = JSON.parse(event.detail.xhr.responseText);
            document.getElementById("search-placeholder")?.classList.add("hidden"); // hide intro

            renderOpportunities(data);
        } catch (err) {
            console.error("Failed to parse HTMX JSON response", err);
        }
    }
});
// Toggles the visibility of the opportunity type fields based on the selected radio button
function toggleOpportunityType() {
    let isOngoing = document.querySelector('input[name="ongoing"]:checked').value === "true";
    document.getElementById("one-time-fields").classList.toggle("hidden", isOngoing);
    document.getElementById("ongoing-fields").classList.toggle("hidden", !isOngoing);
    document.getElementById("duration-select").disabled = !isOngoing;
    if(!isOngoing) {
        document.getElementById("duration-select").value = "short-term";
    }
}

// Toggles the visibility of the engagement type fields based on the selected radio button
function toggleGroupApplication() {
    let checkbox = document.getElementById('as_group');
    let groupSizeContainer = document.getElementById('group-size-container');
    
    if (checkbox.checked) {
        groupSizeContainer.classList.remove('hidden');
    } else {
        groupSizeContainer.classList.add('hidden');
    }
}

// Toggles the visibility of the engagement type fields based on the selected radio button
function filterOpportunities(status) {
    document.querySelectorAll('.opportunity-card').forEach(card => {
        if (card.getAttribute('data-status') === status) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });

    // If no opportunities, show message
    if (!document.querySelector(`.opportunity-card[data-status="${status}"]`)) {
        document.getElementById('opportunities-container').innerHTML = `<p class="text-center text-gray-500 mt-4">No ${status} opportunities available.</p>`;
    }
}

// Toggles the visibility of the engagement type fields based on the selected radio button
function filterSessions(status) {
    document.querySelectorAll('.session-card').forEach(card => {
        if (status === "all" || card.getAttribute('data-status') === status) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });

    // If no sessions match the selected filter, show a message
    let visibleSessions = document.querySelectorAll(`.session-card[data-status="${status}"]`);
    let sessionContainer = document.getElementById('sessions-container');

    if (visibleSessions.length === 0 && status !== "all") {
        sessionContainer.innerHTML = `<p class="text-center text-gray-500 mt-4">No ${status} sessions available.</p>`;
    }
}
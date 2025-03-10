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

// Toggles the group application fields based on the selected radio button
function toggleGroupApplication() {
    let checkbox = document.getElementById('as_group');
    let groupSizeContainer = document.getElementById('group-size-container');
    
    if (checkbox.checked) {
        groupSizeContainer.classList.remove('hidden');
    } else {
        groupSizeContainer.classList.add('hidden');
    }
}

// Toggles the visibility of the session type fields based on the selected radio button
function filterSessions(status) {
    let isOwner = document.body.dataset.isOpportunityOwner === "true"; // Passed from Django template
    document.querySelectorAll('.session-card').forEach(card => {
        if (!isOwner && card.getAttribute('data-status') !== "upcoming") {
            card.style.display = 'none'; // Volunteers only see upcoming
        } else if (status === "all" || card.getAttribute('data-status') === status) {
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

// Toggles the filter for engagements, applications and log requests
function filterEngagementsApplicationsLogRequests(type, status) {
    document.querySelectorAll(`.${type}-card`).forEach(card => {
        card.style.display = status === "all" || card.getAttribute("data-status") === status ? "block" : "none";
    });
}

// Toggle the filter of applications and log requests
function filterApplicationsLogRequests(filter){
    document.getElementById("pending-applications").classList.add("hidden");
    document.getElementById("pending-log-requests").classList.add("hidden");
    document.getElementById(filter).classList.remove("hidden");
}
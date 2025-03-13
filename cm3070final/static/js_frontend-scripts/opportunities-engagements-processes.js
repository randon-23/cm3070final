// FILTERS & TOGGLES
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

// HELPER FUNCTION FOR SEQUENTIAL API CALLS
// Asynchronous function to execute a series of actions in sequence
async function executeChainedActions(actions, prevData = {}) {
    const modalContent = document.getElementById("loading-modal-content");
    modalContent.innerHTML = "<p>Processing...</p>";
    let modal = document.getElementById("loading-modal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    let hasErrorOccurred = false;

    for (let action of actions) {
        try{
            let url = typeof action.url === "function" ? action.url(prevData) : action.url;
            let response = await fetch(url, {
                method: action.method,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                },
                body: action.method !== "GET" ? JSON.stringify(action.data) : null
            })

            let data = await response.json();

            if (data.message){
                modalContent.innerHTML += `<p>${data.message}</p>`;
            } else if (data.error){
                modalContent.innerHTML += `<p>${data.error}</p>`;
            }

            if(response.status == 400 && typeof data.data === "object"){
                modalContent.innerHTML += "<ul>";
                for (let field in data.data){
                    if (data.data.hasOwnProperty(field)){
                        modalContent.innerHTML += `<li><strong>${field}:</strong> ${data.data[field].join(", ")}</li>`;
                    }
                }
                modalContent.innerHTML += "</ul>";
            }

            if(action.extractParam && action.nextKey){
                let keys = action.extractParam.split(".");
                let extractedValue = keys.reduce((obj, key) => obj[key], data);
                if (extractedValue) {
                    prevData[action.nextKey] = extractedValue;
                }
            }

            if (!response.ok) {
                hasErrorOccurred = true;
                break;
            }
        } catch {
            modalContent.innerHTML += `<p class="text-red-600">❌ An error occurred. Please try again later.</p>`;
            hasErrorOccurred = true;
            break;
        }
    }

    if(!hasErrorOccurred){
        modalContent.innerHTML += `<p class="text-blue-600">✅ All actions completed successfully!</p>`;
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
}

// SEQUENTIAL API CALL FUNCTIONS
// no form
function cancelOpportunity(volunteerOpportunityId) {
    executeChainedActions([
        { url: `/api/opportunities/cancel_opportunity/${volunteerOpportunityId}/`, method: "PATCH"},
        { url: `/api/engagements/cancel_engagements_organization/${volunteerOpportunityId}/`, method: "PATCH"}
    ]);
}

// no form - called from modal which displays current engagees so org can remove any
function completeOpportunity(volunteerOpportunityId, isOngoing) {
    let actions = [
        { url: `/api/opportunities/complete_opportunity/${volunteerOpportunityId}/`, method: "PATCH" },
        { url: `/api/engagements/complete_engagements_organization/${volunteerOpportunityId}/`, method: "PATCH" },
    ];

    if (!isOngoing) {
        actions.push({
            url: `/api/engagement_logs/create_opportunity_engagement_logs/${volunteerOpportunityId}/`,
            method: "POST",
        });
    }
    executeChainedActions(actions);
}

// no form
function acceptApplication(applicationId, accountUuid, opportunityId, isOngoing) {
    let actions = [
        { url: `/api/opportunities/applications/accept/${applicationId}/`, method: "PATCH" },
        { url: `/api/engagements/create_engagement/${applicationId}/`, method: "POST" },
    ];

    if (isOngoing) {
        actions.push({url: `/api/session_engagements/create_session_engagements_for_volunteer/${accountUuid}/${opportunityId}/`, method: "POST"});
    }

    executeChainedActions(actions);
}

// called from form
function createSession(opportunityId, data) {
    executeChainedActions([
        {
            url: `/api/sessions/create_session/${opportunityId}/`,
            method: "POST",
            data: data,
            extractParam: "data.session_id",
            nextKey: "sessionId"
        },
        {
            url: (params) => `/api/session_engagements/create_session_engagements_for_session/${params.sessionId}/`,
            method: "POST"
        }
    ]);
}

document.addEventListener("DOMContentLoaded", () => {
    let createSessionForm = document.getElementById("create-session-form");
    if (createSessionForm) {
        createSessionForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(createSessionForm);
            const data = Object.fromEntries(formData.entries());
            if(!data.slots) {
                delete data.slots; // Remove slots if not provided - null instead of ""
            }
            const opportunityId = document.getElementById("create-session-modal").dataset.opportunityId;
            createSession(opportunityId, data);
        });
    }
});

// no form - called from modal which displays current session engagees so org can remove any
function completeSession(sessionId) {
    executeChainedActions([
        { url: `/api/sessions/complete_session/${sessionId}/`, method: "PATCH"},
        { url: `/api/engagement_logs/create_session_engagement_logs/${sessionId}/`, method: "POST"}
    ]);
}

// FETCH REQUESTS AND CORRESPONDING REMOVAL ON MODAL OPEN FUNCTIONS
function removeEngagement(engagementId) {
    fetch(`/api/engagements/cancel_engagement_volunteer/${engagementId}/`, { method: "PATCH" })
        .then(() => document.getElementById(engagementId).remove());
}

function setCantGo(sessionEngagementId) {
    fetch(`/api/session_engagements/cancel_attendance/${sessionEngagementId}/`, { method: "PATCH" })
        .then(() => document.getElementById(sessionEngagementId).remove());
}

// Open modal to confirm opportunity completion with option to cancel listed engagements
function openCompleteOpportunityModal(volunteerOpportunityId) {
    let modal = document.getElementById("complete-opportunity-modal");
    let listContainer = document.getElementById("opportunity-engagement-list");

    // Fetch engaged volunteers
    fetch(`/api/engagements/get_opportunity_engagements/${volunteerOpportunityId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                listContainer.innerHTML = `<p class="text-gray-500 text-center">No engaged volunteers found.</p>`;
                document.getElementById("confirm-complete-opportunity").add("disabled");
                return;
            }

            listContainer.innerHTML = data.map(engagement => `
                <div id="${engagement.volunteer_engagement_id}" class="flex justify-between bg-gray-100 p-4 rounded-md">
                    <span>${engagement.volunteer.account.email_address}</span>
                    <button onclick="removeEngagement('${engagement.volunteer_engagement_id}')"
                            class="bg-red-500 text-white px-4 py-1 rounded-md hover:bg-red-700">
                        Remove
                    </button>
                </div>
            `).join('');
        });

    // Show modal
    modal.classList.remove("hidden");
}

// Open modal to confirm session completion with option to cancel listed session engagements
function openCompleteSessionModal(sessionId) {
    let modal = document.getElementById("complete-session-modal");
    let listContainer = document.getElementById("session-attendee-list");

    // Fetch session attendees
    fetch(`/api/session_engagements/get_session_engagements/${sessionId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                listContainer.innerHTML = `<p class="text-gray-500 text-center">No attendees found.</p>`;
                document.getElementById("confirm-complete-session").add("disabled");
                return;
            }

            listContainer.innerHTML = data.map(attendee => `
                <div id="${attendee.session_engagement_id}" class="flex justify-between bg-gray-100 p-4 rounded-md">
                    <span>${attendee.volunteer.account.email_address}</span>
                    <button onclick="setCantGo('${attendee.session_engagement_id}')"
                            class="bg-red-500 text-white px-4 py-1 rounded-md hover:bg-red-700">
                        Mark as 'Can't Go'
                    </button>
                </div>
            `).join('');
        });

    // Show modal
    modal.classList.remove("hidden");
}
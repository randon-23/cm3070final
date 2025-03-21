function updateSearchResults(event) {
    let response = event.detail.xhr.responseText;
    try{
        let data = JSON.parse(response)
        let resultsContainer = document.getElementById("search-results-container");

        if(data.results.length === 0 && document.getElementById("search-input").value !== ""){
            resultsContainer.innerHTML = '<p class="p-3 text-center text-gray-500">No results found</p>';
            //resultsContainer.classList.add("hidden");
            return;
        } else if(document.getElementById("search-input").value === ""){
            resultsContainer.innerHTML = '';
            resultsContainer.classList.add("hidden");
            return;
        }

        let resultsHTML = data.results.map(result => `
            <a href="${result.profile_url}" class="flex items-center p-3 hover:bg-gray-100 cursor-pointer">
                <img src="${result.profile_img ? result.profile_img : (result.first_name ? '/static/images/default_volunteer.svg' : (result.organization_profile_img ? result.organization_profile_img : '/static/images/default_organization.svg'))}" class="w-10 h-10 rounded-full object-cover mr-3" alt="">
                <div>
                    <p class="font-bold text-gray-800">
                        ${result.first_name ? result.first_name + ' ' + result.last_name : result.organization_name}
                    </p>
                    <p class="text-gray-500 text-sm">
                        ${result.first_name ? 'Volunteer' : 'Organization'}
                    </p>
                </div>
            </a>
        `).join('');

        resultsContainer.innerHTML = resultsHTML;
        resultsContainer.classList.remove("hidden");

    } catch (error) {
        console.error("Invalid JSON response:", response);
    }
}

function closeLoadingModal() {
    let modal = document.getElementById("loading-modal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
}

// Used when users have not set their preferences yet, as a redirect to the profile page this modal is shown to inform the user on what is happening
function redirectToProfileForPreferences(event, url) {
    event.preventDefault();

    let modal = document.getElementById("loading-modal");
    let modalContent = document.getElementById("loading-modal-content");

    modalContent.innerHTML = `<p>Redirecting to profile page to set preferences...</p>`;
    modal.classList.remove("hidden");
    modal.classList.add("flex");

    setTimeout(() => {
        window.location.href = url;
    }, 1500);

}
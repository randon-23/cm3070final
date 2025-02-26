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
                <img src="${result.profile_img ? result.profile_img : (result.first_name ? '/static/images/default_volunteer.svg' : '/static/images/default_organization.svg')}" class="w-10 h-10 rounded-full object-cover mr-3" alt="">
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
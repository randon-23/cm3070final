function updateFollowerCount(event) {
    let response = event.detail.xhr.responseText;
    try {
        let data = JSON.parse(response);
        console.log(data)
        let followBtnContainer = document.getElementById("follow-btn-container");
        let followersCountElement = document.getElementById("followers-count");
        
        let accountUuid = event.detail.xhr.responseURL?.split('/').pop();
        console.log(accountUuid);
        
        if(!accountUuid){
            console.error("Account UUID not found in the request URL");
        }

        // Update the followers count
        if (followersCountElement) {
            followersCountElement.innerText = data.followers_count;
        }

        let buttonHTML = "";
        // Update the follow button
        if(data.is_following){
            buttonHTML = `
                <button id="unfollow-btn" 
                hx-delete="/volunteers-organizations/api/following/delete_following/${accountUuid}"
                hx-trigger="click"
                hx-target="#follow-btn-container"
                class="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center justify-center space-x-2 transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M22 10.5h-6m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM4 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 10.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
                    </svg>
                    <span class="font-bold">Unfollow</span>
                </button>`
        } else {
            buttonHTML = `
                <button id="follow-btn"
                hx-post="/volunteers-organizations/api/following/create_following/${accountUuid}"
                hx-trigger="click"
                hx-target="#follow-btn-container"
                class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center space-x-2 transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
                    </svg>                      
                    <span class="font-bold">Follow</span>
                </button>`
        }
        // Update the button container
        followBtnContainer.innerHTML = buttonHTML;

        // Reattach htmx listener to the follow button container
        htmx.process(followBtnContainer);
    } catch (error) {
        console.error("Invalid JSON response:", response);
    }
}

// Used for responsiveness in the application when submitting so that user knows that the request is being processed and this then triggers refresh to show the changes
function updateContent(event){
    let response = event.detail.xhr.responseText;
    try{
        let data = JSON.parse(response);
        console.log(data);
        let modalContent
        if(data.message){
            modalContent = `<p>${data.message}</p>`;
        } else if(data.error){
            modalContent = `<p>${data.error}</p>`;
        } else if(data.non_field_errors){
            if(data.non_field_errors[0].includes('must make a unique set')){
                modalContent = `<p>Error - Already done</p>`;
            } else {
                modalContent = `<p>${data.non_field_errors}</p>`;
            }
        }
        
        if (event.detail.xhr.status === 400 && typeof data.data === 'object') {
            modalContent += `<ul>`;
            for (let field in data.data) {
                if (data.data.hasOwnProperty(field)) {
                    modalContent += `<li><strong>${field}:</strong> ${data.data[field].join(', ')}</li>`;
                }
            }
            modalContent += `</ul>`;
        }

        document.getElementById("loading-modal-content").innerHTML = modalContent

        let modal = document.getElementById("loading-modal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        // Check if a redirect URL is present
        let redirectUrl = event.target.getAttribute("data-redirect-url");

        setTimeout(() => {
            if(event.detail.xhr.status === 201 || event.detail.xhr.status === 200){
                if(redirectUrl){
                    window.location.href = redirectUrl;
                } else {
                    window.location.reload();
                }
            }
        }
        , 1000);
    } catch(error){
        console.error("Invalid JSON response:", response);
    }
}
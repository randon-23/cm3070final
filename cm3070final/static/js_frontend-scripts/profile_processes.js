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
                class="w-full mx-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center justify-center space-x-2">
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
                class="w-full mx-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center space-x-2">
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

function updateContent(event){
    let response = event.detail.xhr.responseText;
    try{
        let data = JSON.parse(response);
        console.log(data);
        document.getElementById("loading-modal-content").innerHTML = `<p>${data.message}</p>`;
        
        let modal = document.getElementById("loading-modal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        setTimeout(() => {
            if(event.detail.xhr.status === 201){
                window.location.reload();
            }
        }
        , 1000);
    } catch(error){
        console.error("Invalid JSON response:", response);
    }
}
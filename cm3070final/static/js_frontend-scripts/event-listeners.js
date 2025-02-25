document.addEventListener("htmx:afterRequest", function(event) {
    let url = event.detail.xhr.responseURL

    if (url.includes("logout")){
        console.log("Logging out!", event);
        showLogoutMessage(event);
    } else if (url.includes("following")){
        console.log("Updating following count!", event);
        updateFollowerCount(event);
    } else if(url.includes("/status/create_status_post/")){
        console.log("Updating status post!", event);
        updateContent(event);
    } else if(url.includes("/endorsements/create_endorsement/")){
        console.log("Updating endorsements!", event);
        updateContent(event);
    } else if(url.includes("/search/get_search_profiles/")){
        console.log("Updating search results!", event);
        updateSearchResults(event);
    }
});
document.addEventListener("htmx:afterRequest", function(event) {

    let url = event.detail.xhr.responseURL

    if (url.includes("logout")){
        console.log("Logging out!", event);
        showLogoutMessage(event);
    } else if (url.includes("following")){
        console.log("Updating following count!", event);
        updateFollowerCount(event);
    }
});
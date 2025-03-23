document.addEventListener("htmx:afterRequest", function(event) {
    let url = event.detail.xhr.responseURL

    // Authentication
    if (url.includes("logout")){
        console.log("Logging out!", event);
        showLogoutMessage(event);
    } 
    // Following
    else if (url.includes("following")){
        console.log("Updating following count!", event);
        updateFollowerCount(event);
    } 
    // Status posts
    else if(url.includes("/status/create_status_post/")){
        console.log("Updating status post!", event);
        updateContent(event);

        // Reset the form
        const form = document.getElementById("status-post-form");
        if (form) {
            form.reset();
        }
    } 
    // Endorsements
    else if(url.includes("/endorsements/create_endorsement/")){
        console.log("Updating endorsements!", event);
        updateContent(event);
    } 
    // Search results profiles
    else if(url.includes("/search/get_search_profiles/")){
        console.log("Updating search results!", event);
        updateSearchResults(event);
    } 
    // Preferences
    else if(url.includes("/volunteer_matching_preferences/create_volunteer_preferences/")){
        console.log("Creating initial preferences!", event);
        updateContent(event);
    } else if(url.includes("/organization_preferences/create_organization_preferences/")){
        console.log("Creating initial preferences!", event);
        updateContent(event);
    } else if(url.includes("update_volunteer_preferences") || url.includes("update_organization_preferences")){
        console.log("Updating preferences!", event);
        updateContent(event);
    } 
    // Opportunities
    else if(url.includes('/opportunities/create_opportunity/')){
        console.log("Creating opportunity!", event);
        updateContent(event);
    } 
    // Applications
    else if(url.includes('/applications/create/')){
        console.log("Creating application!", event);
        updateContent(event);
    } else if(url.includes('/applications/reject/')){
        console.log("Rejecting application!", event);
        updateContent(event);
    } else if(url.includes('/applications/cancel/')){
        console.log("Cancelling application!", event);
        updateContent(event);
    } 
    // Engagements
    else if(url.includes('/engagements/cancel_engagement_volunteer')){
        console.log("Cancelling engagement!", event);
        updateContent(event);
    } else if(url.includes('/engagements/get_opportunity_engagements/')){
        console.log("Getting opportunity engagements!", event);
        updateEngagementsModal(event);
    }
    // Sessions
    else if(url.includes('/sessions/get_sessions/')){
        console.log("Updating sessions!", event);
        updateContent(event);
    } else if(url.includes('/sessions/cancel_session/')){
        console.log("Cancelling session!", event);
        updateContent(event);
    } 
    // Session engagements
    else if(url.includes('/session_engagements/confirm_attendance/')){
        console.log("Confirming attendance!", event);
        updateContent(event);
    } else if(url.includes('/session_engagements/cancel_attendance/')){
        console.log("Cancelling attendance!", event);
        updateContent(event);
    } else if(url.includes('/session_engagements/get_session_engagements/')){
        console.log("Getting session engagements!", event);
        updateEngagementsModal(event);
    }
    // Engagement logs
    else if(url.includes('/engagement_logs/create_engagement_log_volunteer/')){
        console.log("Creating engagement log!", event);
        updateContent(event);
    } else if(url.includes('/engagement_logs/approve_engagement_log/')){
        console.log("Approving engagement log!", event);
        updateContent(event);
    } else if(url.includes('/engagement_logs/reject_engagement_log/')){
        console.log("Rejecting engagement log!", event);
        updateContent(event);
    } 
    //Notifications
    else if(url.includes('/notifications/mark_read/')){
        console.log("Marking notification as read!", event)
        let button = event.detail.target
        let notificationId = button.dataset.notificationId
        markAsRead(notificationId)
    }
    // Messages
    else if(url.includes('/chats/start_or_send_message/')){
        console.log("Sending message!", event);
        updateContent(event);
    }
    // Donate
    else if(url.includes('donate/donate_volontera_points/')){
        console.log("Donating points!", event);
        updateContent(event);
    }
});
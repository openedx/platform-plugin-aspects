function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function fetchGuestToken() {
  // Fetch the guest token from your backend
  const response = await fetch(guest_token_url, {
    method: 'POST',
    body: JSON.stringify({
      "X-CSRFToken": getCookie("csrftoken"),
    })
  });
  const data = await response.json();
  return data.guestToken;
}

function embedDashboard(dashboard_uuid, superset_url, guest_token_url, xblock_id) {
  xblock_id = xblock_id || "";

  window.supersetEmbeddedSdk
    .embedDashboard({
      id: dashboard_uuid, // given by the Superset embedding UI
      supersetDomain: superset_url, // your Superset instance
      mountPoint: document.getElementById(`superset-embedded-container-${xblock_id}`), // any html element that can contain an iframe
      fetchGuestToken: fetchGuestToken,
      dashboardUiConfig: {
        // dashboard UI config: hideTitle, hideTab, hideChartControls, filters.visible, filters.expanded (optional)
        hideTitle: true,
        filters: {
          expanded: false,
        },
        hideTab: true,
        hideChartControls: false,
        hideFilters: true,
      },
    })
    .then((dashboard) => {
      mountPoint = document.getElementById("superset-embedded-container");
      /*
      Perform extra operations on the dashboard object or the container
      when the dashboard is loaded
      */
    });
};

if (window.superset_dashboards !== undefined) {
  window.superset_dashboards.forEach(function(dashboard) {
    embedDashboard(dashboard.uuid, window.superset_url, window.superset_guest_token_url, dashboard.uuid);
  });
}

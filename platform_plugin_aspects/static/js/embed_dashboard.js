function embedDashboard(dashboard_uuid, superset_url, guest_token_url, xblock_id) {
  xblock_id = xblock_id || "";

  async fetchGuestToken() {
    // Fetch the guest token from your backend
    const response = await fetch(guest_token_url, {
      method: 'POST',
      body: JSON.stringify({
        // TODO csrf_token: csrf_token,
      })
    });
    const data = await response.json();
    return data.guestToken;
  }

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
    embedDashboard(dashboard.uuid, window.superset_url, window.superset_guest_token_url);
  });
}

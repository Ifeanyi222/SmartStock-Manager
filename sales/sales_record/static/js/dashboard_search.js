document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("dashboard-search");
  const dashboardTables = document.getElementById("dashboard-tables");

  if (!searchInput || !dashboardTables) return;

  searchInput.addEventListener("input", async (e) => {
    const query = e.target.value.trim();

    const response = await fetch(`/search-dashboard/?q=${encodeURIComponent(query)}`);
    const data = await response.json();

    dashboardTables.innerHTML = data.html;
  });
});

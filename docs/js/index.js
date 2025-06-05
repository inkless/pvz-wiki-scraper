// Index page JavaScript functionality

function createContentCard(item, isZombie = false) {
  const card = document.createElement("a");
  card.className = "plant-card" + (isZombie ? " zombie" : "");
  card.href = "./" + item.name + ".html";

  let imageHtml = "";
  if (item.image) {
    imageHtml =
      '<div class="plant-image-container">' +
      '<img src="./' +
      item.image +
      '" alt="' +
      item.name +
      '" class="plant-icon">' +
      "</div>";
  } else {
    const icon = isZombie ? "🧟" : "🌱";
    imageHtml =
      '<div class="plant-image-container">' +
      '<div class="plant-placeholder">' +
      icon +
      "</div>" +
      "</div>";
  }

  card.innerHTML =
    imageHtml +
    '<div class="plant-info">' +
    '<div class="plant-name">' +
    item.name +
    "</div>" +
    '<div class="plant-description">点击查看详细资料</div>' +
    "</div>";

  return card;
}

function renderGroupedContent() {
  // Separate plants and zombies using content_type field
  const plants = [];
  const zombies = [];

  contentList.forEach((item) => {
    if (item.content_type === "zombies") {
      zombies.push(item);
    } else {
      plants.push(item);
    }
  });

  // Render plants
  const plantsGrid = document.getElementById("plantsGrid");
  const plantsCount = document.getElementById("plantsCount");
  plantsGrid.innerHTML = "";
  plants.forEach((plant) => {
    plantsGrid.appendChild(createContentCard(plant, false));
  });
  plantsCount.textContent = plants.length + " 种植物";

  // Render zombies
  const zombiesGrid = document.getElementById("zombiesGrid");
  const zombiesCount = document.getElementById("zombiesCount");
  zombiesGrid.innerHTML = "";
  zombies.forEach((zombie) => {
    zombiesGrid.appendChild(createContentCard(zombie, true));
  });
  zombiesCount.textContent = zombies.length + " 种僵尸";

  // Show/hide sections based on content
  document.getElementById("plantsSection").style.display =
    plants.length > 0 ? "block" : "none";
  document.getElementById("zombiesSection").style.display =
    zombies.length > 0 ? "block" : "none";
}

function renderSearchResults(filteredContent) {
  const searchGrid = document.getElementById("searchGrid");
  const noResults = document.getElementById("noResults");
  const contentSections = document.getElementById("contentSections");

  if (filteredContent.length === 0) {
    searchGrid.style.display = "none";
    contentSections.style.display = "none";
    noResults.style.display = "block";
    return;
  }

  // Hide grouped sections and show search grid
  contentSections.style.display = "none";
  searchGrid.style.display = "grid";
  noResults.style.display = "none";

  // Clear and populate search results
  searchGrid.innerHTML = "";
  filteredContent.forEach((item) => {
    // Use content_type to determine if item is zombie
    const isZombie = item.content_type === "zombies";
    searchGrid.appendChild(createContentCard(item, isZombie));
  });
}

function setupSearch() {
  const searchInput = document.getElementById("searchInput");
  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();

    if (query === "") {
      // Show grouped content when search is empty
      document.getElementById("contentSections").style.display = "block";
      document.getElementById("searchGrid").style.display = "none";
      document.getElementById("noResults").style.display = "none";
    } else {
      // Filter and show search results
      const filtered = contentList.filter((item) =>
        item.name.toLowerCase().includes(query)
      );
      renderSearchResults(filtered);
    }
  });
}

// Initialize the page when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  renderGroupedContent();
  setupSearch();
});

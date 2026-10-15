const state = {
  selectedRestaurant: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof body === "object" && body !== null
      ? body.detail || JSON.stringify(body)
      : body;
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return body;
}

function restaurantCard(restaurant) {
  const card = document.createElement("article");
  card.className = "restaurant-card";
  card.innerHTML = `
    <h3>${escapeHtml(restaurant.name)}</h3>
    <p>${escapeHtml(restaurant.cuisine)} · ${restaurant.rating.toFixed(1)}/5</p>
    <p>${restaurant.delivery_time_minutes} min · $${restaurant.delivery_fee.toFixed(2)} delivery</p>
    <p>${restaurant.is_open ? "Open" : "Closed"}</p>
    <p>${escapeHtml(restaurant.address)}</p>
  `;

  const viewButton = document.createElement("button");
  viewButton.textContent = "View details";
  viewButton.addEventListener("click", () => loadRestaurant(restaurant.id));

  const editButton = document.createElement("button");
  editButton.textContent = "Edit";
  editButton.className = "secondary";
  editButton.style.marginLeft = "8px";
  editButton.addEventListener("click", () => fillForm(restaurant));

  card.append(viewButton, editButton);
  return card;
}

async function loadRestaurants() {
  const params = new URLSearchParams();
  const search = $("search").value.trim();
  const cuisine = $("cuisine").value.trim();
  const isOpen = $("open-status").value;

  if (search) params.set("search", search);
  if (cuisine) params.set("cuisine", cuisine);
  if (isOpen) params.set("is_open", isOpen);

  $("list-status").textContent = "Loading restaurants...";
  $("restaurant-list").replaceChildren();

  try {
    const restaurants = await api(`/restaurants?${params.toString()}`);
    $("list-status").textContent = `${restaurants.length} restaurant(s) found.`;

    if (!restaurants.length) {
      $("list-status").textContent = "No restaurants matched your filters.";
      return;
    }

    const fragment = document.createDocumentFragment();
    restaurants.forEach((restaurant) => fragment.appendChild(restaurantCard(restaurant)));
    $("restaurant-list").appendChild(fragment);
  } catch (error) {
    $("list-status").textContent = `Could not load restaurants: ${error.message}`;
    $("list-status").classList.add("error");
  }
}

async function loadRestaurant(id) {
  try {
    const [restaurant, menu] = await Promise.all([
      api(`/restaurants/${encodeURIComponent(id)}`),
      api(`/restaurants/${encodeURIComponent(id)}/menu`),
    ]);

    state.selectedRestaurant = restaurant;
    $("details-panel").classList.remove("hidden");
    $("restaurant-name").textContent = restaurant.name;
    $("restaurant-details").innerHTML = `
      <p><strong>Cuisine:</strong> ${escapeHtml(restaurant.cuisine)}</p>
      <p><strong>Rating:</strong> ${restaurant.rating.toFixed(1)}/5</p>
      <p><strong>Delivery:</strong> ${restaurant.delivery_time_minutes} minutes,
        $${restaurant.delivery_fee.toFixed(2)}</p>
      <p><strong>Status:</strong> ${restaurant.is_open ? "Open" : "Closed"}</p>
      <p><strong>Address:</strong> ${escapeHtml(restaurant.address)}</p>
    `;

    const menuList = $("menu-list");
    menuList.replaceChildren();

    if (!menu.items.length) {
      menuList.textContent = "No menu items found.";
      return;
    }

    menu.items.forEach((item) => {
      const element = document.createElement("article");
      element.className = "menu-item";
      element.innerHTML = `
        <h4>${escapeHtml(item.name)} — $${item.price.toFixed(2)}</h4>
        <p>${escapeHtml(item.description)}</p>
        <p>${escapeHtml(item.category)} · ${item.is_available ? "Available" : "Unavailable"}</p>
      `;
      menuList.appendChild(element);
    });

    $("details-panel").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    alert(`Could not load restaurant: ${error.message}`);
  }
}

function fillForm(restaurant) {
  $("restaurant-id").value = restaurant.id;
  $("restaurant-name-input").value = restaurant.name;
  $("restaurant-cuisine").value = restaurant.cuisine;
  $("restaurant-rating").value = restaurant.rating;
  $("restaurant-time").value = restaurant.delivery_time_minutes;
  $("restaurant-fee").value = restaurant.delivery_fee;
  $("restaurant-address").value = restaurant.address;
  $("restaurant-open").checked = restaurant.is_open;
  $("save-restaurant").textContent = "Update restaurant";
  $("restaurant-form").scrollIntoView({ behavior: "smooth" });
}

function resetForm() {
  $("restaurant-form").reset();
  $("restaurant-id").value = "";
  $("save-restaurant").textContent = "Create restaurant";
  $("form-status").textContent = "";
  $("form-status").classList.remove("error");
}

async function saveRestaurant(event) {
  event.preventDefault();

  const id = $("restaurant-id").value;
  const payload = {
    name: $("restaurant-name-input").value.trim(),
    cuisine: $("restaurant-cuisine").value.trim(),
    rating: Number($("restaurant-rating").value),
    delivery_time_minutes: Number($("restaurant-time").value),
    delivery_fee: Number($("restaurant-fee").value),
    is_open: $("restaurant-open").checked,
    address: $("restaurant-address").value.trim(),
  };

  $("form-status").textContent = "Saving...";
  $("form-status").classList.remove("error");

  try {
    const path = id ? `/restaurants/${encodeURIComponent(id)}` : "/restaurants";
    const method = id ? "PUT" : "POST";
    await api(path, {
      method,
      body: JSON.stringify(payload),
    });

    $("form-status").textContent = id
      ? "Restaurant updated successfully."
      : "Restaurant created successfully.";

    resetForm();
    await loadRestaurants();
  } catch (error) {
    $("form-status").textContent = `Could not save restaurant: ${error.message}`;
    $("form-status").classList.add("error");
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

$("filter-form").addEventListener("submit", (event) => {
  event.preventDefault();
  loadRestaurants();
});

$("clear-filters").addEventListener("click", () => {
  $("search").value = "";
  $("cuisine").value = "";
  $("open-status").value = "";
  loadRestaurants();
});

$("close-details").addEventListener("click", () => {
  $("details-panel").classList.add("hidden");
});

$("restaurant-form").addEventListener("submit", saveRestaurant);
$("reset-form").addEventListener("click", resetForm);

loadRestaurants();

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
    throw new Error(JSON.stringify(body, null, 2));
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

async function login() {
  try {
    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: $("login-email").value,
        password: $("login-password").value,
      }),
    });

    localStorage.setItem("token", result.access_token);

    $("login-status").textContent = "Login successful";
  } catch (error) {
    try {
      const parsed = JSON.parse(error.message);

      $("login-status").textContent = parsed.detail;
    } catch {
      $("login-status").textContent = error.message;
    }
  }
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
    restaurants.forEach((restaurant) =>
      fragment.appendChild(restaurantCard(restaurant)),
    );
    $("restaurant-list").appendChild(fragment);
  } catch (error) {
    $("list-status").textContent =
      `Could not load restaurants: ${error.message}`;
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

      const addButton = document.createElement("button");

      if (!item.is_available) {
        addButton.disabled = true;
        addButton.textContent = "Unavailable";
      } else {
        addButton.textContent = "Add To Cart";

        addButton.addEventListener("click", () => {
          addToCart(item.id);
        });
      }

      element.appendChild(addButton);

      menuList.appendChild(element);
    });

    $("details-panel").scrollIntoView({
      behavior: "smooth",
    });
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
    const method = id ? "PATCH" : "POST";
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
    $("form-status").textContent =
      `Could not save restaurant: ${error.message}`;
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

async function registerCustomer() {
  if (
    !$("register-name").value.trim() ||
    !$("register-email").value.trim() ||
    !$("register-password").value.trim() ||
    !$("register-phone").value.trim() ||
    !$("register-street").value.trim() ||
    !$("register-city").value.trim() ||
    !$("register-province").value.trim() ||
    !$("register-postal").value.trim()
  ) {
    $("register-status").textContent = "Please fill in all fields.";
    return;
  }

  try {
    await api("/customers/register", {
      method: "POST",
      body: JSON.stringify({
        name: $("register-name").value,
        email: $("register-email").value,
        password: $("register-password").value,
        phone: $("register-phone").value,

        addresses: [
          {
            label: "Home",
            street: $("register-street").value,
            city: $("register-city").value,
            province: $("register-province").value,
            postal_code: $("register-postal").value,
            is_default: true,
          },
        ],
      }),
    });

    $("register-status").textContent = "Registration successful";
  } catch (error) {
    try {
      const parsed = JSON.parse(error.message);

      $("register-status").textContent = parsed.detail;
    } catch {
      $("register-status").textContent = error.message;
    }
  }
}

async function addToCart(menuItemId) {
  const token = localStorage.getItem("token");

  try {
    const response = await fetch("/carts/items", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        menu_item_id: menuItemId,
        quantity: 1,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      alert(data.detail || "Could not add item to cart");
      return;
    }

    await loadCart();
  } catch (error) {
    console.error(error);
  }
}

async function loadCart() {
  const token = localStorage.getItem("token");

  try {
    const result = await api("/carts", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!result) {
      $("cart-items").textContent = "Your cart is empty.";

      $("cart-total").textContent = "";

      return;
    }

    $("cart-items").innerHTML = result.items
      .map(
        (item) => `
          <div class="menu-item">
            <strong>${escapeHtml(item.menu_item_id)}</strong><br>

            <button
              onclick="updateQuantity(
                '${escapeHtml(item.menu_item_id)}',
                ${item.quantity - 1}
              )"
            >
              -
            </button>

            ${item.quantity}

            <button
              onclick="updateQuantity(
                '${escapeHtml(item.menu_item_id)}',
                ${item.quantity + 1}
              )"
            >
              +
            </button>

            <br>

            <button
              onclick="removeFromCart(
                '${escapeHtml(item.menu_item_id)}'
              )"
            >
              Remove
            </button>
          </div>
        `,
      )
      .join("");

    $("cart-total").innerHTML = `
      <strong>Subtotal:</strong> $${result.subtotal.toFixed(2)}<br>
      <strong>Delivery Fee:</strong> $${result.delivery_fee.toFixed(2)}<br>
      <strong>Total:</strong> $${result.total.toFixed(2)}
    `;
  } catch (error) {
    $("cart-total").textContent = error.message;
  }
}

async function removeFromCart(menuItemId) {
  const token = localStorage.getItem("token");

  await api(`/carts/items/${encodeURIComponent(menuItemId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  await loadCart();
}

async function updateQuantity(menuItemId, quantity) {
  if (quantity <= 0) {
    await removeFromCart(menuItemId);
    return;
  }

  const token = localStorage.getItem("token");

  await api(`/carts/items/${encodeURIComponent(menuItemId)}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      quantity,
    }),
  });

  await loadCart();
}

async function clearCart() {
  const token = localStorage.getItem("token");

  await api("/carts/items", {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  await loadCart();
}

async function checkout() {
  const token = localStorage.getItem("token");

  try {
    const result = await api("/checkout", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    $("checkout-status").innerHTML = `
      Checkout successful<br>
      Order ID: ${escapeHtml(result.id)}<br>
      Status: ${escapeHtml(result.status)}
    `;

    await loadCart();
    await loadOrders();
  } catch (error) {
    $("checkout-status").textContent = error.message;
  }
}

async function loadOrders() {
  const token = localStorage.getItem("token");

  try {
    const result = await api("/orders", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    $("orders-list").innerHTML = result
      .map(
        (order) => `
    <div class="panel">
      <h3>${escapeHtml(order.restaurant_name)}</h3>

      <p>
        <strong>Order ID:</strong> ${escapeHtml(order.id)}
      </p>

      <p>
        <strong>Status:</strong> ${escapeHtml(order.status)}
      </p>

      <p>
        <strong>Total:</strong> $${order.total}
      </p>

      <p>
        <strong>Created:</strong>
        ${new Date(order.created_at).toLocaleString()}
      </p>

      <h4>Items</h4>

      <ul>
        ${order.items
          .map(
            (item) => `
              <li>
                ${escapeHtml(item.name)}
                × ${item.quantity}
                ($${item.line_total})
              </li>
            `,
          )
          .join("")}
      </ul>
    </div>
  `,
      )
      .join("");
  } catch (error) {
    $("orders-list").textContent = error.message;
  }
}

$("restaurant-form").addEventListener("submit", saveRestaurant);
$("reset-form").addEventListener("click", resetForm);
$("login-btn").addEventListener("click", login);
$("register-btn").addEventListener("click", registerCustomer);
$("load-cart-btn").addEventListener("click", loadCart);
$("checkout-btn").addEventListener("click", checkout);
$("orders-btn").addEventListener("click", loadOrders);
$("clear-cart-btn").addEventListener("click", clearCart);
loadRestaurants();

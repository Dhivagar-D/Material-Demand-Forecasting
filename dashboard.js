const API = "http://127.0.0.1:10000";

// ======================
// LOAD DROPDOWN OPTIONS
// ======================
async function loadOptions() {
    try {
        const res = await fetch(`${API}/api/options`);
        const data = await res.json();

        fillSelect("category", data.categories);
        fillSelect("region", data.regions);
        fillSelect("weather", data.weather);
        fillSelect("seasonality", data.seasonality);

    } catch (err) {
        console.error("Option Load Error:", err);
    }
}

function fillSelect(id, items) {
    const select = document.getElementById(id);

    if (!select) return;

    select.innerHTML = "<option value=''>Select</option>";

    items.forEach(item => {
        const option = document.createElement("option");
        option.value = item;
        option.textContent = item;
        select.appendChild(option);
    });
}

// ======================
// PREDICT DEMAND
// ======================
async function predictDemand() {

    const payload = {
        "Category": document.getElementById("category").value,
        "Region": document.getElementById("region").value,
        "Inventory Level": parseFloat(document.getElementById("inventory").value) || 0,
        "Price": parseFloat(document.getElementById("price").value) || 0,
        "Discount": parseFloat(document.getElementById("discount").value) || 0,
        "Weather Condition": document.getElementById("weather").value,
        "Holiday/Promotion": parseInt(document.getElementById("holiday").value) || 0,
        "Competitor Pricing": parseFloat(document.getElementById("competitor").value) || 0,
        "Seasonality": document.getElementById("seasonality").value
    };

    try {

        const res = await fetch(`${API}/api/predict`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.error || "Prediction Failed");
            return;
        }

        document.getElementById("predictedDemand").innerHTML =
            data.predicted_demand.toFixed(2);

        document.getElementById("recommendedStock").innerHTML =
            data.recommended_stock.toFixed(2);

        document.getElementById("inventoryAlert").innerHTML =
            data.inventory_alert;

        loadHistory();

    } catch (err) {
        console.error(err);
        alert("Prediction Error");
    }
}

// ======================
// LOAD ANALYTICS
// ======================
async function loadAnalytics() {

    try {

        const res = await fetch(`${API}/api/analytics`);

        const data = await res.json();

        document.getElementById("totalRecords").innerHTML =
            data.records;

        document.getElementById("totalCategories").innerHTML =
            data.categories;

        document.getElementById("totalRegions").innerHTML =
            data.regions;

        document.getElementById("avgForecast").innerHTML =
            data.average_forecast.toFixed(2);

        createAnalyticsChart(data);

    } catch (err) {

        console.error(err);

    }
}

// ======================
// ANALYTICS CHART
// ======================
let analyticsChart = null;

function createAnalyticsChart(data) {

    const ctx = document.getElementById("analyticsChart");

    if (!ctx) return;

    if (analyticsChart) {
        analyticsChart.destroy();
    }

    analyticsChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: [
                "Records",
                "Categories",
                "Regions"
            ],
            datasets: [{
                label: "Dataset Statistics",
                data: [
                    data.records,
                    data.categories,
                    data.regions
                ]
            }]
        }
    });
}

// ======================
// LOAD HISTORY
// ======================
async function loadHistory() {

    try {

        const res = await fetch(`${API}/api/history`);

        const data = await res.json();

        const table =
            document.getElementById("historyBody");

        if (!table) return;

        table.innerHTML = "";

        data.forEach(item => {

            table.innerHTML += `
            <tr>
                <td>${item.id}</td>
                <td>${item.category}</td>
                <td>${item.region}</td>
                <td>${item.predicted_demand}</td>
                <td>${item.alert}</td>
                <td>${item.created_at}</td>
            </tr>
            `;
        });

    } catch (err) {

        console.error(err);

    }
}

// ======================
// DATASET UPLOAD
// ======================
async function uploadDataset() {

    const file =
        document.getElementById("datasetFile").files[0];

    if (!file) {
        alert("Choose CSV file");
        return;
    }

    const token =
        localStorage.getItem("token");

    const formData = new FormData();

    formData.append("file", file);

    try {

        const res = await fetch(`${API}/api/upload`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            },
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            alert("Dataset Uploaded Successfully");
            loadOptions();
            loadAnalytics();
        } else {
            alert("Upload Failed");
        }

    } catch (err) {

        console.error(err);

    }
}

// ======================
// LOGOUT
// ======================
function logout() {

    localStorage.removeItem("token");

    window.location.href = "login.html";
}

// ======================
// INITIAL LOAD
// ======================
window.onload = () => {

    loadOptions();

    loadAnalytics();

    loadHistory();
};
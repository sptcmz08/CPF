// =====================================
// chart.js : Dashboard Charts
// ห้องพยาบาล CPF ขอนแก่น
// =====================================

// ---------- ข้อมูล Top 5 ยา ----------
const top5Labels = [
  "Paracetamol (500)",
  "ชุดตรวจสารเสพติด MET",
  "Air-x / CPM",
  "Plaster",
  "Zyetec"
];

const top5Values = [140, 127, 60, 30, 30];

// ---------- กราฟแท่ง (Bar Chart) ----------
function renderTop5BarChart(canvasId) {
  const ctx = document.getElementById(canvasId);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: top5Labels,
      datasets: [{
        label: "จำนวนที่ใช้",
        data: top5Values,
        backgroundColor: [
          "#4e79a7",
          "#f28e2b",
          "#e15759",
          "#76b7b2",
          "#59a14f"
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: "Top 5 ยาและเวชภัณฑ์ที่ใช้มากที่สุด"
        }
      }
    }
  });
}

// ---------- กราฟวงกลม (Pie Chart) ----------
function renderTop5PieChart(canvasId) {
  const ctx = document.getElementById(canvasId);

  new Chart(ctx, {
    type: "pie",
    data: {
      labels: top5Labels,
      datasets: [{
        data: top5Values,
        backgroundColor: [
          "#4e79a7",
          "#f28e2b",
          "#e15759",
          "#76b7b2",
          "#59a14f"
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "สัดส่วนการใช้ยา Top 5"
        }
      }
    }
  });
}

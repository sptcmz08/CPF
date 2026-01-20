/* ===============================
   CostLog.js
   แสดงกราฟค่าใช้จ่ายรายเดือน
================================ */

let costChart = null;

/* ===== โหลดกราฟครั้งแรก ===== */
document.addEventListener("DOMContentLoaded", () => {
    const year = new Date().getFullYear();
    loadCostChart(year);
});

/* ===== ดึงข้อมูลค่าใช้จ่าย ===== */
function loadCostChart(year){
    fetch(`/api/cost/monthly?year=${year}`)
        .then(res => res.json())
        .then(data => {
            renderCostChart(data, year);
        })
        .catch(err => {
            console.error("โหลดข้อมูลค่าใช้จ่ายไม่สำเร็จ", err);
        });
}

/* ===== สร้างกราฟ ===== */
function renderCostChart(costData, year){

    const ctx = document.getElementById("costChart");

    if(!ctx){
        console.warn("ไม่พบ canvas id=costChart");
        return;
    }

    const labels = [
        "ม.ค","ก.พ","มี.ค","เม.ย","พ.ค","มิ.ย",
        "ก.ค","ส.ค","ก.ย","ต.ค","พ.ย","ธ.ค"
    ];

    const data = labels.map((_,i)=> costData[i+1] || 0);

    if(costChart){
        costChart.destroy();
    }

    costChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: `ค่าใช้จ่าย (บาท) ปี ${year}`,
                data: data,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.y.toLocaleString()} บาท`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: val => val.toLocaleString()
                    }
                }
            }
        }
    });
}

/* ===== เปลี่ยนปี (เรียกจาก scroll ปี) ===== */
function changeCostYear(year){
    loadCostChart(year);
}

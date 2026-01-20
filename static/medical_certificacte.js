/* ===============================
   แสดง / ซ่อน ส่วนที่ 1 และ 2
================================ */
function showPart(n) {
  document.getElementById("s1").classList.add("hide");
  document.getElementById("s2").classList.add("hide");
  document.getElementById("s" + n).classList.remove("hide");
}

/* ===============================
   บันทึกข้อมูลส่วนที่ 1
   + ส่งข้อมูลไปส่วนที่ 2
================================ */
function savePart1() {

  const title1 = document.getElementById("p_title").value;
  const name1  = document.getElementById("p_name").value;
  const date1  = document.getElementById("p_date")?.value || "";

  if (title1 === "" || name1.trim() === "") {
    alert("กรุณาเลือกคำนำหน้า และกรอกชื่อ-นามสกุล");
    return;
  }

  // 🔁 ส่งค่าไปส่วนที่ 2
  document.getElementById("checked_title").value = title1;
  document.getElementById("checked_name").value  = name1;

  if (document.getElementById("checked_date")) {
    document.getElementById("checked_date").value = date1;
  }

  alert("บันทึกข้อมูลส่วนที่ 1 เรียบร้อยแล้ว");

  // เปิดไปส่วนที่ 2 อัตโนมัติ
  showPart(2);
}

/* ===============================
   บันทึกข้อมูลส่วนที่ 2
================================ */
function savePart2() {
  const doctor = document.querySelector("input[name='doctor_name']");
  if (!doctor || doctor.value.trim() === "") {
    alert("กรุณากรอกชื่อแพทย์");
    return;
  }

  alert("บันทึกข้อมูลส่วนที่ 2 เรียบร้อยแล้ว");
}

/* ===============================
   พิมพ์ PDF
================================ */
function preparePDF() {
  window.print();
}

function toggleDetail(id, show) {
    const el = document.getElementById(id);
    if (!el) return;

    if (show) {
        el.classList.remove('hide');
    } else {
        el.classList.add('hide');
        el.value = "";
    }
}

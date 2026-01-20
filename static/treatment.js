const medicineMap = {
  "ระบบย่อยอาหาร": [
    "Air-x","K milk120cc","Buscopan","Diasgest",
    "M.car ขับลม","ORS ผงเกลือแร่",
    "Paracetamol(500)","Motilium","K-milk",
    "ยาหอม","CA-R-Bon"
  ],
  "กล้ามเนื้อ": [
    "Balm นวด","Mydoclam","Norgesic"
  ],
  "ระบบสมอง": [
    "B1,6,12","Dimen","ORS ผงเกลือแร่","Paracetamol(500)"
  ],
  "ผิวหนัง": [
    "Acyclovir","CPM","Loratadine","Zyetec",
    "0.1% TA Cream","Mycozol",
    "Silver cream","Calamine lotion"
  ],
  "ระบบขับถ่าย": [
    "Paracetamol(500)","Norflox"
  ],
  "ระบบสืบพันธุ์": [
    "Ponstan(500)"
  ],
  "ตา หู ช่องปาก": [
    "Hista oph","Op Sar","Ointment",
    "Brufen(400)","Kenalog"
  ],
  "ทำแผล": [
    "Plaster","ไม้พันสำลี"
  ],
  "อื่นๆ": []
};

function updateMedicineList(){
  const group = document.getElementById("symptom_group").value;
  const select = document.getElementById("medicine_select");
  const otherInput = document.getElementById("other_medicine");

  select.innerHTML = '<option value="">-- เลือกยา --</option>';
  otherInput.style.display = "none";

  if(group === "อื่นๆ"){
    otherInput.style.display = "block";
    return;
  }

  if(medicineMap[group]){
    medicineMap[group].forEach(med => {
      const opt = document.createElement("option");
      opt.value = med;
      opt.textContent = med;
      select.appendChild(opt);
    });
  }
}

function checkOtherMedicine(){
  const select = document.getElementById("medicine_select");
  const otherInput = document.getElementById("other_medicine");
  otherInput.style.display = select.value === "" ? "none" : "none";
}

function toggleAllergy(show){
  document.getElementById("allergy_detail").style.display =
    show ? "block" : "none";
}


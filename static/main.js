async function saveMedicine() {
  const data = {
    group: document.getElementById("group").value,
    name: document.getElementById("name").value,
    qty: document.getElementById("qty").value,
    expire: document.getElementById("expire").value
  };

  const res = await fetch("/save_medicine", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });

  const result = await res.json();
  alert(result.synced ? "บันทึกและ Sync แล้ว" : "บันทึก Offline");
}

// ================================
// ฟังก์ชันกำหนดสีสถานะยา
// ================================
function getColor(expireDate, qty, minQty) {
  const today = new Date();
  const exp = new Date(expireDate);

  // หมดอายุ
  if (exp < today) return "red";

  // ใกล้หมดอายุ (น้อยกว่า 30 วัน)
  const daysLeft = (exp - today) / (1000 * 60 * 60 * 24);
  if (daysLeft < 30) return "orange";

  // ใกล้หมดสต๊อก
  if (qty < minQty) return "yellow";

  // ปกติ
  return "black";
}

function getColor(expireDate, qty, minQty) {
  const today = new Date();
  const exp = new Date(expireDate);

  if (exp < today) return "red";
  if ((exp - today) / (1000*60*60*24) < 30) return "orange";
  if (qty < minQty) return "yellow";
  return "black";
}

function getColor(expireDate, qty, minQty) {
  const today = new Date();
  const exp = new Date(expireDate);

  if (exp < today) return "red";
  if ((exp - today) / (1000*60*60*24) <= 30) return "orange";
  if (qty <= minQty) return "yellow";
  return "black";
}

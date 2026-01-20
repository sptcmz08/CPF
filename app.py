from flask import Flask, render_template, request, redirect, session, jsonify
import requests
import json
from datetime import datetime
from functools import wraps

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "cpf_nurse"

# ⭐ ใส่ URL ของ Google Apps Script ที่ Deploy แล้ว
GAS_URL = "https://script.google.com/macros/s/AKfycbyFLXNjy21R8gVHfWecWCwKKLAAnnfOsbi5ex4hJDaMR_kkoZKNIC53DVbBOUrszdUH/exec"

# ============================================
# GOOGLE SHEETS API HELPERS
# ============================================

def gas_list(table, limit=1000):
    """ดึงข้อมูลทั้งหมดจาก Sheet"""
    try:
        r = requests.get(GAS_URL, params={
            "action": "list",
            "table": table,
            "limit": limit
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_list error: {e}")
        return {"ok": False, "data": [], "message": str(e)}

def gas_get(table, row_id):
    """ดึงข้อมูลตาม ID"""
    try:
        r = requests.get(GAS_URL, params={
            "action": "get",
            "table": table,
            "id": str(row_id)
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_get error: {e}")
        return {"ok": False, "data": None, "message": str(e)}

def gas_search(table, field, value):
    """ค้นหาข้อมูลตามฟิลด์"""
    try:
        r = requests.get(GAS_URL, params={
            "action": "search",
            "table": table,
            "field": field,
            "value": value
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_search error: {e}")
        return {"ok": False, "data": [], "message": str(e)}

def gas_append(table, payload):
    """เพิ่มข้อมูลใหม่"""
    try:
        r = requests.post(GAS_URL, json={
            "action": "append",
            "table": table,
            "payload": payload
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_append error: {e}")
        return {"ok": False, "message": str(e)}

def gas_update(table, row_id, payload):
    """แก้ไขข้อมูลตาม ID"""
    try:
        r = requests.post(GAS_URL, json={
            "action": "update",
            "table": table,
            "id": str(row_id),
            "payload": payload
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_update error: {e}")
        return {"ok": False, "message": str(e)}

def gas_update_field(table, row_id, field, value):
    """อัปเดตฟิลด์เดียว"""
    try:
        r = requests.post(GAS_URL, json={
            "action": "update_field",
            "table": table,
            "id": str(row_id),
            "field": field,
            "value": value
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_update_field error: {e}")
        return {"ok": False, "message": str(e)}

def gas_delete(table, row_id):
    """ลบข้อมูลตาม ID"""
    try:
        r = requests.post(GAS_URL, json={
            "action": "delete",
            "table": table,
            "id": str(row_id)
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"gas_delete error: {e}")
        return {"ok": False, "message": str(e)}

# ============================================
# AUTH DECORATORS
# ============================================

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "username" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect("/menu")
        return f(*args, **kwargs)
    return wrap

# ============================================
# TEST ROUTES
# ============================================

@app.get("/test-gas")
def test_gas():
    """ทดสอบการเชื่อมต่อ GAS"""
    res = gas_list("users", 5)
    return jsonify(res)

@app.get("/fix-admin")
def fix_admin():
    """สร้าง Admin สำรองกรณีเข้าไม่ได้"""
    # 1. ลองค้นหาก่อน
    search = gas_search("users", "username", "admin")
    if search.get("ok") and search.get("data") and len(search["data"]) > 0:
        return "<h1>Admin user already exists!</h1> <p>User: admin / Pass: 111</p> <a href='/'>Go to Login</a>"
    
    # 2. ถ้าไม่มี ให้สร้างใหม่
    payload = {
        "username": "admin",
        "password": "111",
        "name": "Admin Recovery",
        "dept": "IT",
        "role": "admin"
    }
    res = gas_append("users", payload)
    return f"<h1>Created Admin!</h1> <pre>{res}</pre> <a href='/'>Go to Login</a>"

# ============================================
# LOGIN / LOGOUT
# ============================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # ค้นหา user จาก Google Sheets
        res = gas_search("users", "username", username)
        print(f"DEBUG LOGIN: username={username}, password={password}, res={res}") # DEBUG PRINT
        if res.get("ok") and res.get("data"):
            for user in res["data"]:
                if str(user.get("password", "")).strip() == password:
                    session["username"] = user["username"]
                    session["role"] = user.get("role", "user")
                    session["user_name"] = user.get("name", "")
                    return redirect("/menu")
        
        return render_template("login.html", error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    
    return render_template("login.html")

# ============================================
# MENU
# ============================================

@app.route("/menu")
@login_required
def menu():
    return render_template("menu.html", role=session.get("role"))

# ============================================
# USER MANAGEMENT (ADMIN)
# ============================================

@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        payload = {
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", "").strip(),
            "name": request.form.get("name", "").strip(),
            "dept": request.form.get("dept", "").strip(),
            "role": request.form.get("role", "user").strip()
        }
        gas_append("users", payload)

    res = gas_list("users", 1000)
    users_list = res.get("data", []) if res.get("ok") else []
    return render_template("users.html", users=users_list)

@app.route("/users/delete/<int:id>")
@admin_required
def delete_user(id):
    # ไม่ลบ admin
    res = gas_get("users", id)
    if res.get("ok") and res.get("data"):
        if res["data"].get("role") != "admin":
            gas_delete("users", id)
    return redirect("/users")

# ============================================
# MEDICINE TYPE / GROUP
# ============================================

SYMPTOM_GROUPS = [
    "ระบบทางเดินหายใจ","ระบบย่อยอาหาร","กล้ามเนื้อ","ระบบสมอง",
    "ผิวหนัง","อายุรกรรม","ระบบขับถ่าย","ระบบสืบพันธุ์",
    "ตา หู ช่องปาก","คอ","จมูก","ทำแผล",
    "อุบัติเหตุในงาน","อุบัติเหตุนอกงาน","อื่นๆ"
]

@app.route("/medicine_type")
def medicine_type():
    return render_template("medicine_type.html")

@app.route("/medicine/group")
def medicine_group():
    return render_template("medicine_group.html", groups=SYMPTOM_GROUPS)

# ============================================
# MEDICINE LIST
# ============================================

from urllib.parse import unquote

@app.route("/medicine/list/<group>")
def medicine_list(group):
    # ถอดรหัส URL (เช่น %E0%B8%... -> ภาษาไทย)
    group = unquote(group)
    # เปลี่ยนมาดึงทั้งหมดแล้ว Filter ใน Python แทน (แก้ปัญหา case sensitive / วรรค)
    res = gas_list("medicine", 5000)
    meds = []
    if res.get("ok"):
        for m in res.get("data", []):
            m_type = str(m.get("type", "")).strip().lower()
            m_group = str(m.get("group_name", "")).strip()
            
            # เช็คว่าเป็น medicine และกลุ่มตรงกัน
            if m_type == "medicine" and m_group == group.strip():
                meds.append(m)
                
    return render_template("medicine_list.html", medicines=meds, group=group)

# ============================================
# MEDICINE DETAIL & LOT
# ============================================

@app.route("/medicine/<int:med_id>")
def medicine_detail(med_id):
    # ดึงข้อมูลยา
    med_res = gas_get("medicine", med_id)
    if not med_res.get("ok") or not med_res.get("data"):
        return "ไม่พบข้อมูล", 404
    
    med = med_res["data"]
    
    # ดึง Lots ของยานี้
    # เปลี่ยนมาใช้ gas_list แล้ว filter เองเหมือนกัน เพื่อความชัวร์
    all_lots = gas_list("medicine_lot", 5000)
    lots = []
    if all_lots.get("ok"):
        for l in all_lots.get("data", []):
            if str(l.get("medicine_id", "")) == str(med_id):
                lots.append(l)
    
    # เรียงตาม expire_date
    lots.sort(key=lambda x: x.get("expire_date", ""))
    
    return render_template("medicine_lot.html", med=med, lots=lots)

@app.route("/medicine/<int:med_id>/add_lot", methods=["POST"])
def add_lot(med_id):
    expire_date = request.form.get("expire_date", "").strip()
    qty = int(request.form.get("qty", 0))
    price = float(request.form.get("price", 0))
    
    # หา Lot เดิมที่ expire_date เดียวกัน (ใช้ list + filter)
    all_lots = gas_list("medicine_lot", 5000)
    existing_lot = None
    if all_lots.get("ok"):
        for lot in all_lots.get("data", []):
            if str(lot.get("medicine_id", "")) == str(med_id) and str(lot.get("expire_date", "")).strip() == expire_date:
                existing_lot = lot
                break
    
    if existing_lot:
        # รวม Lot เดิม
        new_qty_total = int(existing_lot.get("qty_total", 0)) + qty
        new_qty_remain = int(existing_lot.get("qty_remain", 0)) + qty
        new_price_per_lot = float(existing_lot.get("price_per_lot", 0)) + price
        new_price_per_unit = new_price_per_lot / new_qty_total if new_qty_total > 0 else 0
        
        gas_update("medicine_lot", existing_lot["id"], {
            "qty_total": new_qty_total,
            "qty_remain": new_qty_remain,
            "price_per_lot": new_price_per_lot,
            "price_per_unit": new_price_per_unit
        })
    else:
        # สร้าง Lot ใหม่
        # นับจำนวน Lot เดิมของยานี้
        lot_count = 0
        if all_lots.get("ok"):
            for lot in all_lots.get("data", []):
                if str(lot.get("medicine_id", "")) == str(med_id):
                    lot_count += 1
        
        lot_name = f"LOT {lot_count + 1}"
        price_per_unit = price / qty if qty > 0 else 0
        
        gas_append("medicine_lot", {
            "medicine_id": med_id,
            "lot_name": lot_name,
            "expire_date": expire_date,
            "qty_total": qty,
            "qty_remain": qty,
            "price_per_lot": price,
            "price_per_unit": price_per_unit
        })
    
    return redirect(f"/medicine/{med_id}")

@app.route("/lot/<int:lot_id>/delete", methods=["POST"])
def delete_lot(lot_id):
    # หา lot ก่อน
    lot_res = gas_get("medicine_lot", lot_id)
    if not lot_res.get("ok") or not lot_res.get("data"):
        return "ไม่พบ Lot", 404
    
    med_id = lot_res["data"].get("medicine_id")
    gas_delete("medicine_lot", lot_id)
    
    return redirect(f"/medicine/{med_id}")

# ============================================
# SUPPLY LIST
# ============================================

@app.route("/supply")
def supply_list():
    # เปลี่ยนมาใช้ gas_list แล้ว filter ใน Python
    res = gas_list("medicine", 5000)
    supplies = []
    if res.get("ok"):
        for m in res.get("data", []):
            # เช็ค type เป็น supply (normalize case)
            m_type = str(m.get("type", "")).strip().lower()
            if m_type == "supply":
                supplies.append(m)
                
    return render_template("supply_list.html", supplies=supplies)

# ============================================
# RECORD (เพิ่มยา/เวชภัณฑ์)
# ============================================

@app.route("/record", methods=["GET", "POST"])
def record():
    if request.method == "POST":
        type_map = {"ยา": "medicine", "เวชภัณฑ์": "supply"}
        
        payload = {
            "type": type_map.get(request.form.get("type", ""), "medicine"),
            "group_name": request.form.get("group", "").strip(),
            "name": request.form.get("name", "").strip(),
            "benefit": request.form.get("benefit", "").strip(),
            "min_qty": int(request.form.get("min_qty", 0)),
            "qty": int(request.form.get("qty", 0)),
            "expire_date": request.form.get("expire_date", "").strip(),
            "used": int(request.form.get("used", 0))
        }
        
        res = gas_append("medicine", payload)
        if res.get("ok"):
            med_id = res.get("id")
            return redirect(f"/medicine/{med_id}")
        
        return "บันทึกไม่สำเร็จ", 500
    
    return render_template("record.html")

# ============================================
# TREATMENT
# ============================================

@app.route("/treatment_menu")
def treatment_menu():
    return render_template("treatment_menu.html")

@app.route("/treatment/register")
@login_required
def treatment_register():
    res = gas_list("treatment", 300)
    rows = res.get("data", []) if res.get("ok") else []
    return render_template("treatment_register.html", rows=rows)

@app.route("/treatment/form", methods=["GET", "POST"])
@login_required
def treatment_form():
    if request.method == "POST":
        try:
            medicine_json = request.form.get("medicine_json") or "[]"
            
            # parse รายการยา
            try:
                items = json.loads(medicine_json)
            except:
                items = []
            
            if not isinstance(items, list) or len(items) == 0:
                return "กรุณาเพิ่มยาอย่างน้อย 1 รายการ", 400
            
            # ตรวจ stock และตัด stock
            for it in items:
                lot_id = it.get("lot_id")
                qty = int(it.get("qty") or 0)
                
                if not lot_id or qty <= 0:
                    return "ข้อมูล Lot/จำนวนไม่ถูกต้อง", 400
                
                # ดึง lot ปัจจุบัน
                lot_res = gas_get("medicine_lot", lot_id)
                if not lot_res.get("ok") or not lot_res.get("data"):
                    return "ไม่พบ Lot", 404
                
                lot = lot_res["data"]
                current_remain = int(lot.get("qty_remain", 0))
                
                if current_remain < qty:
                    return f"จำนวนคงเหลือไม่พอ (Lot {lot_id})", 400
                
                # ตัด stock
                new_remain = current_remain - qty
                gas_update_field("medicine_lot", lot_id, "qty_remain", new_remain)
            
            # บันทึกการรักษา
            visit_date = (request.form.get("visit_date") or request.form.get("date") or "").strip()
            department = (request.form.get("department") or request.form.get("dept") or "").strip()
            symptom_group = (request.form.get("symptom_group") or request.form.get("group") or "").strip()
            symptom_detail = (request.form.get("symptom_detail") or request.form.get("detail") or "").strip()
            
            payload = {
                "visit_date": visit_date,
                "patient_name": request.form.get("patient_name", "").strip(),
                "department": department,
                "symptom_group": symptom_group,
                "symptom_detail": symptom_detail,
                "medicine": medicine_json,
                "allergy": request.form.get("allergy", "0"),
                "allergy_detail": request.form.get("allergy_detail", "").strip(),
                "occupational_disease": request.form.get("occupational_disease", "0"),
                "doctor_opinion": request.form.get("doctor_opinion", "").strip()
            }
            
            gas_append("treatment", payload)
            return redirect("/treatment/register")
            
        except Exception as e:
            return f"บันทึกไม่สำเร็จ: {e}", 500
    
    return render_template("treatment_form.html")

# ============================================
# TREATMENT API
# ============================================

@app.route("/api/treatment/<int:id>")
@login_required
def api_treatment_view(id):
    res = gas_get("treatment", id)
    if res.get("ok") and res.get("data"):
        return {"success": True, "data": res["data"]}
    return {"success": False}

@app.route("/api/treatment/edit/<int:id>", methods=["POST"])
@login_required
def api_treatment_edit(id):
    data = request.json
    
    # ดึงข้อมูลยาเดิม
    old_res = gas_get("treatment", id)
    old_meds = []
    if old_res.get("ok") and old_res.get("data"):
        try:
            old_meds = json.loads(old_res["data"].get("medicine", "[]"))
        except:
            old_meds = []
    
    # คืน stock Lot เดิม
    for m in old_meds:
        if m.get("lot_id"):
            lot_res = gas_get("medicine_lot", m["lot_id"])
            if lot_res.get("ok") and lot_res.get("data"):
                current = int(lot_res["data"].get("qty_remain", 0))
                new_remain = current + int(m.get("qty", 0))
                gas_update_field("medicine_lot", m["lot_id"], "qty_remain", new_remain)
    
    # ตัด stock ตามรายการใหม่
    try:
        new_meds = json.loads(data.get("medicine", "[]"))
    except:
        new_meds = []
    
    for m in new_meds:
        if m.get("lot_id"):
            lot_res = gas_get("medicine_lot", m["lot_id"])
            if lot_res.get("ok") and lot_res.get("data"):
                current = int(lot_res["data"].get("qty_remain", 0))
                new_remain = current - int(m.get("qty", 0))
                gas_update_field("medicine_lot", m["lot_id"], "qty_remain", new_remain)
    
    # update treatment
    gas_update("treatment", id, data)
    return {"success": True}

@app.route("/api/treatment/delete/<int:id>", methods=["DELETE"])
@login_required
def api_treatment_delete(id):
    # ดึงรายการยาที่เคยตัด stock
    old_res = gas_get("treatment", id)
    old_items = []
    if old_res.get("ok") and old_res.get("data"):
        try:
            old_items = json.loads(old_res["data"].get("medicine", "[]"))
        except:
            old_items = []
    
    # คืน stock
    for it in old_items:
        lot_id = it.get("lot_id")
        qty = int(it.get("qty") or 0)
        if lot_id and qty > 0:
            lot_res = gas_get("medicine_lot", lot_id)
            if lot_res.get("ok") and lot_res.get("data"):
                current = int(lot_res["data"].get("qty_remain", 0))
                new_remain = current + qty
                gas_update_field("medicine_lot", lot_id, "qty_remain", new_remain)
    
    # ลบ treatment
    gas_delete("treatment", id)
    return {"success": True}

@app.route("/api/treatment_list")
def treatment_list():
    res = gas_list("treatment", 1000)
    rows = res.get("data", []) if res.get("ok") else []
    
    data = []
    for r in rows:
        data.append({
            "id": r.get("id"),
            "visit_date": r.get("visit_date"),
            "patient_name": r.get("patient_name"),
            "medicine": r.get("medicine")
        })
    
    return jsonify(data)

# ============================================
# MEDICINE API
# ============================================

@app.route("/api/medicine_list")
def api_medicine_list():
    mtype = request.args.get("type", "")
    res = gas_search("medicine", "type", mtype)
    rows = res.get("data", []) if res.get("ok") else []
    return jsonify([{"id": r.get("id"), "name": r.get("name")} for r in rows])

@app.route("/api/medicine_id")
def api_medicine_id():
    name = (request.args.get("name") or "").strip()
    res = gas_list("medicine", 1000)
    
    if res.get("ok"):
        for m in res.get("data", []):
            if str(m.get("name", "")).strip() == name:
                return jsonify({"medicine_id": m.get("id")})
    
    return jsonify({"medicine_id": None})

@app.route("/api/medicine_lots")
def api_medicine_lots():
    medicine_id = request.args.get("medicine_id", "")
    res = gas_search("medicine_lot", "medicine_id", medicine_id)
    
    lots = []
    if res.get("ok"):
        for r in res.get("data", []):
            if int(r.get("qty_remain", 0)) > 0:
                lots.append({
                    "id": r.get("id"),
                    "name": r.get("lot_name"),
                    "remain": r.get("qty_remain"),
                    "price": r.get("price_per_unit")
                })
    
    return jsonify({"lots": lots})

@app.route("/api/cut_stock", methods=["POST"])
def api_cut_stock():
    data = request.json
    lot_id = data.get("lot_id")
    qty = int(data.get("qty", 0))
    
    lot_res = gas_get("medicine_lot", lot_id)
    if not lot_res.get("ok") or not lot_res.get("data"):
        return {"success": False, "message": "ไม่พบ Lot"}
    
    current = int(lot_res["data"].get("qty_remain", 0))
    if current < qty:
        return {"success": False, "message": "จำนวนคงเหลือไม่พอ"}
    
    new_remain = current - qty
    gas_update_field("medicine_lot", lot_id, "qty_remain", new_remain)
    return {"success": True}

# ============================================
# WASTE (ขยะติดเชื้อ)
# ============================================

@app.route("/waste")
@login_required
def waste_menu():
    return render_template("waste.html")

@app.route("/waste/add", methods=["GET", "POST"])
@login_required
def waste_add():
    if request.method == "POST":
        payload = {
            "company": request.form.get("company", "").strip(),
            "amount": request.form.get("amount", "").strip(),
            "date": request.form.get("date", "").strip(),
            "time": request.form.get("time", "").strip(),
            "place": request.form.get("place", "").strip(),
            "photo": request.form.get("photo", "")
        }
        
        gas_append("waste", payload)
        return redirect("/waste/register")
    
    return render_template("infectious_add.html")

@app.route("/waste/register")
@login_required
def waste_register():
    res = gas_list("waste", 1000)
    records = res.get("data", []) if res.get("ok") else []
    # เรียงใหม่สุดก่อน
    records.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return render_template("infectious_register.html", records=records)

@app.route("/waste/view/<int:id>")
@login_required
def waste_view(id):
    res = gas_get("waste", id)
    if not res.get("ok") or not res.get("data"):
        return "ไม่พบข้อมูล", 404
    return render_template("infectious_view.html", w=res["data"])

@app.route("/waste/edit/<int:id>", methods=["GET", "POST"])
@login_required
def waste_edit(id):
    if request.method == "POST":
        photo_new = request.form.get("photo", "").strip()
        
        # ถ้าไม่มีรูปใหม่ ใช้รูปเดิม
        old_res = gas_get("waste", id)
        old_photo = ""
        if old_res.get("ok") and old_res.get("data"):
            old_photo = old_res["data"].get("photo", "")
        
        payload = {
            "company": request.form.get("company", "").strip(),
            "amount": request.form.get("amount", "").strip(),
            "date": request.form.get("date", "").strip(),
            "time": request.form.get("time", "").strip(),
            "place": request.form.get("place", "").strip(),
            "photo": photo_new if photo_new else old_photo
        }
        
        gas_update("waste", id, payload)
        return redirect("/waste/register")
    
    # GET
    res = gas_get("waste", id)
    if not res.get("ok") or not res.get("data"):
        return "ไม่พบข้อมูล", 404
    return render_template("infectious_edit.html", w=res["data"])

@app.route("/waste/delete/<int:id>")
@login_required
def waste_delete(id):
    gas_delete("waste", id)
    return redirect("/waste/register")

# ============================================
# DASHBOARD
# ============================================

def has_supply(medicine_json_text):
    try:
        items = json.loads(medicine_json_text or "[]")
        for it in items:
            t = (it.get("type") or it.get("item_type") or "").strip().lower()
            if t in ("เวชภัณฑ์", "supply", "supplies"):
                return True
        return False
    except:
        return False

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/dashboard/drug_summary")
def dashboard_drug_summary():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    
    def norm(s):
        if s is None:
            return ""
        s = str(s).strip().lower()
        for ch in ["–", "—", "-", "−"]:
            s = s.replace(ch, "-")
        s = " ".join(s.split())
        return s
    
    # ดึง master ยา
    med_res = gas_list("medicine", 1000)
    meds = med_res.get("data", []) if med_res.get("ok") else []
    
    result = {}
    name_map = {}
    
    for m in meds:
        display = str(m.get("name", "")).strip()
        key = norm(display)
        if not key:
            continue
        if key not in name_map:
            name_map[key] = display
        disp = name_map[key]
        result[disp] = {"used": 0, "remain": 0, "has_used": False, "has_lot": False}
    
    def to_display(any_name):
        k = norm(any_name)
        return name_map.get(k)
    
    # ดึง lots
    lot_res = gas_list("medicine_lot", 10000)
    lots = lot_res.get("data", []) if lot_res.get("ok") else []
    
    # สร้าง map medicine_id -> name
    med_id_to_name = {str(m.get("id")): str(m.get("name", "")).strip() for m in meds}
    
    for lot in lots:
        med_id = str(lot.get("medicine_id", ""))
        med_name = med_id_to_name.get(med_id, "")
        disp = to_display(med_name)
        if disp and disp in result:
            result[disp]["remain"] += int(lot.get("qty_remain", 0))
            result[disp]["has_lot"] = True
    
    # ดึง treatments
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 7:
            try:
                v_year = int(visit_date[:4])
                v_month = int(visit_date[5:7])
            except:
                continue
            
            if v_year == year and v_month == month:
                try:
                    items = json.loads(t.get("medicine", "[]"))
                except:
                    continue
                
                if isinstance(items, list):
                    for item in items:
                        name = item.get("name", "")
                        qty = int(item.get("qty", 0) or 0)
                        disp = to_display(name)
                        if disp and disp in result:
                            result[disp]["used"] += qty
                            result[disp]["has_used"] = True
    
    return jsonify(result)

@app.route("/api/dashboard/monthly_cost")
@login_required
def api_dashboard_monthly_cost():
    year = request.args.get("year", type=int) or datetime.now().year
    
    months = [{"month": i, "drug": 0.0, "supply": 0.0, "total": 0.0} for i in range(1, 13)]
    
    # ดึง treatment
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    # ดึง lots
    lot_res = gas_list("medicine_lot", 10000)
    lots = lot_res.get("data", []) if lot_res.get("ok") else []
    lot_cache = {str(l.get("id")): l for l in lots}
    
    # ดึง medicines
    med_res = gas_list("medicine", 1000)
    meds = med_res.get("data", []) if med_res.get("ok") else []
    med_cache = {str(m.get("id")): m for m in meds}
    
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) < 7:
            continue
        
        try:
            v_year = int(visit_date[:4])
            v_month = int(visit_date[5:7])
        except:
            continue
        
        if v_year != year or v_month < 1 or v_month > 12:
            continue
        
        try:
            items = json.loads(t.get("medicine", "[]"))
        except:
            continue
        
        if not isinstance(items, list):
            continue
        
        for it in items:
            lot_id = str(it.get("lot_id", ""))
            qty = int(it.get("qty", 0) or 0)
            
            if not lot_id or qty <= 0:
                continue
            
            lot = lot_cache.get(lot_id)
            if not lot:
                continue
            
            price_per_unit = float(lot.get("price_per_unit", 0) or 0)
            med_id = str(lot.get("medicine_id", ""))
            med = med_cache.get(med_id)
            mtype = med.get("type") if med else None
            
            cost = price_per_unit * qty
            
            if mtype == "medicine":
                months[v_month - 1]["drug"] += cost
            elif mtype == "supply":
                months[v_month - 1]["supply"] += cost
    
    for obj in months:
        obj["total"] = obj["drug"] + obj["supply"]
        obj["drug"] = round(obj["drug"], 2)
        obj["supply"] = round(obj["supply"], 2)
        obj["total"] = round(obj["total"], 2)
    
    return jsonify({"year": year, "months": months})

@app.route("/api/dashboard/top5_month")
@login_required
def api_dashboard_top5_month():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    
    if not year or not month:
        return jsonify([])
    
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    counter = {}
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 7:
            try:
                v_year = int(visit_date[:4])
                v_month = int(visit_date[5:7])
            except:
                continue
            
            if v_year == year and v_month == month:
                try:
                    items = json.loads(t.get("medicine", "[]"))
                except:
                    continue
                
                if isinstance(items, list):
                    for item in items:
                        name = str(item.get("name", "")).strip()
                        qty = int(item.get("qty", 0) or 0)
                        if name and qty > 0:
                            counter[name] = counter.get(name, 0) + qty
    
    top5 = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify([{"name": k, "total": v} for k, v in top5])

@app.route("/api/dashboard/top5_year")
@login_required
def api_dashboard_top5_year():
    year = request.args.get("year", type=int)
    if not year:
        return jsonify([])
    
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    counter = {}
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 4:
            try:
                v_year = int(visit_date[:4])
            except:
                continue
            
            if v_year == year:
                try:
                    items = json.loads(t.get("medicine", "[]"))
                except:
                    continue
                
                if isinstance(items, list):
                    for item in items:
                        name = str(item.get("name", "")).strip()
                        qty = int(item.get("qty", 0) or 0)
                        if name and qty > 0:
                            counter[name] = counter.get(name, 0) + qty
    
    top5 = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify([{"name": k, "total": v} for k, v in top5])

@app.route("/api/dashboard/dept_year")
@login_required
def api_dashboard_dept_year():
    year = request.args.get("year", type=int)
    if not year:
        return jsonify([])
    
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    counter = {}
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 4:
            try:
                v_year = int(visit_date[:4])
            except:
                continue
            
            if v_year == year:
                dept = str(t.get("department", "")).strip()
                if dept:
                    counter[dept] = counter.get(dept, 0) + 1
    
    result = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return jsonify([{"name": k, "total": v} for k, v in result])

@app.route("/api/dashboard/dept_month")
@login_required
def api_dashboard_dept_month():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        return jsonify([])
    
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    counter = {}
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 7:
            try:
                v_year = int(visit_date[:4])
                v_month = int(visit_date[5:7])
            except:
                continue
            
            if v_year == year and v_month == month:
                dept = str(t.get("department", "")).strip()
                if dept:
                    counter[dept] = counter.get(dept, 0) + 1
    
    result = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return jsonify([{"name": k, "total": v} for k, v in result])

@app.route("/api/dashboard/symptom_year")
@login_required
def api_dashboard_symptom_year():
    year = request.args.get("year", type=int)
    if not year:
        return jsonify([])
    
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    counter = {}
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 4:
            try:
                v_year = int(visit_date[:4])
            except:
                continue
            
            if v_year == year:
                symptom = str(t.get("symptom_group", "")).strip()
                if symptom:
                    counter[symptom] = counter.get(symptom, 0) + 1
    
    result = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return jsonify([{"name": k, "total": v} for k, v in result])

@app.route("/api/dashboard/symptom_month")
@login_required
def api_dashboard_symptom_month():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        return jsonify([])
    
    treat_res = gas_list("treatment", 10000)
    treatments = treat_res.get("data", []) if treat_res.get("ok") else []
    
    counter = {}
    for t in treatments:
        visit_date = str(t.get("visit_date", ""))
        if len(visit_date) >= 7:
            try:
                v_year = int(visit_date[:4])
                v_month = int(visit_date[5:7])
            except:
                continue
            
            if v_year == year and v_month == month:
                if has_supply(t.get("medicine", "")):
                    name = "เวชภัณฑ์"
                else:
                    name = str(t.get("symptom_group", "")).strip() or "อื่นๆ"
                counter[name] = counter.get(name, 0) + 1
    
    result = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return jsonify([{"name": k, "total": v} for k, v in result])

# ============================================
# MEDICAL CERTIFICATE
# ============================================

@app.route("/medical_certificate")
@login_required
def medical_certificate_menu():
    return render_template("certificate_menu.html")

@app.route("/medical_certificate/form", methods=["GET", "POST"])
@login_required
def medical_certificate_form():
    if request.method == "POST":
        payload = {
            "title": request.form.get("title", "").strip(),
            "fullname": request.form.get("fullname", "").strip(),
            "address": request.form.get("address", "").strip(),
            "disease": request.form.get("disease", "").strip(),
            "disease_detail": request.form.get("disease_detail", "").strip(),
            "accident": request.form.get("accident", "").strip(),
            "accident_detail": request.form.get("accident_detail", "").strip(),
            "hospital": request.form.get("hospital", "").strip(),
            "hospital_detail": request.form.get("hospital_detail", "").strip(),
            "other_history": request.form.get("other_history", "").strip(),
            "requester_sign": request.form.get("requester_sign", "").strip(),
            "requester_date": request.form.get("requester_date", "").strip(),
            "hospital_name": request.form.get("hospital_name", "").strip(),
            "weight": request.form.get("weight", "").strip(),
            "height": request.form.get("height", "").strip(),
            "bp": request.form.get("bp", "").strip(),
            "pulse": request.form.get("pulse", "").strip(),
            "body_status": request.form.get("body_status", "").strip(),
            "body_detail": request.form.get("body_detail", "").strip(),
            "work_result": request.form.get("work_result", "").strip(),
            "doctor_name": request.form.get("doctor_name", "").strip()
        }
        
        gas_append("medical_certificate", payload)
        return redirect("/medical_certificate/register")
    
    return render_template("certificate_form.html")

@app.route("/medical_certificate/edit")
@login_required
def medical_certificate_edit():
    return render_template("certificate_edit.html")

@app.route("/medical_certificate/register")
@login_required
def medical_certificate_register():
    res = gas_list("medical_certificate", 1000)
    records = res.get("data", []) if res.get("ok") else []
    return render_template("certificate_register.html", records=records)

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    app.run(debug=True)

import sqlite3
import json
import time
import sys
import datetime

# การตั้งค่า (Configuration)
DB_PATH = 'offline.db'
GAS_URL = "https://script.google.com/macros/s/AKfycbyFLXNjy21R8gVHfWecWCwKKLAAnnfOsbi5ex4hJDaMR_kkoZKNIC53DVbBOUrszdUH/exec"
LOG_FILE = 'migration_log.txt'

# เราจะย้าย users และ medicine ก่อน เพื่อให้ได้ ID ใหม่มา map
TABLES_ORDER = [
    'users',
    'medicine',
    'medical_certificate', 
    'waste',
    'treatment',
    'medicine_lot'
]

# เก็บ ID เก่า -> ID ใหม่ สำหรับตาราง medicine
medicine_id_map = {}

def log(msg):
    """บันทึกข้อความลงไฟล์และแสดงผลหน้าจอ"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def gas_append(table, payload_data):
    """
    ส่งข้อมูลไปยัง Google Sheet ผ่าน GAS API
    แก้ไข: ส่งใน key 'payload' แทน 'data' ตามที่ GAS ต้องการ
    """
    import requests
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # แก้ไข: เปลี่ยน data -> payload
            body = {
                "action": "append",
                "table": table,
                "payload": payload_data 
            }
            
            response = requests.post(GAS_URL, json=body, timeout=60)
            response.raise_for_status()
            result = response.json()
            if result.get("ok"):
                return True, result
            else:
                return False, result.get("message", "Unknown error")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False, str(e)
    return False, "ครบจำนวนครั้งการลองใหม่แล้ว (Max retries reached)"

def migrate_table(conn, table_name):
    log(f"--- กำลังเริ่มย้ายข้อมูลตาราง: {table_name} ---")
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        log(f"ข้ามตาราง '{table_name}': {e}")
        return

    total = len(rows)
    log(f"พบข้อมูลจำนวน {total} รายการ")
    
    success_count = 0
    fail_count = 0

    for i, row in enumerate(rows):
        row_dict = dict(row)
        old_id = row_dict.get('id')
        
        # จัดการประเภทข้อมูลให้ถูกต้อง
        for key, value in row_dict.items():
            if value is None:
                row_dict[key] = ""
            elif isinstance(value, bytes):
                try:
                    row_dict[key] = value.decode('utf-8')
                except:
                    row_dict[key] = str(value)

        # ถ้าเป็นตาราง medicine_lot ต้องแก้ medicine_id ให้ตรงกับ ID ใหม่
        if table_name == 'medicine_lot':
            old_med_id = row_dict.get('medicine_id')
            if old_med_id in medicine_id_map:
                row_dict['medicine_id'] = medicine_id_map[old_med_id]
            else:
                # ถ้าหาไม่เจอ อาจจะเก็บ log ไว้ หรือปล่อยไป
                pass

        # ส่งข้อมูลไปยัง GAS
        success, res = gas_append(table_name, row_dict)
        
        if success:
            success_count += 1
            new_id = res.get('id')
            
            # ถ้าเป็นตาราง medicine ให้เก็บ ID ใหม่ไว้ใช้งาน
            if table_name == 'medicine' and old_id is not None:
                medicine_id_map[old_id] = new_id
                
            if (i + 1) % 5 == 0:
                log(f"ความคืบหน้า: {i+1}/{total} - สำเร็จ (OK)")
        else:
            fail_count += 1
            msg = res if isinstance(res, str) else res.get('message', str(res))
            log(f"รายการ ID {old_id} ล้มเหลว: {msg}")
            
        time.sleep(0.5)

    log(f"เสร็จสิ้นตาราง {table_name}. สำเร็จ: {success_count}, ล้มเหลว: {fail_count}")

def main():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"เริ่มการทำงานเมื่อ {datetime.datetime.now()}\n")
    except Exception as e:
        print(f"คำเตือน: ไม่สามารถสร้างไฟล์ log ได้: {e}")

    try:
        import requests
    except ImportError:
        log("ข้อผิดพลาด: ไม่พบโมดูล 'requests' กรุณาติดตั้งด้วยคำสั่ง: pip install requests")
        return

    log(f"กำลังเชื่อมต่อฐานข้อมูล: {DB_PATH}")
    try:
        conn = get_db_connection()
    except Exception as e:
        log(f"เกิดข้อผิดพลาดในการเปิดฐานข้อมูล: {e}")
        return

    for table in TABLES_ORDER:
        migrate_table(conn, table)

    conn.close()
    log("การย้ายข้อมูลเสร็จสมบูรณ์ (Migration complete).")

if __name__ == "__main__":
    main()

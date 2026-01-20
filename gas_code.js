/**
 * CPF Nurse - Google Apps Script Backend
 * ใช้ Google Sheets เป็น Database
 * 
 * สำหรับ Container-bound Script (สร้างจาก Extensions > Apps Script)
 */

// Headers สำหรับแต่ละ Sheet
const TABLE_HEADERS = {
  users: ['id', 'username', 'password', 'name', 'dept', 'role', 'created_at'],
  medicine: ['id', 'type', 'group_name', 'name', 'benefit', 'min_qty', 'qty', 'expire_date', 'used', 'created_at'],
  medicine_lot: ['id', 'medicine_id', 'lot_name', 'expire_date', 'qty_total', 'qty_remain', 'price_per_lot', 'price_per_unit', 'created_at'],
  treatment: ['id', 'visit_date', 'patient_name', 'department', 'symptom_group', 'symptom_detail', 'medicine', 'allergy', 'allergy_detail', 'occupational_disease', 'doctor_opinion', 'created_at'],
  waste: ['id', 'company', 'amount', 'date', 'time', 'place', 'photo', 'created_at'],
  medical_certificate: ['id', 'title', 'fullname', 'address', 'disease', 'disease_detail', 'accident', 'accident_detail', 'hospital', 'hospital_detail', 'other_history', 'requester_sign', 'requester_date', 'hospital_name', 'weight', 'height', 'bp', 'pulse', 'body_status', 'body_detail', 'work_result', 'doctor_name', 'created_at']
};

// ============================================
// HELPER FUNCTIONS
// ============================================
function getSpreadsheet_() {
  // ใช้ getActive() สำหรับ container-bound script
  return SpreadsheetApp.getActive();
}

function getSheet_(name) {
  return getSpreadsheet_().getSheetByName(name);
}

function jsonResponse_(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

// ============================================
// INIT - รันครั้งแรกเพื่อสร้าง Headers
// ============================================
function initSheets() {
  var ss = SpreadsheetApp.getActive();

  for (var table in TABLE_HEADERS) {
    var headers = TABLE_HEADERS[table];
    var sheet = ss.getSheetByName(table);

    if (!sheet) {
      sheet = ss.insertSheet(table);
    }

    var data = sheet.getDataRange().getValues();
    if (data.length === 0 || data[0].length === 0 || data[0][0] === '') {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    }
  }

  // ใส่ admin user
  var usersSheet = ss.getSheetByName('users');
  var userData = usersSheet.getDataRange().getValues();
  if (userData.length <= 1) {
    usersSheet.appendRow([1, 'admin', '111', 'ผู้ดูแลระบบ', 'Safety', 'admin', new Date().toISOString()]);
  }

  Logger.log('Sheets initialized successfully!');
  SpreadsheetApp.getUi().alert('สร้าง Headers และ Admin User เรียบร้อยแล้ว!');
}

// ============================================
// HTTP HANDLERS
// ============================================
function doGet(e) {
  try {
    var action = e.parameter.action;
    var table = e.parameter.table;

    if (!action || !table) {
      return jsonResponse_({ ok: false, message: 'Missing action or table' });
    }

    switch (action) {
      case 'list':
        return jsonResponse_(listRows_(table, parseInt(e.parameter.limit) || 1000));
      case 'get':
        return jsonResponse_(getRowById_(table, e.parameter.id));
      case 'search':
        return jsonResponse_(searchRows_(table, e.parameter.field, e.parameter.value));
      default:
        return jsonResponse_({ ok: false, message: 'Unknown action' });
    }
  } catch (err) {
    return jsonResponse_({ ok: false, message: err.toString() });
  }
}

function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    var action = body.action;
    var table = body.table;
    var payload = body.payload;
    var id = body.id;
    var field = body.field;
    var value = body.value;

    if (!action || !table) {
      return jsonResponse_({ ok: false, message: 'Missing action or table' });
    }

    switch (action) {
      case 'append':
        return jsonResponse_(appendRow_(table, payload));
      case 'update':
        return jsonResponse_(updateRow_(table, id, payload));
      case 'delete':
        return jsonResponse_(deleteRow_(table, id));
      case 'update_field':
        return jsonResponse_(updateField_(table, id, field, value));
      default:
        return jsonResponse_({ ok: false, message: 'Unknown action' });
    }
  } catch (err) {
    return jsonResponse_({ ok: false, message: err.toString() });
  }
}

// ============================================
// CRUD FUNCTIONS
// ============================================
function listRows_(table, limit) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found: ' + table };

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return { ok: true, data: [] };

  var headers = data[0];
  var rows = [];

  for (var i = 1; i < data.length && rows.length < limit; i++) {
    var row = {};
    for (var j = 0; j < headers.length; j++) {
      row[headers[j]] = data[i][j];
    }
    rows.push(row);
  }

  return { ok: true, data: rows };
}

function getRowById_(table, id) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found' };

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return { ok: false, message: 'Not found' };

  var headers = data[0];
  var idCol = headers.indexOf('id');

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idCol]) === String(id)) {
      var row = {};
      for (var j = 0; j < headers.length; j++) {
        row[headers[j]] = data[i][j];
      }
      return { ok: true, data: row };
    }
  }

  return { ok: false, message: 'Not found' };
}

function searchRows_(table, field, value) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found' };

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return { ok: true, data: [] };

  var headers = data[0];
  var fieldCol = headers.indexOf(field);
  if (fieldCol < 0) return { ok: false, message: 'Field not found' };

  var rows = [];
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][fieldCol]).trim() === String(value).trim()) {
      var row = {};
      for (var j = 0; j < headers.length; j++) {
        row[headers[j]] = data[i][j];
      }
      rows.push(row);
    }
  }

  return { ok: true, data: rows };
}

function appendRow_(table, payload) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found' };

  var data = sheet.getDataRange().getValues();
  var headers = data[0] || TABLE_HEADERS[table];

  // หา max ID
  var maxId = 0;
  var idCol = headers.indexOf('id');
  for (var i = 1; i < data.length; i++) {
    var id = parseInt(data[i][idCol]) || 0;
    if (id > maxId) maxId = id;
  }
  var newId = maxId + 1;

  // สร้างแถวใหม่
  var newRow = [];
  for (var j = 0; j < headers.length; j++) {
    var col = headers[j];
    if (col === 'id') {
      newRow.push(newId);
    } else if (col === 'created_at' && !payload[col]) {
      newRow.push(new Date().toISOString());
    } else {
      newRow.push(payload[col] !== undefined ? payload[col] : '');
    }
  }

  sheet.appendRow(newRow);
  return { ok: true, id: newId };
}

function updateRow_(table, id, payload) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found' };

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idCol = headers.indexOf('id');

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idCol]) === String(id)) {
      var range = sheet.getRange(i + 1, 1, 1, headers.length);
      var rowData = range.getValues()[0];

      for (var j = 0; j < headers.length; j++) {
        if (headers[j] !== 'id' && payload[headers[j]] !== undefined) {
          rowData[j] = payload[headers[j]];
        }
      }

      range.setValues([rowData]);
      return { ok: true };
    }
  }

  return { ok: false, message: 'Not found' };
}

function updateField_(table, id, field, value) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found' };

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idCol = headers.indexOf('id');
  var fieldCol = headers.indexOf(field);

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idCol]) === String(id)) {
      sheet.getRange(i + 1, fieldCol + 1).setValue(value);
      return { ok: true };
    }
  }

  return { ok: false, message: 'Not found' };
}

function deleteRow_(table, id) {
  var sheet = getSheet_(table);
  if (!sheet) return { ok: false, message: 'Sheet not found' };

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idCol = headers.indexOf('id');

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idCol]) === String(id)) {
      sheet.deleteRow(i + 1);
      return { ok: true };
    }
  }

  return { ok: false, message: 'Not found' };
}

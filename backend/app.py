from flask import Flask, jsonify, request, send_file
from flask_cors import CORS # 导入 CORS
import pandas as pd # 导入 pandas
import io # 导入 io 模块
import os

app = Flask(__name__)
CORS(app)  # 启用 CORS

contacts = [
    {"id": 1, "name": "张三", "contact_details": [
        {"type": "phone", "value": "13800138000"},
        {"type": "email", "value": "zhangsan@example.com"}
    ], "is_favorite": False},
    {"id": 2, "name": "李四", "contact_details": [
        {"type": "phone", "value": "13912345678"},
        {"type": "email", "value": "lisi@example.com"}
    ], "is_favorite": True},
]

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/contacts', methods=['GET'])
def get_contacts():
    return jsonify(contacts)

@app.route('/contacts', methods=['POST'])
def create_contact():
    data = request.get_json()
    new_id = max([c["id"] for c in contacts]) + 1 if contacts else 1
    new_contact = {
        "id": new_id,
        "name": data.get('name', ''),
        "contact_details": data.get('contact_details', []),
        "is_favorite": False # 新联系人默认不收藏
    }
    contacts.append(new_contact)
    return jsonify(new_contact), 201

@app.route('/import_contacts', methods=['POST'])
def import_contacts():
    if 'file' not in request.files:
        return jsonify({"error": "没有文件部分（字段名应为 file）"}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())

    # 同时支持 xlsx 和 xls
    if ext not in ('.xlsx', '.xls', '.xlsm'):
        return jsonify({"error": "不支持的文件类型，请上传 .xlsx 或 .xls"}), 400

    # 按扩展名显式选择 pandas 引擎
    engine = None
    if ext in ('.xlsx', '.xlsm'):
        engine = 'openpyxl'
    elif ext == '.xls':
        engine = 'xlrd'

    try:
        # 显式 engine，避免 pandas 在服务端环境里猜错/缺依赖
        df = pd.read_excel(file, engine=engine)

        # 基础校验：必须有 name 列（否则 name 取不到）
        if 'name' not in df.columns:
            return jsonify({"error": "Excel 缺少必需列：name（联系人姓名）"}), 400

        for _, row in df.iterrows():
            new_id = max([c["id"] for c in contacts]) + 1 if contacts else 1
            contact_details = []

            for col_name in df.columns:
                if col_name in ('id',):  # 可选：忽略 id 列（导入时重新生成）
                    continue
                if col_name == 'name':
                    continue
                if col_name == 'is_favorite':
                    continue

                if pd.notna(row.get(col_name)):
                    value = row[col_name]

                    # 数值去 .0
                    if isinstance(value, (int, float)):
                        if value == int(value):
                            value = str(int(value))
                        else:
                            value = str(value)
                    else:
                        value = str(value)

                    # phone_1 / email_2 等
                    if '_' in col_name:
                        parts = col_name.rsplit('_', 1)
                        detail_type = parts[0]
                        contact_details.append({"type": detail_type, "value": value})
                    elif col_name in ["phone", "email", "social_media", "address", "other"]:
                        contact_details.append({"type": col_name, "value": value})

            # is_favorite 兼容转换（可能是 0/1、TRUE/FALSE、空）
            fav = row.get('is_favorite', False)
            if isinstance(fav, str):
                fav = fav.strip().lower() in ('1', 'true', 'yes', 'y', '是')
            elif isinstance(fav, (int, float)):
                fav = bool(int(fav)) if pd.notna(fav) else False
            elif pd.isna(fav):
                fav = False

            new_contact = {
                "id": new_id,
                "name": str(row.get('name', '') if pd.notna(row.get('name')) else ''),
                "contact_details": contact_details,
                "is_favorite": fav
            }
            contacts.append(new_contact)

        return jsonify({"message": "联系人导入成功"}), 200

    except ImportError as e:
        # 缺引擎依赖时给明确提示
        if engine == 'xlrd':
            return jsonify({"error": "服务器未安装 xlrd，无法导入 .xls。请安装 xlrd 后重试。", "detail": str(e)}), 500
        if engine == 'openpyxl':
            return jsonify({"error": "服务器未安装 openpyxl，无法导入 .xlsx。请安装 openpyxl 后重试。", "detail": str(e)}), 500
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/export_contacts', methods=['GET'])
def export_contacts():
    try:
        # 将联系人数据转换为适合 Excel 的格式
        export_data = []
        for contact in contacts:
            row = {"id": contact["id"], "name": contact["name"], "is_favorite": contact["is_favorite"]}
            
            # 为每种联系方式类型收集值
            details_by_type = {}
            for detail in contact["contact_details"]:
                detail_type = detail["type"]
                detail_value = detail["value"]
                if detail_type not in details_by_type:
                    details_by_type[detail_type] = []
                details_by_type[detail_type].append(detail_value)

            # 将收集到的值添加到 row 中，并创建多列（如果需要）
            for detail_type, values in details_by_type.items():
                for i, value in enumerate(values):
                    row[f'{detail_type}_{i+1}'] = value
            export_data.append(row)

        df = pd.DataFrame(export_data)

        # 使用 io.BytesIO 捕获 Excel 输出
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='contacts.xlsx'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    data = request.get_json()
    contact = next((c for c in contacts if c["id"] == contact_id), None)
    if contact:
        contact["name"] = data.get('name', contact["name"])
        contact["contact_details"] = data.get('contact_details', contact["contact_details"])
        return jsonify(contact)
    return jsonify({"error": "联系人未找到"}), 404

@app.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    global contacts
    initial_len = len(contacts)
    contacts = [c for c in contacts if c["id"] != contact_id]
    if len(contacts) < initial_len:
        return jsonify({"message": "联系人删除成功"}), 200
    return jsonify({"error": "联系人未找到"}), 404

@app.route('/contacts/<int:contact_id>/favorite', methods=['PUT'])
def update_favorite_status(contact_id):
    data = request.get_json()
    is_favorite = data.get('is_favorite')

    if is_favorite is None:
        return jsonify({"error": "缺少 is_favorite 字段"}), 400

    contact = next((c for c in contacts if c["id"] == contact_id), None)
    if contact:
        contact["is_favorite"] = is_favorite
        return jsonify(contact)
    return jsonify({"error": "联系人未找到"}), 404

if __name__ == '__main__':
    app.run(debug=True)
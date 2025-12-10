from flask import Flask, jsonify, request, send_file
from flask_cors import CORS # 导入 CORS
import pandas as pd # 导入 pandas
import io # 导入 io 模块

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
        return jsonify({"error": "没有文件部分"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # 使用 pd.read_excel() 读取 Excel 文件
            df = pd.read_excel(file)
            for index, row in df.iterrows():
                new_id = max([c["id"] for c in contacts]) + 1 if contacts else 1
                contact_details = []
                if pd.notna(row.get('phone')):
                    contact_details.append({"type": "phone", "value": str(row['phone'])})
                if pd.notna(row.get('email')):
                    contact_details.append({"type": "email", "value": str(row['email'])})
                # 可以根据需要添加更多联系方式类型
                new_contact = {
                    "id": new_id,
                    "name": row.get('name', ''),
                    "contact_details": contact_details,
                    "is_favorite": False
                }
                contacts.append(new_contact)
            return jsonify({"message": "联系人导入成功"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "不支持的文件类型"}), 400

@app.route('/export_contacts', methods=['GET'])
def export_contacts():
    try:
        # 将联系人数据转换为适合 CSV 的格式
        export_data = []
        for contact in contacts:
            row = {"id": contact["id"], "name": contact["name"], "is_favorite": contact["is_favorite"]}
            for detail in contact["contact_details"]:
                row[detail["type"]] = detail["value"]
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

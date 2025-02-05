from flask import Flask, request, jsonify, render_template, redirect, url_for
from google.cloud import firestore
from datetime import datetime

app = Flask(__name__)
db = firestore.Client()

# 首頁
@app.route('/')
def index():
    return render_template('index.html')

# 新增任務
@app.route('/add_task', methods=['POST'])
def add_task():
    task = request.form['task']
    due_time = request.form['due_time']
    if task and due_time:
        db.collection('tasks').add({'task': task, 'due_time': due_time, 'completed': False})
    return redirect('/')

# 列出未完成任務
@app.route('/list')
def list_tasks():
    tasks = db.collection('tasks').where('completed', '==', False).stream()
    task_list = []
    for t in tasks:
        task_data = t.to_dict()
        task_data['id'] = t.id
        # 格式化日期
        if 'due_time' in task_data:
            try:
                dt = datetime.fromisoformat(task_data['due_time'])
                task_data['formatted_due_time'] = dt.strftime('%H:%M %d.%m.%Y')  # 格式：XX:XX XX.XX.XXXX
            except ValueError:
                task_data['formatted_due_time'] = task_data['due_time']
        task_list.append(task_data)
    return render_template('list.html', tasks=task_list)

# 標記任務為完成
@app.route('/complete_task/<task_id>', methods=['POST'])
def complete_task(task_id):
    task_ref = db.collection('tasks').document(task_id)
    task = task_ref.get().to_dict()
    if task:
        db.collection('completed_tasks').add(task)
        task_ref.delete()
    return redirect('/list')

@app.route('/history')
def history():
    try:
        completed_tasks = db.collection('completed_tasks').stream()
        task_list = []
        for t in completed_tasks:
            task_data = t.to_dict()
            task_data['id'] = t.id  # 添加文檔 ID
            # 處理日期格式化
            if 'due_time' in task_data:
                due_time = task_data['due_time']
                if isinstance(due_time, str):
                    # 假設 Firestore 中日期是字符串格式
                    try:
                        dt = datetime.fromisoformat(due_time)
                        task_data['formatted_due_time'] = dt.strftime('%H:%M %d.%m.%Y')
                    except ValueError:
                        task_data['formatted_due_time'] = due_time
                elif hasattr(due_time, 'to_datetime'):
                    # Firestore Timestamp 格式
                    dt = due_time.to_datetime()
                    task_data['formatted_due_time'] = dt.strftime('%H:%M %d.%m.%Y')
                else:
                    task_data['formatted_due_time'] = str(due_time)
            else:
                task_data['formatted_due_time'] = 'No due time'
            task_list.append(task_data)
        return render_template('history.html', tasks=task_list)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/test')
def test_firestore():
    try:
        tasks = db.collection('tasks').stream()
        task_list = [{'id': t.id, **t.to_dict()} for t in tasks]
        return f"Tasks: {task_list}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
    app.run(host='0.0.0.0', port=8080)

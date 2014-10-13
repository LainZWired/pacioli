from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from app import app, db
from werkzeug import secure_filename
from app.models import Memoranda
import io
import uuid
import os
import datetime

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST','GET'])
def upload():
    filenames = ''
    if request.method == 'POST':
        filenames = []
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                id = str(uuid.uuid4())
                uploadDate = datetime.datetime.now()
                fileName = secure_filename(file.filename)
                fileType = fileName.rsplit('.', 1)[1]
                file.seek(0, os.SEEK_END)
                fileSize = file.tell()
                fileText = file.stream.getvalue()
                memo = Memoranda(id=id, date=uploadDate, fileName=fileName, fileType=fileType, file=fileText, fileSize=fileSize, fileMap_id = "")
                db.session.add(memo)
                db.session.commit()
                filenames.append(fileName)
                file.close()    
    memos = Memoranda.query.order_by(Memoranda.date.desc()).all()
    
    return render_template('upload.html',
        title = 'Upload',
        filenames=filenames,
        memos=memos)
